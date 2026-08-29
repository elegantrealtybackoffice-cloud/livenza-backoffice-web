"""Versioned consumer API for Livenza.life V1.

This module deliberately avoids importing app.py or Flask at module-import time.
The back-office injects db/models/provider adapters through register_api_v1().
"""
import datetime
import json
import os
import secrets
import uuid

from livenza_customer_core import (
    hash_otp,
    hash_session_token,
    new_session_token,
    normalize_mobile,
    verify_otp,
)
from livenza_inventory_core import availability_state
from livenza_booking_core import validate_booking_dates, hold_expiry, amount_due_now, hash_share_token
from livenza_payment_core import verify_razorpay_webhook, payment_event_state, public_gateway_config
from livenza_integrations import RazorpayGateway
from livenza_receipts import build_receipt_view, render_receipt_html
from livenza_commerce_core import available_stock, validate_quantity, calculate_order_totals, transition_order
from livenza_loyalty_core import balance, points_for_paid_amount
from livenza_storage import storage_from_env

COOKIE_NAME = "livenza_customer_session"


def _int_env(name, default, minimum=1):
    try:
        return max(int(os.getenv(name, str(default))), minimum)
    except (TypeError, ValueError):
        return default


def _test_mode_enabled():
    if os.getenv("CUSTOMER_AUTH_TEST_MODE", "0") != "1":
        return False
    environment = (
        os.getenv("LIVENZA_ENV")
        or os.getenv("FLASK_ENV")
        or os.getenv("ENVIRONMENT")
        or ""
    ).strip().lower()
    return environment in {"test", "testing", "development", "dev", "local"}


def _serialize_customer(row):
    return {
        "id": row.public_id,
        "full_name": row.full_name or "",
        "primary_mobile": row.primary_mobile or "",
        "primary_email": row.primary_email or "",
        "status": row.status or "active",
    }


def serialize_property(row):
    return {
        "id": row.id,
        "slug": row.slug,
        "name": row.name,
        "city": row.city,
        "area": row.area or "",
        "summary": row.summary or "",
        "stay_types": row.stay_types,
    }


