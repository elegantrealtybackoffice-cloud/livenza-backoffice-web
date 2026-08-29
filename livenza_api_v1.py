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


def register_api_v1(app, db, models, send_otp):
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
            metadata = item.get("metadata") if isinstance(item, dict) and isinstance(item.get("metadata"), dict) else {}
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
            booking = StayBooking.query.get(payment.source_id) if payment.source_type == "booking" else None
            if booking and booking.status == "pending_payment":
                booking.status = "held"
        if next_state == "paid":
            payment.status = "paid"
            _confirm_booking_payment(payment)
        if next_state == "pending" and payment.status not in {"paid", "failed"}:
            payment.status = "pending"
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            if ProcessedWebhookEvent.query.filter_by(gateway="razorpay", external_event_id=event_id).first():
                return jsonify(ok=True, duplicate=True)
            raise
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