def register_api_v1(app, db, models, send_otp, notify=None):
    from flask import Blueprint, jsonify, make_response, request

    Customer = models["Customer"]
    CustomerIdentity = models["CustomerIdentity"]
    CustomerOtpChallenge = models["CustomerOtpChallenge"]
    CustomerSession = models["CustomerSession"]
    StayProperty = models["StayProperty"]
    StayRoomCategory = models["StayRoomCategory"]
    StayInventoryUnit = models["StayInventoryUnit"]
    StayRatePlan = models["StayRatePlan"]
    StayInventoryHold = models["StayInventoryHold"]
    StayBooking = models["StayBooking"]
    StayBookingItem = models["StayBookingItem"]
    BookingAddOn = models["BookingAddOn"]
    BookingShareToken = models["BookingShareToken"]
    PaymentRecord = models["PaymentRecord"]
    ProcessedWebhookEvent = models["ProcessedWebhookEvent"]
    CustomerDocument = models["CustomerDocument"]
    SupportTicket = models["SupportTicket"]
    Product = models["Product"]
    ProductVariant = models["ProductVariant"]
    StoreOrder = models["StoreOrder"]
    StoreOrderItem = models["StoreOrderItem"]
    LoyaltyAccount = models["LoyaltyAccount"]
    LoyaltyLedgerEntry = models["LoyaltyLedgerEntry"]
    ContentEntry = models["ContentEntry"]
    PropertyMedia = models["PropertyMedia"]
    storage = storage_from_env()

    notify = notify or (lambda *args, **kwargs: [])

    api = Blueprint("livenza_api_v1", __name__, url_prefix="/api/v1")

    def error(message, status=400, code="invalid_request"):
        return jsonify(ok=False, error=message, code=code), status

    def _booking_addon_catalog():
        raw = os.getenv("BOOKING_ADDONS_JSON", "[]")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = []
        if isinstance(parsed, dict):
            parsed = [dict(value, code=key) if isinstance(value, dict) else {"code": key, "label": str(value), "amount_minor": 0} for key, value in parsed.items()]
        catalog = {}
        if not isinstance(parsed, list):
            return catalog
        for item in parsed:
            if not isinstance(item, dict) or item.get("active") is False:
                continue
            code = str(item.get("code") or "").strip()[:80]
            if not code:
                continue
            catalog[code] = {
                "code": code,
                "label": str(item.get("label") or code.replace("_", " ").title())[:180],
                "amount_minor": max(int(item.get("amount_minor") or 0), 0),
            }
        # Store-backed booking add-ons (for example Move-In Kit) use the
        # published variant price as the server-authoritative booking snapshot.
        try:
            variants = ProductVariant.query.filter(ProductVariant.active.is_(True)).order_by(ProductVariant.id.asc()).all()
            products = Product.query.filter(Product.id.in_(sorted({v.product_id for v in variants}))).all() if variants else []
            products_by_id = {row.id: row for row in products if row.active and row.public}
            for variant in variants:
                product = products_by_id.get(variant.product_id)
                attrs = _variant_attributes(variant)
                code = str(attrs.get("booking_addon_code") or "").strip()[:80]
                if not product or not code:
                    continue
                catalog[code] = {
                    "code": code,
                    "label": str(attrs.get("booking_addon_label") or product.name)[:180],
                    "amount_minor": max(int(variant.price_minor or 0), 0),
                    "source_product_id": product.id,
                    "source_variant_id": variant.id,
                    "source_sku": variant.sku,
                }
        except Exception:
            # Store tables may not be migrated yet during a staged rollout.
            pass
        return catalog

    def session_for_request():
        token = (request.cookies.get(COOKIE_NAME) or "").strip()
        if not token:
            return None, None
        digest = hash_session_token(token)
        now = datetime.datetime.utcnow()
        row = CustomerSession.query.filter_by(token_hash=digest, revoked_at=None).filter(
            CustomerSession.expires_at > now
        ).first()
        if not row:
            return None, None
        return row, Customer.query.get(row.customer_id)

    @api.post("/auth/otp/request")
    def customer_otp_request():
        payload = request.get_json(silent=True) or {}
        try:
            identifier = normalize_mobile(payload.get("mobile", ""))
        except ValueError as exc:
            return error(str(exc), 400, "invalid_mobile")

        now = datetime.datetime.utcnow()
        window_start = now - datetime.timedelta(minutes=15)
        max_requests = _int_env("CUSTOMER_OTP_MAX_REQUESTS_15M", 5)
        recent = CustomerOtpChallenge.query.filter(
            CustomerOtpChallenge.identifier == identifier,
            CustomerOtpChallenge.requested_at >= window_start,
        ).count()
        if recent >= max_requests:
            return error("Too many OTP requests. Try again later.", 429, "otp_rate_limited")

        otp = f"{secrets.randbelow(1_000_000):06d}"
        salt = secrets.token_hex(16)
        expiry_minutes = _int_env("CUSTOMER_OTP_EXPIRY_MINUTES", 5)
        challenge = CustomerOtpChallenge(
            identifier=identifier,
            purpose="login",
            otp_hash=hash_otp(identifier, otp, salt),
            salt=salt,
            attempts=0,
            expires_at=now + datetime.timedelta(minutes=expiry_minutes),
            requested_at=now,
        )
        db.session.add(challenge)
        try:
            send_otp(identifier, otp)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return error(
                "Customer OTP delivery is not configured or temporarily unavailable.",
                503,
                "otp_delivery_unavailable",
            )

        body = {"ok": True, "expires_in_seconds": expiry_minutes * 60}
        if _test_mode_enabled():
            body["test_otp"] = otp
        return jsonify(body), 202

    @api.post("/auth/otp/verify")
    def customer_otp_verify():
        payload = request.get_json(silent=True) or {}
        try:
            identifier = normalize_mobile(payload.get("mobile", ""))
        except ValueError as exc:
            return error(str(exc), 400, "invalid_mobile")
        otp = str(payload.get("otp", "")).strip()
        if len(otp) != 6 or not otp.isdigit():
            return error("A valid 6-digit OTP is required.", 400, "invalid_otp")

        now = datetime.datetime.utcnow()
        challenge = CustomerOtpChallenge.query.filter(
            CustomerOtpChallenge.identifier == identifier,
            CustomerOtpChallenge.purpose == "login",
            CustomerOtpChallenge.consumed_at.is_(None),
            CustomerOtpChallenge.expires_at > now,
        ).order_by(CustomerOtpChallenge.requested_at.desc(), CustomerOtpChallenge.id.desc()).first()
        if not challenge:
            return error("OTP expired or not found.", 401, "otp_expired")
        if int(challenge.attempts or 0) >= 5:
            return error("OTP attempt limit reached.", 429, "otp_attempt_limit")
        if not verify_otp(identifier, otp, challenge.salt, challenge.otp_hash):
            challenge.attempts = int(challenge.attempts or 0) + 1
            db.session.commit()
            if challenge.attempts >= 5:
                return error("OTP attempt limit reached.", 429, "otp_attempt_limit")
            return error("Incorrect OTP.", 401, "otp_incorrect")

        identity = CustomerIdentity.query.filter_by(provider="mobile", identifier=identifier).first()
        if identity:
            customer = Customer.query.get(identity.customer_id)
        else:
            customer = Customer(
                public_id=str(uuid.uuid4()),
                primary_mobile=identifier,
                status="active",
            )
            db.session.add(customer)
            db.session.flush()
            identity = CustomerIdentity(
                customer_id=customer.id,
                provider="mobile",
                identifier=identifier,
                verified_at=now,
            )
            db.session.add(identity)
        if not customer:
            db.session.rollback()
            return error("Customer identity could not be resolved.", 500, "identity_error")
        if not identity.verified_at:
            identity.verified_at = now
        if not customer.primary_mobile:
            customer.primary_mobile = identifier

        challenge.consumed_at = now
        session_days = _int_env("CUSTOMER_SESSION_DAYS", 30)
        raw_token = new_session_token()
        session_row = CustomerSession(
            customer_id=customer.id,
            token_hash=hash_session_token(raw_token),
            expires_at=now + datetime.timedelta(days=session_days),
        )
        db.session.add(session_row)
        db.session.commit()

        response = make_response(jsonify(ok=True, customer=_serialize_customer(customer)))
        response.set_cookie(
            COOKIE_NAME,
            raw_token,
            max_age=session_days * 24 * 60 * 60,
            httponly=True,
            secure=bool(app.config.get("SESSION_COOKIE_SECURE", False)),
            samesite="Lax",
            path="/",
        )
        return response

    @api.post("/auth/logout")
    def customer_logout():
        session_row, _customer = session_for_request()
        if session_row:
            session_row.revoked_at = datetime.datetime.utcnow()
            db.session.commit()
        response = make_response(jsonify(ok=True))
        response.delete_cookie(COOKIE_NAME, path="/", samesite="Lax")
        return response

    @api.get("/me")
    def customer_me():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        return jsonify(ok=True, customer=_serialize_customer(customer))

    def _variant_attributes(row):
        try:
            value = json.loads(row.attributes_json or '{}')
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}

    def _serialize_variant(row):
        return {
            "id": row.id,
            "sku": row.sku,
            "title": row.title,
            "price_minor": int(row.price_minor or 0),
            "currency": row.currency or "INR",
            "available_stock": available_stock(row.stock_on_hand, row.stock_reserved),
            "attributes": _variant_attributes(row),
        }

    def _serialize_product(row, include_variants=True):
        data = {
            "id": row.id,
            "slug": row.slug,
            "name": row.name,
            "brand": row.brand or "store",
            "category": row.category,
            "collection": row.collection or "",
            "summary": row.summary or "",
            "description": row.description or "",
        }
        if include_variants:
            variants = ProductVariant.query.filter_by(product_id=row.id).filter(
                ProductVariant.active.is_(True)
            ).order_by(ProductVariant.id.asc()).all()
            data["variants"] = [_serialize_variant(item) for item in variants]
        return data

    @api.get("/products")
    def list_products():
        rows = Product.query.filter(
            Product.public.is_(True), Product.active.is_(True)
        ).order_by(Product.id.desc()).all()
        category = (request.args.get("category") or "").strip().lower()
        collection = (request.args.get("collection") or "").strip().lower()
        query = (request.args.get("q") or "").strip().lower()
        if category:
            rows = [row for row in rows if (row.category or "").lower() == category]
        if collection:
            rows = [row for row in rows if (row.collection or "").lower() == collection]
        if query:
            rows = [row for row in rows if query in " ".join([row.name or "", row.summary or "", row.category or "", row.collection or ""]).lower()]
        return jsonify(ok=True, products=[_serialize_product(row) for row in rows])

    @api.get("/products/<slug>")
    def product_detail(slug):
        row = Product.query.filter_by(slug=slug, public=True, active=True).first()
        if not row:
            return error("Product not found.", 404, "product_not_found")
        return jsonify(ok=True, product=_serialize_product(row))

    def _quote_items(payload_items):
        if not isinstance(payload_items, list) or not payload_items:
            raise ValueError("Your bag is empty.")
        normalized = []
        ids = []
        for item in payload_items:
            if not isinstance(item, dict):
                raise ValueError("Invalid cart item.")
            variant_id = int(item.get("variant_id") or 0)
            quantity = int(item.get("quantity") or 0)
            if variant_id <= 0:
                raise ValueError("Invalid product variant.")
            ids.append(variant_id)
            normalized.append((variant_id, quantity))
        variants = ProductVariant.query.filter(ProductVariant.id.in_(sorted(set(ids)))).all()
        by_id = {row.id: row for row in variants}
        product_ids = sorted({row.product_id for row in variants})
        products = Product.query.filter(Product.id.in_(product_ids)).all() if product_ids else []
        product_by_id = {row.id: row for row in products if row.public and row.active}
        lines = []
        totals_input = []
        for variant_id, quantity in normalized:
            row = by_id.get(variant_id)
            product = product_by_id.get(row.product_id) if row else None
            if not row or not row.active or not product:
                raise LookupError("PRODUCT_UNAVAILABLE")
            available = available_stock(row.stock_on_hand, row.stock_reserved)
            try:
                quantity = validate_quantity(quantity, available)
            except ValueError as exc:
                raise RuntimeError("OUT_OF_STOCK") from exc
            line_total = int(row.price_minor or 0) * quantity
            lines.append({
                "variant_id": row.id,
                "product_id": product.id,
                "product_slug": product.slug,
                "product_name": product.name,
                "variant_title": row.title,
                "sku": row.sku,
                "unit_price_minor": int(row.price_minor or 0),
                "quantity": quantity,
                "line_total_minor": line_total,
                "currency": row.currency or "INR",
            })
            totals_input.append((int(row.price_minor or 0), quantity))
        totals = calculate_order_totals(totals_input, discount_minor=0, delivery_minor=0)
        return lines, totals

    @api.post("/cart/quote")
    def cart_quote():
        payload = request.get_json(silent=True) or {}
        try:
            lines, totals = _quote_items(payload.get("items") or [])
        except RuntimeError as exc:
            if str(exc) == "OUT_OF_STOCK":
                return error("One or more items are out of stock.", 409, "OUT_OF_STOCK")
            raise
        except LookupError:
            return error("One or more products are unavailable.", 409, "PRODUCT_UNAVAILABLE")
        except (TypeError, ValueError) as exc:
            return error(str(exc), 400, "invalid_cart")
        return jsonify(ok=True, quote={"items": lines, **totals, "currency": "INR"})

    @api.get("/health")
    def api_health():
        try:
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
        except Exception:
            return jsonify(ok=False,status="degraded",service="livenza-api-v1"),503
        return jsonify(ok=True,status="ok",service="livenza-api-v1")

    @api.get("/content/<content_type>/<key>")
    def public_content(content_type, key):
        locale=(request.args.get("locale") or "en").strip()[:12]
        allowed={"homepage","city","property_editorial","journal","faq","offer","early_access"}
        if content_type not in allowed:
            return error("Content not found.",404,"not_found")
        row=ContentEntry.query.filter_by(content_type=content_type,key=key,locale=locale,status='published').first()
        if not row:
            return error("Content not found.",404,"not_found")
        try: body=json.loads(row.body_json or "{}")
        except Exception: body={}
        try: seo=json.loads(row.seo_json or "{}")
        except Exception: seo={}
        if not isinstance(body,dict): body={}
        if not isinstance(seo,dict): seo={}
        return jsonify(ok=True,content={
            "type":row.content_type,"key":row.key,"locale":row.locale,"title":row.title or "",
            "body":body,"seo":seo,"updated_at":row.updated_at.isoformat() if row.updated_at else None,
        })

    @api.get("/cities")
    def public_cities():
        rows = StayProperty.query.filter_by(active=True, public=True).with_entities(
            StayProperty.city
        ).distinct().order_by(StayProperty.city.asc()).all()
        return jsonify(items=[{"name": str(row[0])} for row in rows if row[0]])

    @api.get("/properties")
    def public_properties():
        query = StayProperty.query.filter_by(active=True, public=True)
        city = (request.args.get("city") or "").strip()
        q = (request.args.get("q") or "").strip()
        stay_type = (request.args.get("stay_type") or "").strip().lower()
        if city:
            query = query.filter(StayProperty.city.ilike(city))
        if q:
            term = f"%{q}%"
            query = query.filter(
                StayProperty.name.ilike(term)
                | StayProperty.city.ilike(term)
                | StayProperty.area.ilike(term)
                | StayProperty.summary.ilike(term)
            )
        rows = query.order_by(StayProperty.city.asc(), StayProperty.name.asc()).all()
        if stay_type:
            rows = [row for row in rows if stay_type in {item.lower() for item in row.stay_types}]
        return jsonify(items=[serialize_property(row) for row in rows])

    @api.get("/properties/<slug>")
    def public_property_detail(slug):
        row = StayProperty.query.filter_by(slug=slug, active=True, public=True).first()
        if not row:
            return error("Property not found.", 404, "property_not_found")
        body = serialize_property(row)
        categories = StayRoomCategory.query.filter_by(property_id=row.id, active=True).order_by(
            StayRoomCategory.name.asc()
        ).all()
        body["room_categories"] = []
        for item in categories:
            plans = StayRatePlan.query.filter_by(
                property_id=row.id, room_category_id=item.id, active=True
            ).order_by(StayRatePlan.amount_minor.asc()).all()
            body["room_categories"].append({
                "slug": item.slug,
                "name": item.name,
                "occupancy": item.occupancy,
                "summary": item.summary or "",
                "rate_plans": [
                    {
                        "code": plan.code,
                        "stay_type": plan.stay_type,
                        "billing_period": plan.billing_period,
                        "currency": plan.currency or "INR",
                        "amount_minor": int(plan.amount_minor or 0),
                        "security_deposit_minor": int(plan.security_deposit_minor or 0),
                        "reservation_amount_minor": int(plan.reservation_amount_minor or 0),
                    }
                    for plan in plans
                ],
            })
        media_rows=PropertyMedia.query.filter_by(property_id=row.id,public=True).order_by(PropertyMedia.sort_order.asc(),PropertyMedia.id.asc()).all()
        media=[]
        for item in media_rows:
            try: public_url=storage.public_url(item.storage_key)
            except Exception: public_url=''
            if public_url:
                media.append({"type":item.media_type,"alt_text":item.alt_text or "","url":public_url})
        body["media"]=media
        return jsonify(body)

    @api.get("/availability")
    def public_availability():
        property_slug = (request.args.get("property") or "").strip()
        category_slug = (request.args.get("room_category") or "").strip()
        start_raw = (request.args.get("start") or "").strip()
        end_raw = (request.args.get("end") or "").strip()
        try:
            start = datetime.date.fromisoformat(start_raw)
            end = datetime.date.fromisoformat(end_raw)
        except ValueError:
            return error("start and end must use YYYY-MM-DD.", 400, "invalid_dates")
        if end <= start:
            return error("end must be after start.", 400, "invalid_date_range")

        prop = StayProperty.query.filter_by(slug=property_slug, active=True, public=True).first()
        if not prop:
            return error("Property not found.", 404, "property_not_found")
        category = StayRoomCategory.query.filter_by(
            property_id=prop.id, slug=category_slug, active=True
        ).first()
        if not category:
            return error("Room category not found.", 404, "room_category_not_found")
        units = StayInventoryUnit.query.filter_by(
            property_id=prop.id,
            room_category_id=category.id,
            allocatable=True,
            active=True,
        ).all()
        unit_types = sorted({row.unit_type for row in units if row.unit_type})
        allocatable_unit_type = unit_types[0] if len(unit_types) == 1 else ("mixed" if unit_types else "")
        unit_ids = [row.id for row in units]
        now = datetime.datetime.utcnow()
        blocked_ids = set()
        if unit_ids:
            active_holds = StayInventoryHold.query.filter(
                StayInventoryHold.inventory_unit_id.in_(unit_ids),
                StayInventoryHold.status == "active",
                StayInventoryHold.expires_at > now,
                StayInventoryHold.start_date < end,
                StayInventoryHold.end_date > start,
            ).all()
            blocked_ids.update(row.inventory_unit_id for row in active_holds)
            confirmed_rows = db.session.query(StayBookingItem.inventory_unit_id).join(
                StayBooking, StayBooking.id == StayBookingItem.booking_id
            ).filter(
                StayBookingItem.inventory_unit_id.in_(unit_ids),
                StayBooking.status == "confirmed",
                StayBooking.start_date < end,
                StayBooking.end_date > start,
            ).all()
            blocked_ids.update(int(row[0]) for row in confirmed_rows)
        count = len(units)
        available = max(count - len(blocked_ids), 0)
        return jsonify(
            property=prop.slug,
            room_category=category.slug,
            start=start.isoformat(),
            end=end.isoformat(),
            available_count=available,
            availability_state=availability_state(count, len(blocked_ids)),
            allocatable_unit_type=allocatable_unit_type,
        )

    def _serialize_hold(row):
        return {
            "id": row.public_id,
            "status": row.status,
            "start": row.start_date.isoformat(),
            "end": row.end_date.isoformat(),
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
            "rate_plan_id": row.rate_plan_id,
        }

    def _serialize_booking(row):
        return {
            "id": row.public_id,
            "status": row.status,
            "booking_mode": row.booking_mode,
            "stay_type": row.stay_type,
            "start": row.start_date.isoformat(),
            "end": row.end_date.isoformat(),
            "currency": "INR",
            "subtotal_minor": int(row.subtotal_minor or 0),
            "security_deposit_minor": int(row.security_deposit_minor or 0),
            "addon_total_minor": int(row.addon_total_minor or 0),
            "total_minor": int(row.total_minor or 0),
            "amount_due_now_minor": int(row.amount_due_now_minor or 0),
        }

    def _blocked_inventory_ids(unit_ids, start, end, now):
        if not unit_ids:
            return set()
        blocked = set()
        active_holds = StayInventoryHold.query.filter(
            StayInventoryHold.inventory_unit_id.in_(unit_ids),
            StayInventoryHold.status == "active",
            StayInventoryHold.expires_at > now,
            StayInventoryHold.start_date < end,
            StayInventoryHold.end_date > start,
        ).all()
        blocked.update(row.inventory_unit_id for row in active_holds)
        confirmed_rows = db.session.query(StayBookingItem.inventory_unit_id).join(
            StayBooking, StayBooking.id == StayBookingItem.booking_id
        ).filter(
            StayBookingItem.inventory_unit_id.in_(unit_ids),
            StayBooking.status == "confirmed",
            StayBooking.start_date < end,
            StayBooking.end_date > start,
        ).all()
        blocked.update(int(row[0]) for row in confirmed_rows)
        return blocked

    @api.get("/booking-addons")
    def public_booking_addons():
        catalog = _booking_addon_catalog()
        return jsonify(items=list(catalog.values()))

    @api.post("/bookings/hold")
    def booking_hold():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        payload = request.get_json(silent=True) or {}
        try:
            start, end = validate_booking_dates(payload.get("start"), payload.get("end"))
        except ValueError as exc:
            return error(str(exc), 400, "invalid_dates")
        property_slug = str(payload.get("property_slug") or "").strip()
        category_slug = str(payload.get("room_category_slug") or "").strip()
        rate_plan_code = str(payload.get("rate_plan_code") or "").strip()
        prop = StayProperty.query.filter_by(slug=property_slug, active=True, public=True).first()
        if not prop:
            return error("Property not found.", 404, "property_not_found")
        category = StayRoomCategory.query.filter_by(property_id=prop.id, slug=category_slug, active=True).first()
        if not category:
            return error("Room category not found.", 404, "room_category_not_found")
        rate_plan = StayRatePlan.query.filter_by(
            property_id=prop.id, room_category_id=category.id, code=rate_plan_code, active=True
        ).first()
        if not rate_plan:
            return error("Rate plan not found.", 404, "rate_plan_not_found")
        now = datetime.datetime.utcnow()
        expired = StayInventoryHold.query.filter(
            StayInventoryHold.status == "active", StayInventoryHold.expires_at <= now
        ).all()
        for row in expired:
            row.status = "expired"
        query = StayInventoryUnit.query.filter_by(
            property_id=prop.id, room_category_id=category.id, allocatable=True, active=True
        ).order_by(StayInventoryUnit.id.asc())
        try:
            if db.engine.dialect.name == "postgresql":
                query = query.with_for_update(skip_locked=True)
        except Exception:
            pass
        units = query.all()
        blocked = _blocked_inventory_ids([row.id for row in units], start, end, now)
        candidate = next((row for row in units if row.id not in blocked), None)
        if not candidate:
            db.session.rollback()
            return error("No inventory is available for those dates.", 409, "NO_AVAILABILITY")
        hold = StayInventoryHold(
            public_id=str(uuid.uuid4()), customer_id=customer.id, inventory_unit_id=candidate.id,
            rate_plan_id=rate_plan.id, start_date=start, end_date=end, status="active",
            expires_at=hold_expiry(now, int(rate_plan.hold_minutes or 10)),
        )
        db.session.add(hold)
        db.session.commit()
        return jsonify(ok=True, hold=_serialize_hold(hold)), 201

    @api.post("/bookings")
    def create_booking():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        payload = request.get_json(silent=True) or {}
        hold_public_id = str(payload.get("hold_id") or payload.get("hold") or "").strip()
        hold = StayInventoryHold.query.filter_by(public_id=hold_public_id).first()
        if not hold:
            return error("Hold not found.", 404, "hold_not_found")
        now = datetime.datetime.utcnow()
        if hold.customer_id != customer.id:
            return error("This hold belongs to another customer.", 403, "hold_not_owned")
        if hold.status != 'active':
            return error("Hold is not active.", 409, "hold_not_active")
        if hold.expires_at <= now:
            hold.status = "expired"
            db.session.commit()
            return error("Hold has expired.", 409, "hold_expired")
        rate_plan = StayRatePlan.query.get(hold.rate_plan_id)
        unit = StayInventoryUnit.query.get(hold.inventory_unit_id)
        if not rate_plan or not unit:
            return error("Hold configuration is unavailable.", 409, "hold_invalid")
        prop = StayProperty.query.get(unit.property_id)
        mode = str(payload.get("booking_mode") or "book_now").strip().lower()
        addons = payload.get("addons") or []
        if not isinstance(addons, list):
            return error("addons must be a list.", 400, "invalid_addons")
        guardian = payload.get("guardian") or {}
        if rate_plan.stay_type == "student":
            if not isinstance(guardian, dict) or not str(guardian.get("name") or "").strip() or not str(guardian.get("mobile") or "").strip():
                return error("Guardian name and mobile are required for student bookings.", 400, "guardian_required")
        addon_rows = []
        addon_total = 0
        catalog = _booking_addon_catalog()
        for item in addons:
            code = str(item.get("code") if isinstance(item, dict) else item or "").strip()[:80]
            if not code:
                continue
            published = catalog.get(code)
            if not published:
                return error("One or more add-ons are unavailable.", 400, "invalid_addon")
            amount = int(published["amount_minor"])
            addon_total += amount
            metadata = {
                key: published[key]
                for key in ("source_product_id", "source_variant_id", "source_sku")
                if published.get(key) is not None
            }
            addon_rows.append((code, published["label"], amount, metadata))
        subtotal = max(int(rate_plan.amount_minor or 0), 0)
        security = max(int(rate_plan.security_deposit_minor or 0), 0)
        total = subtotal + security + addon_total
        try:
            due_now = amount_due_now(mode, total, int(rate_plan.reservation_amount_minor or 0))
        except ValueError as exc:
            return error(str(exc), 400, "invalid_booking_mode")
        booking = StayBooking(
            public_id=str(uuid.uuid4()), customer_id=customer.id, property_id=prop.id, rate_plan_id=rate_plan.id,
            booking_mode=mode, stay_type=rate_plan.stay_type, start_date=hold.start_date, end_date=hold.end_date,
            status="held", subtotal_minor=subtotal, security_deposit_minor=security, addon_total_minor=addon_total,
            total_minor=total, amount_due_now_minor=due_now, guardian_json=json.dumps(guardian, separators=(",", ":")),
            details_json=json.dumps(payload.get("details") or {}, separators=(",", ":")),
        )
        db.session.add(booking)
        db.session.flush()
        db.session.add(StayBookingItem(booking_id=booking.id, hold_id=hold.id, inventory_unit_id=unit.id))
        for code, label, amount, metadata in addon_rows:
            db.session.add(BookingAddOn(booking_id=booking.id, code=code, label=label, amount_minor=amount, metadata_json=json.dumps(metadata, separators=(",", ":"))))
        db.session.commit()
        return jsonify(ok=True, booking=_serialize_booking(booking)), 201

    @api.get("/bookings/<public_id>")
    def get_booking(public_id):
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        booking = StayBooking.query.filter_by(public_id=public_id, customer_id=customer.id).first()
        if not booking:
            return error("Booking not found.", 404, "booking_not_found")
        return jsonify(ok=True, booking=_serialize_booking(booking))

    @api.post("/bookings/<public_id>/parent-share")
    def create_parent_share(public_id):
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        booking = StayBooking.query.filter_by(public_id=public_id).first()
        if not booking:
            return error("Booking not found.", 404, "booking_not_found")
        if booking.customer_id != customer.id:
            return error("This booking belongs to another customer.", 403, "booking_not_owned")
        raw_token = secrets.token_urlsafe(32)
        hours = _int_env("PARENT_SHARE_EXPIRY_HOURS", 24)
        row = BookingShareToken(
            booking_id=booking.id,
            token_hash=hash_share_token(raw_token),
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=hours),
        )
        db.session.add(row)
        db.session.commit()
        return jsonify(ok=True, token=raw_token, expires_at=row.expires_at.isoformat()), 201

    @api.get("/booking-shares/<token>")
    def get_parent_share(token):
        digest = hash_share_token(token)
        row = BookingShareToken.query.filter_by(token_hash=digest, revoked_at=None).first()
        if not row:
            return error("Share link not found.", 404, "share_not_found")
        now = datetime.datetime.utcnow()
        if row.expires_at <= now:
            return error("Share link has expired.", 410, "share_expired")
        booking = StayBooking.query.get(row.booking_id)
        if not booking:
            return error("Booking not found.", 404, "booking_not_found")
        prop = StayProperty.query.get(booking.property_id)
        rate_plan = StayRatePlan.query.get(booking.rate_plan_id)
        return jsonify(
            ok=True,
            booking={
                "id": booking.public_id,
                "status": booking.status,
                "booking_mode": booking.booking_mode,
                "stay_type": booking.stay_type,
                "start": booking.start_date.isoformat(),
                "end": booking.end_date.isoformat(),
                "currency": (rate_plan.currency if rate_plan else "INR") or "INR",
                "total_minor": int(booking.total_minor or 0),
                "amount_due_now_minor": int(booking.amount_due_now_minor or 0),
            },
            property={
                "name": prop.name if prop else "Livenza stay",
                "city": prop.city if prop else "",
                "area": prop.area if prop else "",
                "summary": prop.summary if prop else "",
            },
            published={
                "safety": None,
                "meals": None,
                "transport": None,
                "policies": None,
            },
        )

    def _serialize_store_order(row):
        items = StoreOrderItem.query.filter_by(order_id=row.id).order_by(StoreOrderItem.id.asc()).all()
        return {
            "id": row.public_id,
            "status": row.status,
            "fulfilment_mode": row.fulfilment_mode,
            "subtotal_minor": int(row.subtotal_minor or 0),
            "discount_minor": int(row.discount_minor or 0),
            "delivery_minor": int(row.delivery_minor or 0),
            "total_minor": int(row.total_minor or 0),
            "currency": "INR",
            "items": [{
                "variant_id": item.variant_id,
                "sku": item.sku,
                "product_name": item.product_name,
                "variant_title": item.variant_title,
                "quantity": int(item.quantity or 0),
                "unit_price_minor": int(item.unit_price_minor or 0),
                "line_total_minor": int(item.line_total_minor or 0),
            } for item in items],
        }

    def _locked_variants(variant_ids):
        query = ProductVariant.query.filter(ProductVariant.id.in_(variant_ids)).order_by(ProductVariant.id.asc())
        dialect = getattr(getattr(db.session, "bind", None), "dialect", None)
        if getattr(dialect, "name", "") == "postgresql":
            return query.with_for_update().all()
        # Production uses PostgreSQL. SQLite/test environments cannot apply FOR UPDATE.
        return query.all()

    def _internal_delivery_property_slugs():
        return {item.strip().lower() for item in os.getenv("LIVENZA_INTERNAL_DELIVERY_PROPERTIES", "").split(",") if item.strip()}

    def _eligible_property_room_delivery(customer_id):
        configured = _internal_delivery_property_slugs()
        if not configured:
            return []
        today = datetime.date.today()
        bookings = StayBooking.query.filter(
            StayBooking.customer_id == customer_id,
            StayBooking.status == "confirmed",
            StayBooking.start_date <= today,
            StayBooking.end_date >= today,
        ).all()
        options = []
        for booking in bookings:
            prop = StayProperty.query.get(booking.property_id)
            if not prop or prop.slug.lower() not in configured:
                continue
            item = StayBookingItem.query.filter_by(booking_id=booking.id).first()
            unit = StayInventoryUnit.query.get(item.inventory_unit_id) if item else None
            if not unit:
                continue
            options.append({
                "id": f"booking:{booking.public_id}",
                "type": "property_room",
                "label": f"{prop.name} · {unit.display_name or unit.code}",
                "property": {"id": prop.id, "slug": prop.slug, "name": prop.name, "city": prop.city},
                "room": {"id": unit.id, "code": unit.code, "display_name": unit.display_name or unit.code},
                "booking_id": booking.public_id,
            })
        return options

    @api.post("/orders")
    def create_store_order():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        payload = request.get_json(silent=True) or {}
        raw_items = payload.get("items") or []
        if not isinstance(raw_items, list) or not raw_items:
            return error("Your bag is empty.", 400, "invalid_cart")
        quantities = {}
        try:
            for item in raw_items:
                variant_id = int((item or {}).get("variant_id") or 0)
                quantity = int((item or {}).get("quantity") or 0)
                if variant_id <= 0 or quantity <= 0:
                    raise ValueError
                quantities[variant_id] = quantities.get(variant_id, 0) + quantity
        except Exception:
            return error("Invalid cart item.", 400, "invalid_cart")
        variant_ids = sorted(quantities)
        variants = _locked_variants(variant_ids)
        if len(variants) != len(variant_ids):
            db.session.rollback()
            return error("One or more products are unavailable.", 409, "PRODUCT_UNAVAILABLE")
        products = Product.query.filter(Product.id.in_(sorted({v.product_id for v in variants}))).all()
        product_by_id = {row.id: row for row in products if row.public and row.active}
        totals_input = []
        prepared = []
        try:
            for variant in variants:
                product = product_by_id.get(variant.product_id)
                if not variant.active or not product:
                    raise LookupError("PRODUCT_UNAVAILABLE")
                quantity = validate_quantity(quantities[variant.id], available_stock(variant.stock_on_hand, variant.stock_reserved))
                unit_price_minor = int(variant.price_minor or 0)
                prepared.append((variant, product, quantity, unit_price_minor))
                totals_input.append((unit_price_minor, quantity))
        except ValueError:
            db.session.rollback()
            return error("One or more items are out of stock.", 409, "OUT_OF_STOCK")
        except LookupError:
            db.session.rollback()
            return error("One or more products are unavailable.", 409, "PRODUCT_UNAVAILABLE")
        totals = calculate_order_totals(totals_input, discount_minor=0, delivery_minor=0)
        fulfilment_mode = str(payload.get("delivery_mode") or "address").strip()[:32] or "address"
        delivery = payload.get("delivery") if isinstance(payload.get("delivery"), dict) else {}
        if fulfilment_mode == "property_room":
            requested_option = str(delivery.get("delivery_option_id") or "").strip()
            eligible = {item["id"]: item for item in _eligible_property_room_delivery(customer.id)}
            if not requested_option or requested_option not in eligible:
                db.session.rollback()
                return error("That Livenza property delivery option is not available for this account.", 403, "invalid_delivery_option")
            delivery = eligible[requested_option]
        elif fulfilment_mode != "address":
            db.session.rollback()
            return error("Unsupported delivery mode.", 400, "invalid_delivery_option")
        order = StoreOrder(
            public_id=str(uuid.uuid4()), customer_id=customer.id, status="placed",
            fulfilment_mode=fulfilment_mode, delivery_json=json.dumps(delivery, separators=(",", ":")),
            subtotal_minor=totals["subtotal_minor"], discount_minor=0, delivery_minor=0,
            total_minor=totals["total_minor"],
        )
        db.session.add(order)
        db.session.flush()
        for variant, product, quantity, unit_price_minor in prepared:
            variant.stock_reserved = int(variant.stock_reserved or 0) + quantity
            db.session.add(StoreOrderItem(
                order_id=order.id, variant_id=variant.id, sku=variant.sku,
                product_name=product.name, variant_title=variant.title, quantity=quantity,
                unit_price_minor=unit_price_minor, line_total_minor=unit_price_minor * quantity,
            ))
        gateway = RazorpayGateway.from_env()
        try:
            gateway_order = gateway.create_order(
                order.total_minor, "INR", f"LVZ-S-{order.public_id[:16]}",
                {"store_order_id": order.public_id, "customer_id": customer.public_id},
            )
        except Exception:
            db.session.rollback()
            return error("Payment provider is unavailable.", 503, "payment_provider_unavailable")
        payment = PaymentRecord(
            public_id=str(uuid.uuid4()), customer_id=customer.id, source_type="store_order", source_id=order.id,
            gateway="razorpay", gateway_order_id=str(gateway_order.get("id") or ""), amount_minor=order.total_minor,
            currency=str(gateway_order.get("currency") or "INR"), status="created", metadata_json="{}",
        )
        db.session.add(payment)
        db.session.commit()
        public_cfg = public_gateway_config({"key_id": gateway.key_id})
        return jsonify(ok=True, order=_serialize_store_order(order), payment=_serialize_payment(payment), checkout={
            "key_id": public_cfg["key_id"], "order_id": payment.gateway_order_id,
            "amount_minor": payment.amount_minor, "currency": payment.currency,
        }), 201

    @api.get("/orders/<public_id>")
    def get_store_order(public_id):
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        order = StoreOrder.query.filter_by(public_id=public_id, customer_id=customer.id).first()
        if not order:
            return error("Order not found.", 404, "order_not_found")
        return jsonify(ok=True, order=_serialize_store_order(order))

    def _confirm_store_order_payment(payment):
        if payment.source_type != 'store_order':
            return False
        order = StoreOrder.query.get(payment.source_id)
        if not order or order.status == 'confirmed':
            return False
        if order.status != 'placed':
            return False
        items = StoreOrderItem.query.filter_by(order_id=order.id).all()
        variants = {row.id: row for row in ProductVariant.query.filter(ProductVariant.id.in_([item.variant_id for item in items])).all()}
        for item in items:
            variant = variants.get(item.variant_id)
            if not variant or int(variant.stock_reserved or 0) < int(item.quantity or 0) or int(variant.stock_on_hand or 0) < int(item.quantity or 0):
                raise RuntimeError("Reserved stock is inconsistent.")
        for item in items:
            variant = variants[item.variant_id]
            variant.stock_on_hand = int(variant.stock_on_hand or 0) - int(item.quantity or 0)
            variant.stock_reserved = int(variant.stock_reserved or 0) - int(item.quantity or 0)
        order.status = transition_order(order.status, 'payment_paid')
        return True

    def _release_store_order_payment(payment):
        if payment.source_type != 'store_order':
            return False
        order = StoreOrder.query.get(payment.source_id)
        if not order or order.status != 'placed':
            return False
        items = StoreOrderItem.query.filter_by(order_id=order.id).all()
        variants = {row.id: row for row in ProductVariant.query.filter(ProductVariant.id.in_([item.variant_id for item in items])).all()}
        for item in items:
            variant = variants.get(item.variant_id)
            if variant:
                variant.stock_reserved = max(int(variant.stock_reserved or 0) - int(item.quantity or 0), 0)
        order.status = 'cancelled'
        return True

    def _serialize_payment(row):
        return {
            "id": row.public_id,
            "source_type": row.source_type,
            "status": row.status,
            "amount_minor": int(row.amount_minor or 0),
            "currency": row.currency or "INR",
            "gateway": row.gateway,
            "gateway_order_id": row.gateway_order_id or "",
            "gateway_payment_id": row.gateway_payment_id or "",
        }

    def _confirm_booking_payment(payment):
        if payment.source_type != "booking":
            return False
        booking = StayBooking.query.get(payment.source_id)
        if not booking:
            return False
        if booking.status == "confirmed":
            return False
        item = StayBookingItem.query.filter_by(booking_id=booking.id).first()
        if not item:
            return False
        hold = StayInventoryHold.query.get(item.hold_id)
        if booking.status == "held":
            booking.status = "pending_payment"
        if booking.status not in {"pending_payment", "held"}:
            return False
        booking.status = "confirmed"
        if hold and hold.status == "active":
            hold.status = "converted"
        return True

    def _loyalty_account(customer_id):
        account = LoyaltyAccount.query.filter_by(customer_id=customer_id).first()
        if account:
            return account
        account = LoyaltyAccount(customer_id=customer_id, status="active")
        db.session.add(account)
        db.session.flush()
        return account

    def _award_loyalty_points(customer_id, source_type, source_id, effect_key, amount_minor, description):
        existing = LoyaltyLedgerEntry.query.filter_by(
            source_type=source_type, source_id=source_id, effect_key=effect_key
        ).first()
        if existing:
            return False
        rate = max(_int_env("LIVENZA_POINTS_PER_100_INR", 1, minimum=0), 0)
        points = points_for_paid_amount(amount_minor, points_per_100_inr=rate)
        if points <= 0:
            return False
        account = _loyalty_account(customer_id)
        db.session.add(LoyaltyLedgerEntry(
            account_id=account.id, direction="credit", points=points,
            source_type=source_type, source_id=source_id, effect_key=effect_key,
            description=str(description or "")[:220],
        ))
        return True

    def _confirm_payment_source(payment):
        if payment.source_type == "booking":
            changed = _confirm_booking_payment(payment)
            if changed:
                _award_loyalty_points(payment.customer_id, "booking", payment.source_id, "stay_booking_paid", payment.amount_minor, "Livenza stay payment")
            return changed
        if payment.source_type == "store_order":
            changed = _confirm_store_order_payment(payment)
            if changed:
                _award_loyalty_points(payment.customer_id, "store_order", payment.source_id, "store_order_paid", payment.amount_minor, "Livenza.store purchase")
            return changed
        return False

    def _release_payment_source(payment):
        if payment.source_type == "booking":
            booking = StayBooking.query.get(payment.source_id)
            if booking and booking.status == "pending_payment":
                booking.status = "held"
                return True
            return False
        if payment.source_type == "store_order":
            return _release_store_order_payment(payment)
        return False

    @api.post("/payments")
    def create_payment():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        payload = request.get_json(silent=True) or {}
        booking_public_id = str(payload.get("booking_id") or "").strip()
        booking = StayBooking.query.filter_by(public_id=booking_public_id, customer_id=customer.id).first()
        if not booking:
            return error("Booking not found.", 404, "booking_not_found")
        if booking.status == "confirmed":
            return error("Booking is already confirmed.", 409, "booking_already_confirmed")
        item = StayBookingItem.query.filter_by(booking_id=booking.id).first()
        hold = StayInventoryHold.query.get(item.hold_id) if item else None
        now = datetime.datetime.utcnow()
        if not hold or hold.status != "active" or hold.expires_at <= now:
            if hold and hold.status == "active" and hold.expires_at <= now:
                hold.status = "expired"
                booking.status = "expired"
                db.session.commit()
            return error("The inventory hold has expired.", 409, "hold_expired")
        existing = PaymentRecord.query.filter_by(
            customer_id=customer.id, source_type="booking", source_id=booking.id, gateway="razorpay"
        ).filter(PaymentRecord.status.in_(["created", "pending"])).order_by(PaymentRecord.id.desc()).first()
        gateway = RazorpayGateway.from_env()
        if existing and existing.gateway_order_id:
            public_cfg = public_gateway_config({"key_id": gateway.key_id})
            return jsonify(ok=True, payment=_serialize_payment(existing), checkout={
                "key_id": public_cfg["key_id"], "order_id": existing.gateway_order_id,
                "amount_minor": existing.amount_minor, "currency": existing.currency,
            })
        try:
            order = gateway.create_order(
                booking.amount_due_now_minor, "INR", f"LVZ-{booking.public_id[:18]}",
                {"booking_id": booking.public_id, "customer_id": customer.public_id},
            )
        except Exception:
            return error("Payment provider is unavailable.", 503, "payment_provider_unavailable")
        payment = PaymentRecord(
            public_id=str(uuid.uuid4()), customer_id=customer.id, source_type="booking", source_id=booking.id,
            gateway="razorpay", gateway_order_id=str(order.get("id") or ""), amount_minor=booking.amount_due_now_minor,
            currency=str(order.get("currency") or "INR"), status="created", metadata_json="{}",
        )
        if booking.status == "held":
            booking.status = "pending_payment"
        db.session.add(payment)
        db.session.commit()
        public_cfg = public_gateway_config({"key_id": gateway.key_id})
        return jsonify(ok=True, payment=_serialize_payment(payment), checkout={
            "key_id": public_cfg["key_id"], "order_id": payment.gateway_order_id,
            "amount_minor": payment.amount_minor, "currency": payment.currency,
        }), 201

    @api.get("/payments/<public_id>")
    def get_payment(public_id):
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        payment = PaymentRecord.query.filter_by(public_id=public_id, customer_id=customer.id).first()
        if not payment:
            return error("Payment not found.", 404, "payment_not_found")
        return jsonify(ok=True, payment=_serialize_payment(payment))

    @api.post("/payments/webhooks/razorpay")
    def razorpay_webhook():
        raw_body = request.get_data(cache=False, as_text=False)
        signature = request.headers.get("X-Razorpay-Signature", "")
        gateway = RazorpayGateway.from_env()
        if not verify_razorpay_webhook(raw_body, signature, gateway.webhook_secret):
            return error("Invalid webhook signature.", 400, "invalid_webhook_signature")
        event_id = (request.headers.get("x-razorpay-event-id") or "").strip()
        if not event_id:
            return error("Webhook event id is required.", 400, "missing_webhook_event_id")
        if ProcessedWebhookEvent.query.filter_by(gateway="razorpay", external_event_id=event_id).first():
            return jsonify(ok=True, duplicate=True)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception:
            return error("Invalid webhook body.", 400, "invalid_webhook_body")
        event_type = str(payload.get("event") or "")
        next_state = payment_event_state(event_type)
        payment_entity = (((payload.get("payload") or {}).get("payment") or {}).get("entity") or {})
        order_entity = (((payload.get("payload") or {}).get("order") or {}).get("entity") or {})
        gateway_order_id = str(payment_entity.get("order_id") or order_entity.get("id") or "")
        gateway_payment_id = str(payment_entity.get("id") or "")
        processed = ProcessedWebhookEvent(
            gateway="razorpay", external_event_id=event_id, event_type=event_type,
            processed_at=datetime.datetime.utcnow(),
        )
        db.session.add(processed)
        payment = PaymentRecord.query.filter_by(gateway="razorpay", gateway_order_id=gateway_order_id).first() if gateway_order_id else None
        if not payment:
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                return jsonify(ok=True, duplicate=True)
            return jsonify(ok=True, ignored=True), 202
        if gateway_payment_id:
            payment.gateway_payment_id = gateway_payment_id
        if next_state == "failed":
            payment.status = "failed"
            _release_payment_source(payment)
        if next_state == "paid":
            payment.status = "paid"
            _confirm_payment_source(payment)
        if next_state == "pending" and payment.status not in {"paid", "failed"}:
            payment.status = "pending"
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            if ProcessedWebhookEvent.query.filter_by(gateway="razorpay", external_event_id=event_id).first():
                return jsonify(ok=True, duplicate=True)
            raise
        if next_state == "paid":
            customer=Customer.query.get(payment.customer_id)
            if customer:
                try:
                    notify("payment.received",customer,{"reference":payment.public_id},["email","whatsapp"])
                    if payment.source_type == "booking":
                        booking=StayBooking.query.get(payment.source_id)
                        if booking and booking.status == "confirmed":
                            notify("booking.confirmed",customer,{"booking_id":booking.public_id},["email","whatsapp"])
                    elif payment.source_type == "store_order":
                        order=StoreOrder.query.get(payment.source_id)
                        if order and order.status == "confirmed":
                            notify("order.confirmed",customer,{"order_id":order.public_id},["email","whatsapp"])
                except Exception:
                    pass
        return jsonify(ok=True, status=payment.status)

    @api.post("/booking-shares/<token>/payments")
    def create_parent_share_payment(token):
        _session_row, payer_customer = session_for_request()
        if not payer_customer:
            return error("Authentication required.", 401, "authentication_required")
        digest = hash_share_token(token)
        row = BookingShareToken.query.filter_by(token_hash=digest, revoked_at=None).first()
        if not row:
            return error("Share link not found.", 404, "share_not_found")
        now = datetime.datetime.utcnow()
        if row.expires_at <= now:
            return error("Share link has expired.", 410, "share_expired")
        booking = StayBooking.query.get(row.booking_id)
        if not booking:
            return error("Booking not found.", 404, "booking_not_found")
        if booking.status == "confirmed":
            return error("Booking is already confirmed.", 409, "booking_already_confirmed")
        item = StayBookingItem.query.filter_by(booking_id=booking.id).first()
        hold = StayInventoryHold.query.get(item.hold_id) if item else None
        if not hold or hold.status != "active" or hold.expires_at <= now:
            return error("The inventory hold has expired.", 409, "hold_expired")
        existing = PaymentRecord.query.filter_by(
            customer_id=booking.customer_id, source_type="booking", source_id=booking.id, gateway="razorpay"
        ).filter(PaymentRecord.status.in_(["created", "pending"])).order_by(PaymentRecord.id.desc()).first()
        gateway = RazorpayGateway.from_env()
        if existing and existing.gateway_order_id:
            public_cfg = public_gateway_config({"key_id": gateway.key_id})
            return jsonify(ok=True, payment=_serialize_payment(existing), checkout={
                "key_id": public_cfg["key_id"], "order_id": existing.gateway_order_id,
                "amount_minor": existing.amount_minor, "currency": existing.currency,
            })
        try:
            order = gateway.create_order(
                booking.amount_due_now_minor, "INR", f"LVZ-P-{booking.public_id[:16]}",
                {"booking_id": booking.public_id, "payer_customer_public_id": payer_customer.public_id},
            )
        except Exception:
            return error("Payment provider is unavailable.", 503, "payment_provider_unavailable")
        metadata = {
            "payer_customer_public_id": payer_customer.public_id,
            "payer_mobile": payer_customer.primary_mobile or "",
            "payment_context": "parent_share",
        }
        payment = PaymentRecord(
            public_id=str(uuid.uuid4()), customer_id=booking.customer_id, source_type="booking", source_id=booking.id,
            gateway="razorpay", gateway_order_id=str(order.get("id") or ""), amount_minor=booking.amount_due_now_minor,
            currency=str(order.get("currency") or "INR"), status="created", metadata_json=json.dumps(metadata, separators=(",", ":")),
        )
        if booking.status == "held":
            booking.status = "pending_payment"
        db.session.add(payment)
        db.session.commit()
        public_cfg = public_gateway_config({"key_id": gateway.key_id})
        return jsonify(ok=True, payment=_serialize_payment(payment), checkout={
            "key_id": public_cfg["key_id"], "order_id": payment.gateway_order_id,
            "amount_minor": payment.amount_minor, "currency": payment.currency,
        }), 201

    @api.get("/bookings/<public_id>/receipt")
    def booking_receipt(public_id):
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        booking = StayBooking.query.filter_by(public_id=public_id, customer_id=customer.id).first()
        if not booking:
            return error("Booking not found.", 404, "booking_not_found")
        payment = PaymentRecord.query.filter_by(
            customer_id=customer.id, source_type="booking", source_id=booking.id
        ).order_by(PaymentRecord.id.desc()).first()
        if not payment or payment.status != "paid":
            return error("A paid transaction is required before a receipt is available.", 409, "receipt_not_ready")
        prop = StayProperty.query.get(booking.property_id)
        paid_at = (payment.updated_at or payment.created_at or datetime.datetime.utcnow()).isoformat()
        view = build_receipt_view(
            booking_id=booking.public_id, payment_id=payment.public_id,
            property_name=prop.name if prop else "Livenza stay",
            amount_minor=payment.amount_minor, currency=payment.currency or "INR", paid_at=paid_at,
        )
        response = make_response(render_receipt_html(view), 200)
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        response.headers["Cache-Control"] = "private, no-store"
        return response

    @api.get("/me/orders")
    def my_orders():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        rows = StoreOrder.query.filter_by(customer_id=customer.id).order_by(StoreOrder.id.desc()).all()
        return jsonify(items=[_serialize_store_order(row) for row in rows])

    @api.get("/me/rewards")
    def my_rewards():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        account = LoyaltyAccount.query.filter_by(customer_id=customer.id).first()
        if not account:
            account = _loyalty_account(customer.id)
            db.session.commit()
        entries = LoyaltyLedgerEntry.query.filter_by(account_id=account.id).order_by(LoyaltyLedgerEntry.id.desc()).all()
        current_balance = balance([(row.direction, row.points) for row in entries])
        return jsonify(ok=True, rewards={
            "status": account.status or "active",
            "balance": current_balance,
            "entries": [{
                "id": row.id, "direction": row.direction, "points": int(row.points or 0),
                "source_type": row.source_type, "source_id": row.source_id,
                "effect_key": row.effect_key, "description": row.description or "",
                "created_at": row.created_at.isoformat() if row.created_at else None,
            } for row in entries],
        })

    @api.get("/me/delivery-options")
    def my_delivery_options():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        # Eligibility is derived only from confirmed current stays and the
        # LIVENZA_INTERNAL_DELIVERY_PROPERTIES configuration; the request body
        # cannot self-assert a property or room.
        items = _eligible_property_room_delivery(customer.id)
        return jsonify(items=items)

    @api.get("/me/stays")
    def my_stays():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        rows = StayBooking.query.filter_by(customer_id=customer.id).order_by(StayBooking.created_at.desc()).all()
        items = []
        for row in rows:
            prop = StayProperty.query.get(row.property_id)
            item = _serialize_booking(row)
            item["property"] = {"name": prop.name if prop else "Livenza stay", "city": prop.city if prop else "", "area": prop.area if prop else ""}
            items.append(item)
        return jsonify(items=items)

    @api.get("/me/payments")
    def my_payments():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        rows = PaymentRecord.query.filter_by(customer_id=customer.id).order_by(PaymentRecord.created_at.desc()).all()
        return jsonify(items=[_serialize_payment(row) for row in rows])

    @api.get("/me/documents")
    def my_documents():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        rows = CustomerDocument.query.filter_by(customer_id=customer.id).order_by(CustomerDocument.created_at.desc()).all()
        return jsonify(items=[{
            "id": row.id, "booking_id": row.booking_id, "document_type": row.document_type,
            "display_name": row.display_name, "private": bool(row.private),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        } for row in rows])

    @api.get("/me/documents/<int:document_id>/download")
    def my_document_download(document_id):
        session_row, customer = session_for_request()
        if not session_row or not customer:
            return error("Authentication required.",401,"authentication_required")
        document=CustomerDocument.query.get(document_id)
        if not document or document.customer_id != customer.id:
            return error("Document not found.",404,"not_found")
        try:
            signed_url=storage.signed_get_url(document.storage_key,expires_seconds=300)
        except Exception:
            return error("Document storage is temporarily unavailable.",503,"storage_unavailable")
        return jsonify(ok=True,url=signed_url,expires_in_seconds=300)

    @api.get("/me/support")
    def my_support():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        rows = SupportTicket.query.filter_by(customer_id=customer.id).order_by(SupportTicket.created_at.desc()).all()
        return jsonify(items=[{
            "id": row.public_id, "category": row.category, "subject": row.subject,
            "description": row.description, "status": row.status,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        } for row in rows])

    @api.post("/me/support")
    def create_support_ticket():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        payload = request.get_json(silent=True) or {}
        category = str(payload.get("category") or "").strip().lower()
        allowed = {"stay", "payment", "store", "account", "other"}
        if category not in allowed:
            return error("Unsupported support category.", 400, "invalid_support_category")
        subject = str(payload.get("subject") or "").strip()
        description = str(payload.get("description") or "").strip()
        if not subject or len(subject) > 180:
            return error("Subject must be 1 to 180 characters.", 400, "invalid_subject")
        if not description or len(description) > 5000:
            return error("Description must be 1 to 5000 characters.", 400, "invalid_description")
        row = SupportTicket(
            public_id=str(uuid.uuid4()), customer_id=customer.id, category=category,
            subject=subject, description=description, status="open",
        )
        db.session.add(row)
        db.session.commit()
        try: notify("support.updated",customer,{"ticket_id":row.public_id},["email","whatsapp"])
        except Exception: pass
        return jsonify(ok=True, ticket={"id":row.public_id,"category":row.category,"subject":row.subject,"description":row.description,"status":row.status}), 201

    @api.patch("/me/profile")
    def patch_me_profile():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        payload = request.get_json(silent=True) or {}
        if "full_name" in payload:
            full_name = str(payload.get("full_name") or "").strip()[:180]
            customer.full_name = full_name
        if "primary_email" in payload:
            email = str(payload.get("primary_email") or "").strip().lower()[:220]
            if email and ("@" not in email or "." not in email.rsplit("@", 1)[-1]):
                return error("A valid email address is required.", 400, "invalid_email")
            customer.primary_email = email
        db.session.commit()
        return jsonify(ok=True, customer=_serialize_customer(customer))

    app.register_blueprint(api)
    return api
