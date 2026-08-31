"""Versioned consumer API for Livenza.life V1.

This module deliberately avoids importing app.py or Flask at module-import time.
The back-office injects db/models/provider adapters through register_api_v1().
"""
import datetime
import hashlib
import hmac
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
from livenza_booking_core import validate_booking_dates, hold_expiry, payment_hold_expiry, amount_due_now, booking_price_quote, hash_share_token
from livenza_payment_core import verify_razorpay_webhook, payment_event_state, public_gateway_config, verify_cashfree_webhook, cashfree_payment_event_state
from livenza_integrations import RazorpayGateway, CashfreeGateway, RadiusAdapter
from livenza_receipts import build_receipt_view, render_receipt_html
from livenza_commerce_core import available_stock, validate_quantity, calculate_order_totals, transition_order
from livenza_loyalty_core import balance, points_for_paid_amount
from livenza_storage import storage_from_env
from livenza_tenant_core import normalize_tenancy_type, required_profile_fields, missing_profile_fields, required_document_types, mask_government_identifier
from livenza_dues_core import outstanding_minor, due_status
from livenza_meter_core import normalize_recharge_amount, recharge_can_start, masked_meter_label
from livenza_resident_core import normalize_capabilities, capability_enabled
from livenza_referral_core import normalize_referral_code, referral_code_for_seed, referral_source_qualifies

COOKIE_NAME = "livenza_customer_session"

_TENANT_DOCUMENT_TYPES = {
    "government_id": "Government ID",
    "student_id": "Student / Institute ID",
    "corporate_id": "Corporate / Employee ID",
    "passport_visa": "Passport / Visa",
    "pan": "PAN",
    "additional": "Additional document",
}
_TENANT_DOCUMENT_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}
_TENANT_DOCUMENT_MAX_BYTES = 10 * 1024 * 1024


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


def serialize_property(row, cover_media=None):
    payload = {
        "id": row.id,
        "slug": row.slug,
        "name": row.name,
        "city": row.city,
        "area": row.area or "",
        "summary": row.summary or "",
        "stay_types": row.stay_types,
    }
    if cover_media:
        payload["cover_media"] = cover_media
    return payload


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
    TenantOnboarding = models["TenantOnboarding"]
    CustomerAgreement = models["CustomerAgreement"]
    TenantDue = models["TenantDue"]
    TenantDueAllocation = models["TenantDueAllocation"]
    TenantMeterAccount = models["TenantMeterAccount"]
    MeterRecharge = models["MeterRecharge"]
    SupportTicket = models["SupportTicket"]
    ResidentPropertyPolicy = models["ResidentPropertyPolicy"]
    ResidentNotice = models["ResidentNotice"]
    ResidentLeaveRequest = models["ResidentLeaveRequest"]
    ResidentGuestRequest = models["ResidentGuestRequest"]
    PropertyMenu = models["PropertyMenu"]
    Product = models["Product"]
    ProductVariant = models["ProductVariant"]
    StoreOrder = models["StoreOrder"]
    StoreOrderItem = models["StoreOrderItem"]
    LoyaltyAccount = models["LoyaltyAccount"]
    LoyaltyLedgerEntry = models["LoyaltyLedgerEntry"]
    ReferralIdentity = models["ReferralIdentity"]
    ReferralEvent = models["ReferralEvent"]
    ResidentOffer = models["ResidentOffer"]
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

    def _resident_context(customer):
        if not customer:
            return None, None, None, (), None
        booking = StayBooking.query.filter_by(customer_id=customer.id).filter(
            StayBooking.status.notin_(["cancelled", "expired"])
        ).order_by(StayBooking.created_at.desc(), StayBooking.id.desc()).first()
        property_row = StayProperty.query.get(booking.property_id) if booking else None
        onboarding = None
        if booking:
            onboarding = TenantOnboarding.query.filter_by(customer_id=customer.id, booking_id=booking.id).first()
        if not onboarding:
            onboarding = TenantOnboarding.query.filter_by(customer_id=customer.id).order_by(
                TenantOnboarding.created_at.desc(), TenantOnboarding.id.desc()
            ).first()
        policy = ResidentPropertyPolicy.query.filter_by(property_id=property_row.id).first() if property_row else None
        capabilities = normalize_capabilities(policy.capabilities_json if policy else None)
        return booking, property_row, onboarding, capabilities, policy

    def _parse_client_datetime(value):
        text = str(value or "").strip()
        if not text:
            raise ValueError("A date and time are required.")
        try:
            parsed = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
        except Exception as exc:
            raise ValueError("Use a valid ISO date and time.") from exc
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return parsed

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

    _ONBOARDING_BOOKING_STATUSES = {"pending_payment", "payment_review", "confirmed"}
    _ONBOARDING_PROFILE_FIELDS = {
        "full_name", "date_of_birth", "gender", "nationality", "permanent_address", "current_address",
        "emergency_contact_name", "emergency_contact_mobile", "guardian_name", "guardian_mobile",
        "guardian_email", "father_name", "mother_name", "institute_name", "course", "academic_year",
        "employer_name", "employee_id", "designation", "department", "employer_address",
        "employer_contact_name", "employer_contact_mobile", "company_gst", "booking_source",
        "ota_reference", "purpose_of_stay", "marital_status",
    }

    def _onboarding_booking(row):
        return StayBooking.query.get(row.booking_id) if row and row.booking_id else None

    def _latest_eligible_booking(customer_id):
        return StayBooking.query.filter(
            StayBooking.customer_id == customer_id,
            StayBooking.status.in_(sorted(_ONBOARDING_BOOKING_STATUSES)),
        ).order_by(StayBooking.created_at.desc(), StayBooking.id.desc()).first()

    def _get_or_create_onboarding(customer):
        row = TenantOnboarding.query.filter_by(customer_id=customer.id).filter(
            TenantOnboarding.status != "cancelled"
        ).order_by(TenantOnboarding.id.desc()).first()
        if row:
            return row, _onboarding_booking(row), True, False
        booking = _latest_eligible_booking(customer.id)
        if not booking:
            return None, None, False, False
        tenancy_type = normalize_tenancy_type(booking.stay_type)
        initial_profile = {}
        if customer.full_name:
            initial_profile["full_name"] = customer.full_name
        row = TenantOnboarding(
            public_id=str(uuid.uuid4()), customer_id=customer.id, booking_id=booking.id,
            tenancy_type=tenancy_type, status="in_progress", current_step="profile",
            profile_json=json.dumps(initial_profile, ensure_ascii=False),
        )
        db.session.add(row)
        db.session.flush()
        return row, booking, True, True

    def _active_onboarding_documents(row):
        if not row:
            return []
        return CustomerDocument.query.filter_by(
            customer_id=row.customer_id, onboarding_id=row.id
        ).filter(CustomerDocument.verification_status != "withdrawn").order_by(
            CustomerDocument.created_at.desc(), CustomerDocument.id.desc()
        ).all()

    def _serialize_onboarding_document(document):
        return {
            "id": document.public_id or str(document.id),
            "document_type": document.document_type,
            "display_name": document.display_name,
            "private": bool(document.private),
            "verification_status": document.verification_status or "submitted",
            "verification_note": document.verification_note or "",
            "masked_identifier": document.masked_identifier or "",
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if getattr(document, "updated_at", None) else None,
        }

    def _serialize_onboarding(row, booking=None):
        if not row:
            return None
        profile = row.profile if hasattr(row, "profile") else {}
        required = list(required_profile_fields(row.tenancy_type))
        missing = list(missing_profile_fields(row.tenancy_type, profile))
        profile_complete = not missing
        documents = _active_onboarding_documents(row)
        latest_by_type = {}
        for document in documents:
            latest_by_type.setdefault(document.document_type, document)
        required_docs = list(required_document_types(row.tenancy_type))
        missing_docs = [doc_type for doc_type in required_docs if doc_type not in latest_by_type]
        documents_complete = not missing_docs
        documents_verified = documents_complete and all(
            (latest_by_type[doc_type].verification_status or "") == "verified"
            for doc_type in required_docs
        )
        current_step = row.current_step or "profile"
        if not profile_complete:
            current_step = "profile"
        elif not documents_complete:
            current_step = "documents"
        elif not documents_verified and current_step in {"profile", "documents", "verification"}:
            current_step = "verification"
        return {
            "id": row.public_id,
            "booking_id": booking.public_id if booking else None,
            "tenancy_type": row.tenancy_type,
            "status": row.status,
            "current_step": current_step,
            "profile": profile,
            "required_fields": required,
            "missing_fields": missing,
            "profile_complete": profile_complete,
            "required_document_types": required_docs,
            "missing_document_types": missing_docs,
            "documents_complete": documents_complete,
            "documents_verified": documents_verified,
            "documents": [_serialize_onboarding_document(item) for item in documents],
            "completed_at": row.completed_at.isoformat() if row.completed_at else None,
        }

    @api.get("/me/onboarding")
    def my_onboarding():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        row, booking, eligible, created = _get_or_create_onboarding(customer)
        if created:
            db.session.commit()
        return jsonify(ok=True, eligible=eligible, onboarding=_serialize_onboarding(row, booking))

    @api.patch("/me/onboarding/profile")
    def patch_my_onboarding_profile():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        row, booking, eligible, created = _get_or_create_onboarding(customer)
        if not eligible or not row:
            return error("No eligible tenancy onboarding is available.", 404, "onboarding_not_available")
        payload = request.get_json(silent=True) or {}
        requested_tenancy = payload.get("tenancy_type")
        if requested_tenancy is not None:
            try:
                normalized = normalize_tenancy_type(requested_tenancy)
            except ValueError as exc:
                return error(str(exc), 400, "invalid_tenancy_type")
            if booking and normalized != normalize_tenancy_type(booking.stay_type):
                return error("Tenancy type is fixed by this booking.", 409, "tenancy_type_mismatch")
            row.tenancy_type = normalized
        incoming = payload.get("profile") or {}
        if not isinstance(incoming, dict):
            return error("profile must be an object.", 400, "invalid_profile")
        profile = dict(row.profile if hasattr(row, "profile") else {})
        for key, value in incoming.items():
            key = str(key or "").strip()
            if key not in _ONBOARDING_PROFILE_FIELDS:
                continue
            if value is None:
                profile.pop(key, None)
                continue
            text = str(value).strip()
            profile[key] = text[:1000 if key.endswith("address") else 220]
        row.profile_json = json.dumps(profile, ensure_ascii=False)
        if profile.get("full_name"):
            customer.full_name = profile["full_name"][:180]
        missing = missing_profile_fields(row.tenancy_type, profile)
        row.current_step = "profile" if missing else "documents"
        row.status = "in_progress"
        db.session.commit()
        return jsonify(ok=True, onboarding=_serialize_onboarding(row, booking))

    @api.post("/me/onboarding/documents")
    def upload_my_onboarding_document():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        row, booking, eligible, created = _get_or_create_onboarding(customer)
        if not eligible or not row:
            return error("No eligible tenancy onboarding is available.", 404, "onboarding_not_available")
        if missing_profile_fields(row.tenancy_type, row.profile):
            return error("Complete your tenant profile before uploading documents.", 409, "profile_incomplete")
        document_type = str(request.form.get("document_type") or "").strip().lower()
        if document_type not in _TENANT_DOCUMENT_TYPES:
            return error("Unsupported document type.", 400, "invalid_document_type")
        upload = request.files.get("file")
        if not upload or not upload.filename:
            return error("A document file is required.", 400, "missing_document")
        mime = str(upload.mimetype or "").strip().lower()
        extension = _TENANT_DOCUMENT_MIME_TYPES.get(mime)
        if not extension:
            return error("Use a PDF, JPG or PNG document.", 415, "unsupported_document_type")
        raw = upload.stream.read(_TENANT_DOCUMENT_MAX_BYTES + 1)
        if not raw:
            return error("The document is empty.", 400, "empty_document")
        if len(raw) > _TENANT_DOCUMENT_MAX_BYTES:
            return error("The document is larger than 10 MB.", 413, "document_too_large")
        identifier = str(request.form.get("identifier") or "").strip()
        masked_identifier = mask_government_identifier(identifier) if identifier else ""
        public_id = str(uuid.uuid4())
        storage_key = f"customer-documents/{customer.public_id}/{row.public_id}/{public_id}{extension}"
        try:
            storage.put_private(storage_key, raw, mime)
        except Exception:
            return error("Private document storage is temporarily unavailable.", 503, "storage_unavailable")
        document = CustomerDocument(
            public_id=public_id, customer_id=customer.id, booking_id=row.booking_id, onboarding_id=row.id,
            document_type=document_type, display_name=str(upload.filename)[:180], storage_key=storage_key,
            private=True, verification_status="submitted", verification_note="",
            masked_identifier=masked_identifier,
        )
        db.session.add(document)
        db.session.flush()
        row.current_step = "verification" if not _serialize_onboarding(row, booking)["missing_document_types"] else "documents"
        db.session.commit()
        return jsonify(ok=True, document=_serialize_onboarding_document(document), onboarding=_serialize_onboarding(row, booking)), 201

    @api.delete("/me/onboarding/documents/<document_public_id>")
    def delete_my_onboarding_document(document_public_id):
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        row, booking, eligible, created = _get_or_create_onboarding(customer)
        if not eligible or not row:
            return error("No eligible tenancy onboarding is available.", 404, "onboarding_not_available")
        document = CustomerDocument.query.filter_by(
            public_id=document_public_id, customer_id=customer.id, onboarding_id=row.id
        ).first()
        if not document or document.verification_status == "withdrawn":
            return error("Document not found.", 404, "not_found")
        if document.verification_status == "verified":
            return error("A verified document cannot be removed. Contact Livenza support for a replacement.", 409, "document_locked")
        document.verification_status = "withdrawn"
        document.verification_note = "Withdrawn by tenant before verification."
        row.current_step = "documents"
        db.session.commit()
        return jsonify(ok=True, onboarding=_serialize_onboarding(row, booking))

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
        check_in = (request.args.get("check_in") or "").strip()
        check_out = (request.args.get("check_out") or "").strip()
        search_start = search_end = None
        if check_in or check_out:
            if not check_in or not check_out:
                return error("check_in and check_out must be provided together.", 400, "invalid_dates")
            try:
                search_start = datetime.date.fromisoformat(check_in)
                search_end = datetime.date.fromisoformat(check_out)
            except ValueError:
                return error("check_in and check_out must use YYYY-MM-DD.", 400, "invalid_dates")
            if search_end <= search_start:
                return error("check_out must be after check_in.", 400, "invalid_date_range")
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

        availability_by_property = {}
        if search_start and search_end:
            now = datetime.datetime.utcnow()
            available_rows = []
            for row in rows:
                categories = StayRoomCategory.query.filter_by(property_id=row.id, active=True).all()
                category_ids = [item.id for item in categories]
                if not category_ids:
                    continue
                plan_query = StayRatePlan.query.filter_by(property_id=row.id, active=True).filter(
                    StayRatePlan.room_category_id.in_(category_ids)
                )
                if stay_type:
                    plan_query = plan_query.filter(StayRatePlan.stay_type == stay_type)
                bookable_category_ids = {item[0] for item in plan_query.with_entities(StayRatePlan.room_category_id).distinct().all()}
                if not bookable_category_ids:
                    continue
                units = StayInventoryUnit.query.filter(
                    StayInventoryUnit.property_id == row.id,
                    StayInventoryUnit.room_category_id.in_(list(bookable_category_ids)),
                    StayInventoryUnit.allocatable.is_(True),
                    StayInventoryUnit.active.is_(True),
                ).all()
                if not units:
                    continue
                blocked_ids = _blocked_inventory_ids([item.id for item in units], search_start, search_end, now)
                available_count = sum(1 for item in units if item.id not in blocked_ids)
                if available_count < 1:
                    continue
                available_rows.append(row)
                availability_by_property[row.id] = {
                    "check_in": search_start.isoformat(),
                    "check_out": search_end.isoformat(),
                    "available_count": available_count,
                    "availability_state": availability_state(len(units), len(blocked_ids)),
                }
            rows = available_rows

        cover_by_property = {}
        property_ids = [row.id for row in rows]
        if property_ids:
            media_rows = PropertyMedia.query.filter(
                PropertyMedia.property_id.in_(property_ids),
                PropertyMedia.public.is_(True),
            ).order_by(PropertyMedia.property_id.asc(), PropertyMedia.sort_order.asc(), PropertyMedia.id.asc()).all()
            for item in media_rows:
                if item.property_id in cover_by_property:
                    continue
                try:
                    public_url = storage.public_url(item.storage_key)
                except Exception:
                    public_url = ''
                if public_url:
                    cover_by_property[item.property_id] = {
                        "type": item.media_type,
                        "alt_text": item.alt_text or "",
                        "url": public_url,
                    }
        items = []
        for row in rows:
            payload = serialize_property(row, cover_media=cover_by_property.get(row.id))
            if row.id in availability_by_property:
                payload["availability"] = availability_by_property[row.id]
            items.append(payload)
        return jsonify(items=items)

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

    def _booking_pricing(rate_plan, addons, mode):
        if not isinstance(addons, list):
            raise TypeError("addons must be a list.")
        catalog = _booking_addon_catalog()
        addon_rows = []
        addon_amounts = []
        for item in addons:
            code = str(item.get("code") if isinstance(item, dict) else item or "").strip()[:80]
            if not code:
                continue
            published = catalog.get(code)
            if not published:
                raise LookupError("One or more add-ons are unavailable.")
            amount = int(published["amount_minor"])
            addon_amounts.append(amount)
            metadata = {
                key: published[key]
                for key in ("source_product_id", "source_variant_id", "source_sku")
                if published.get(key) is not None
            }
            addon_rows.append((code, published["label"], amount, metadata))
        pricing = booking_price_quote(
            int(rate_plan.amount_minor or 0),
            int(rate_plan.security_deposit_minor or 0),
            addon_amounts,
            mode,
            int(rate_plan.reservation_amount_minor or 0),
        )
        pricing.update({
            "booking_mode": str(mode or "").strip().lower(),
            "currency": str(rate_plan.currency or "INR"),
            "rate_plan_code": rate_plan.code,
            "stay_type": rate_plan.stay_type,
            "addons": [
                {"code": code, "label": label, "amount_minor": amount}
                for code, label, amount, _metadata in addon_rows
            ],
        })
        return pricing, addon_rows

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

    @api.post("/bookings/quote")
    def booking_quote():
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
        mode = str(payload.get("booking_mode") or "book_now").strip().lower()
        try:
            pricing, _addon_rows = _booking_pricing(rate_plan, payload.get("addons") or [], mode)
        except TypeError as exc:
            return error(str(exc), 400, "invalid_addons")
        except LookupError as exc:
            return error(str(exc), 400, "invalid_addon")
        except ValueError as exc:
            return error(str(exc), 400, "invalid_booking_mode")
        pricing.update({
            "property": prop.slug,
            "room_category": category.slug,
            "start": start.isoformat(),
            "end": end.isoformat(),
        })
        return jsonify(ok=True, quote=pricing)

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
        guardian = payload.get("guardian") or {}
        if rate_plan.stay_type == "student":
            if not isinstance(guardian, dict) or not str(guardian.get("name") or "").strip() or not str(guardian.get("mobile") or "").strip():
                return error("Guardian name and mobile are required for student bookings.", 400, "guardian_required")
        try:
            pricing, addon_rows = _booking_pricing(rate_plan, addons, mode)
        except TypeError as exc:
            return error(str(exc), 400, "invalid_addons")
        except LookupError as exc:
            return error(str(exc), 400, "invalid_addon")
        except ValueError as exc:
            return error(str(exc), 400, "invalid_booking_mode")
        booking = StayBooking(
            public_id=str(uuid.uuid4()), customer_id=customer.id, property_id=prop.id, rate_plan_id=rate_plan.id,
            booking_mode=mode, stay_type=rate_plan.stay_type, start_date=hold.start_date, end_date=hold.end_date,
            status="held", subtotal_minor=pricing["subtotal_minor"], security_deposit_minor=pricing["security_deposit_minor"], addon_total_minor=pricing["addon_total_minor"],
            total_minor=pricing["total_minor"], amount_due_now_minor=pricing["amount_due_now_minor"], guardian_json=json.dumps(guardian, separators=(",", ":")),
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
        gateway = CashfreeGateway.from_env()
        payment_public_id=str(uuid.uuid4())
        context=_cashfree_order_context(payment_public_id,customer,{"source_type":"store_order","store_order_id":order.public_id,"customer_id":customer.public_id})
        try:
            gateway_order = gateway.create_order(order.total_minor,"INR",context["order_id"],context["customer"],context["notes"],context["return_url"],context["notify_url"])
        except Exception:
            db.session.rollback()
            return error("Payment provider is unavailable.", 503, "payment_provider_unavailable")
        metadata={"payment_session_id":str(gateway_order.get("payment_session_id") or ""),"cf_order_id":str(gateway_order.get("cf_order_id") or ""),"cashfree_mode":gateway.environment}
        payment = PaymentRecord(
            public_id=payment_public_id, customer_id=customer.id, source_type="store_order", source_id=order.id,
            gateway="cashfree", gateway_order_id=str(gateway_order.get("order_id") or context["order_id"]), amount_minor=order.total_minor,
            currency=str(gateway_order.get("order_currency") or "INR"), status="created", metadata_json=json.dumps(metadata,separators=(",",":")),
        )
        db.session.add(payment)
        db.session.commit()
        return jsonify(ok=True, order=_serialize_store_order(order), payment=_serialize_payment(payment), checkout=_cashfree_checkout(payment)), 201

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

    def _tenant_due_allocated_minor(due):
        rows = TenantDueAllocation.query.filter_by(due_id=due.id).all()
        return sum(max(int(row.amount_minor or 0), 0) for row in rows)

    def _serialize_tenant_due(due):
        allocated = _tenant_due_allocated_minor(due)
        remaining = outstanding_minor(due.amount_minor, allocated)
        computed_status = due_status(due.amount_minor, allocated)
        if due.status not in {"waived", "cancelled"}:
            due.status = computed_status
        return {
            "id": due.public_id,
            "booking_id": due.booking_id,
            "onboarding_id": due.onboarding_id,
            "due_type": due.due_type,
            "description": due.description or "",
            "amount_minor": int(due.amount_minor or 0),
            "allocated_minor": allocated,
            "outstanding_minor": 0 if due.status in {"waived", "cancelled"} else remaining,
            "status": due.status or computed_status,
            "due_date": due.due_date.isoformat() if due.due_date else None,
            "created_at": due.created_at.isoformat() if due.created_at else None,
            "updated_at": due.updated_at.isoformat() if due.updated_at else None,
        }

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

    def _payment_metadata(row):
        try:
            value=json.loads(row.metadata_json or "{}")
            return value if isinstance(value,dict) else {}
        except Exception:
            return {}

    def _cashfree_checkout(payment):
        metadata=_payment_metadata(payment)
        return {
            "provider":"cashfree",
            "order_id":payment.gateway_order_id or "",
            "payment_session_id":str(metadata.get("payment_session_id") or ""),
            "mode":str(metadata.get("cashfree_mode") or "sandbox"),
            "amount_minor":int(payment.amount_minor or 0),
            "currency":payment.currency or "INR",
        }

    def _cashfree_order_context(payment_public_id, customer, notes):
        site=(os.getenv("LIVENZA_SITE_URL") or "https://livenza.life").rstrip("/")
        api_origin=(os.getenv("LIVENZA_API_PUBLIC_URL") or request.host_url.rstrip("/")).rstrip("/")
        return {
            "order_id":f"lvz_{str(payment_public_id).replace('-','')[:28]}",
            "customer":{
                "id":customer.public_id or str(customer.id),
                "phone":customer.primary_mobile or "",
                "name":customer.full_name or "",
                "email":customer.primary_email or "",
            },
            "notes":notes or {},
            "return_url":f"{site}/pay/{payment_public_id}",
            "notify_url":f"{api_origin}/api/v1/payments/webhooks/cashfree",
        }

    def _extend_payment_hold(hold, now):
        minutes = _int_env("BOOKING_PAYMENT_HOLD_MINUTES", 20, minimum=1)
        hold.expires_at = payment_hold_expiry(now, hold.expires_at, minutes)
        return hold.expires_at

    def _lock_booking_inventory(item):
        query = StayInventoryUnit.query.filter_by(id=item.inventory_unit_id)
        try:
            if db.engine.dialect.name == "postgresql":
                query = query.with_for_update()
        except Exception:
            pass
        return query.first()

    def _booking_inventory_conflict(booking, item, hold, now):
        confirmed = db.session.query(StayBookingItem.id).join(
            StayBooking, StayBooking.id == StayBookingItem.booking_id
        ).filter(
            StayBookingItem.inventory_unit_id == item.inventory_unit_id,
            StayBookingItem.booking_id != booking.id,
            StayBooking.status == "confirmed",
            StayBooking.start_date < booking.end_date,
            StayBooking.end_date > booking.start_date,
        ).first()
        if confirmed:
            return True
        if not hold:
            return True
        competing_hold = StayInventoryHold.query.filter(
            StayInventoryHold.inventory_unit_id == item.inventory_unit_id,
            StayInventoryHold.id != hold.id,
            StayInventoryHold.status == "active",
            StayInventoryHold.expires_at > now,
            StayInventoryHold.start_date < booking.end_date,
            StayInventoryHold.end_date > booking.start_date,
        ).first()
        return bool(competing_hold)

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
        now = datetime.datetime.utcnow()
        if not _lock_booking_inventory(item) or _booking_inventory_conflict(booking, item, hold, now):
            booking.status = "payment_review"
            if hold and hold.status == "active":
                hold.status = "payment_review"
            return False
        booking.status = "confirmed"
        if hold and hold.status == "active":
            hold.status = "converted"
        elif hold and hold.status == "expired":
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

    def _referral_identity(customer_id):
        row=ReferralIdentity.query.filter_by(customer_id=customer_id).first()
        if row:
            return row
        customer=Customer.query.get(customer_id)
        seed=f"{getattr(customer,'public_id','')}:{customer_id}"
        code=referral_code_for_seed(seed)
        suffix=0
        while ReferralIdentity.query.filter_by(code=code).first():
            suffix+=1;code=referral_code_for_seed(f"{seed}:{suffix}")
        row=ReferralIdentity(customer_id=customer_id,code=code,status="active")
        db.session.add(row);db.session.flush();return row

    def _qualify_referral(customer_id, source_type, source_id, payment_status):
        if not referral_source_qualifies(source_type,payment_status):
            return False
        event=ReferralEvent.query.filter_by(referred_customer_id=customer_id, status="claimed").first()
        if not event:
            return False
        points=max(_int_env("LIVENZA_REFERRAL_POINTS",500,minimum=0),0)
        if points<=0:
            return False
        existing=LoyaltyLedgerEntry.query.filter_by(source_type="referral",source_id=event.id,effect_key="referral_booking_paid").first()
        if existing:
            event.status="rewarded";event.reward_points=int(existing.points or 0);return False
        account=_loyalty_account(event.referrer_customer_id)
        db.session.add(LoyaltyLedgerEntry(account_id=account.id,direction="credit",points=points,source_type="referral",source_id=event.id,effect_key="referral_booking_paid",description="Livenza referral reward"))
        event.status="rewarded";event.qualifying_source_type=source_type;event.qualifying_source_id=source_id;event.qualified_at=datetime.datetime.utcnow();event.rewarded_at=datetime.datetime.utcnow();event.reward_points=points
        return True

    def _allocate_tenant_due_payment(payment):
        if payment.source_type != "tenant_due":
            return False
        due = TenantDue.query.filter_by(id=payment.source_id, customer_id=payment.customer_id).first()
        if not due:
            return False
        existing = TenantDueAllocation.query.filter_by(due_id=due.id, payment_id=payment.id).first()
        if existing:
            return False
        allocated = _tenant_due_allocated_minor(due)
        remaining = outstanding_minor(due.amount_minor, allocated)
        amount = min(max(int(payment.amount_minor or 0), 0), remaining)
        if amount <= 0:
            return False
        db.session.add(TenantDueAllocation(due_id=due.id, payment_id=payment.id, amount_minor=amount))
        due.status = due_status(due.amount_minor, allocated + amount)
        return True

    def _confirm_meter_recharge_payment(payment):
        if payment.source_type != "meter_recharge":
            return False
        recharge = MeterRecharge.query.filter_by(id=payment.source_id, customer_id=payment.customer_id).first()
        if not recharge:
            return False
        if recharge.payment_id and recharge.payment_id != payment.id:
            return False
        if recharge.status in {"recharged", "refund_followup", "cancelled"}:
            return False
        meter = TenantMeterAccount.query.filter_by(id=recharge.meter_account_id, customer_id=payment.customer_id).first()
        if not meter:
            recharge.status = "review_required"
            recharge.failure_code = "meter_mapping_missing"
            recharge.failure_message = "Assigned meter mapping is unavailable."
            return True
        recharge.payment_id = payment.id
        recharge.status = "radius_processing"
        recharge.failure_code = ""
        recharge.failure_message = ""
        radius = RadiusAdapter.from_env()
        try:
            result = radius.credit_recharge(
                meter.provider_account_id, meter.provider_meter_id, recharge.amount_minor,
                recharge.currency or "INR", recharge.idempotency_key,
            )
            provider_status = str(result.get("status") or "").strip().lower()
            recharge.provider_reference = str(result.get("provider_reference") or "")[:180]
            recharge.provider_status_json = json.dumps(result.get("raw") if isinstance(result.get("raw"), dict) else result)
            if provider_status in {"credited", "recharged", "success", "successful", "completed"}:
                recharge.status = "recharged"
                recharge.credited_at = datetime.datetime.utcnow()
            else:
                recharge.status = "review_required"
                recharge.failure_code = "radius_credit_unconfirmed"
                recharge.failure_message = "Payment received, but the meter provider has not confirmed credit yet."
            return True
        except Exception as exc:
            recharge.status = "review_required"
            recharge.failure_code = "radius_credit_failed"
            recharge.failure_message = str(exc)[:500] or "Radius meter credit failed."
            return True

    def _confirm_payment_source(payment):
        if payment.source_type == "booking":
            changed = _confirm_booking_payment(payment)
            if changed:
                _award_loyalty_points(payment.customer_id, "booking", payment.source_id, "stay_booking_paid", payment.amount_minor, "Livenza stay payment")
                _qualify_referral(payment.customer_id,"booking",payment.source_id,"paid")
            return changed
        if payment.source_type == "store_order":
            changed = _confirm_store_order_payment(payment)
            if changed:
                _award_loyalty_points(payment.customer_id, "store_order", payment.source_id, "store_order_paid", payment.amount_minor, "Livenza.store purchase")
            return changed
        if payment.source_type == "tenant_due":
            return _allocate_tenant_due_payment(payment)
        if payment.source_type == "meter_recharge":
            return _confirm_meter_recharge_payment(payment)
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
        if payment.source_type == "tenant_due":
            return False
        if payment.source_type == "meter_recharge":
            recharge = MeterRecharge.query.filter_by(id=payment.source_id, customer_id=payment.customer_id).first()
            if recharge and recharge.status == "payment_pending":
                recharge.status = "cancelled"
                return True
            return False
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
        _extend_payment_hold(hold, now)
        existing = PaymentRecord.query.filter_by(
            customer_id=customer.id, source_type="booking", source_id=booking.id, gateway="cashfree"
        ).filter(PaymentRecord.status.in_(["created", "pending"])).order_by(PaymentRecord.id.desc()).first()
        gateway = CashfreeGateway.from_env()
        if existing and existing.gateway_order_id and _cashfree_checkout(existing).get("payment_session_id"):
            db.session.commit()
            return jsonify(ok=True, payment=_serialize_payment(existing), checkout=_cashfree_checkout(existing))
        payment_public_id=str(uuid.uuid4())
        context=_cashfree_order_context(payment_public_id,customer,{"source_type":"booking","booking_id":booking.public_id,"customer_id":customer.public_id})
        try:
            order = gateway.create_order(booking.amount_due_now_minor,"INR",context["order_id"],context["customer"],context["notes"],context["return_url"],context["notify_url"])
        except Exception:
            return error("Payment provider is unavailable.", 503, "payment_provider_unavailable")
        metadata={"payment_session_id":str(order.get("payment_session_id") or ""),"cf_order_id":str(order.get("cf_order_id") or ""),"cashfree_mode":gateway.environment}
        payment = PaymentRecord(
            public_id=payment_public_id, customer_id=customer.id, source_type="booking", source_id=booking.id,
            gateway="cashfree", gateway_order_id=str(order.get("order_id") or context["order_id"]), amount_minor=booking.amount_due_now_minor,
            currency=str(order.get("order_currency") or "INR"), status="created", metadata_json=json.dumps(metadata,separators=(",",":")),
        )
        if booking.status == "held":
            booking.status = "pending_payment"
        db.session.add(payment)
        db.session.commit()
        return jsonify(ok=True, payment=_serialize_payment(payment), checkout=_cashfree_checkout(payment)), 201

    @api.get("/payments/<public_id>")
    def get_payment(public_id):
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        payment = PaymentRecord.query.filter_by(public_id=public_id, customer_id=customer.id).first()
        if not payment:
            return error("Payment not found.", 404, "payment_not_found")
        return jsonify(ok=True, payment=_serialize_payment(payment))

    @api.post("/payments/webhooks/cashfree")
    def cashfree_webhook():
        raw_body = request.get_data(cache=False, as_text=False)
        signature = request.headers.get("x-webhook-signature", "")
        timestamp = request.headers.get("x-webhook-timestamp", "")
        gateway = CashfreeGateway.from_env()
        if not verify_cashfree_webhook(raw_body, signature, timestamp, gateway.client_secret):
            return error("Invalid webhook signature.", 400, "invalid_webhook_signature")
        try:
            payload=json.loads(raw_body.decode("utf-8"))
        except Exception:
            return error("Invalid webhook body.",400,"invalid_webhook_body")
        event_type=str(payload.get("type") or "")
        next_state=cashfree_payment_event_state(event_type)
        data=payload.get("data") if isinstance(payload.get("data"),dict) else {}
        order_entity=data.get("order") if isinstance(data.get("order"),dict) else {}
        payment_entity=data.get("payment") if isinstance(data.get("payment"),dict) else {}
        gateway_order_id=str(order_entity.get("order_id") or "")
        gateway_payment_id=str(payment_entity.get("cf_payment_id") or "")
        header_event=(request.headers.get("x-idempotency-key") or "").strip()
        if header_event:
            event_id=f"cashfree:{header_event}"
        else:
            event_id="cashfree:"+hashlib.sha256((event_type+"|"+gateway_order_id+"|"+gateway_payment_id+"|"+str(payload.get("event_time") or "")).encode("utf-8")).hexdigest()
        if ProcessedWebhookEvent.query.filter_by(gateway="cashfree", external_event_id=event_id).first():
            return jsonify(ok=True, duplicate=True)
        payment=PaymentRecord.query.filter_by(gateway="cashfree",gateway_order_id=gateway_order_id).first() if gateway_order_id else None
        processed=ProcessedWebhookEvent(gateway="cashfree",external_event_id=event_id,event_type=event_type,processed_at=datetime.datetime.utcnow())
        db.session.add(processed)
        if not payment:
            try: db.session.commit()
            except Exception:
                db.session.rollback(); return jsonify(ok=True,duplicate=True)
            return jsonify(ok=True,ignored=True),202
        if gateway_payment_id:
            payment.gateway_payment_id=gateway_payment_id
        if next_state == "paid":
            try:
                if gateway.test_stub:
                    gateway.mark_test_order_paid(gateway_order_id)
                verified_order=gateway.fetch_order(gateway_order_id)
                order_status=str(verified_order.get("order_status") or "").upper()
                verified_minor=int(round(float(verified_order.get("order_amount") or 0)*100))
            except Exception:
                db.session.rollback()
                return error("Cashfree payment could not be verified yet.",409,"payment_verification_pending")
            if order_status != "PAID" or verified_minor != int(payment.amount_minor or 0):
                db.session.rollback()
                return error("Cashfree payment verification did not match this Livenza payment.",409,"payment_verification_mismatch")
            payment.status="paid"
            _confirm_payment_source(payment)
        elif next_state == "failed":
            if payment.status != "paid":
                payment.status="failed"
                _release_payment_source(payment)
        elif payment.status not in {"paid","failed"}:
            payment.status="pending"
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            if ProcessedWebhookEvent.query.filter_by(gateway="cashfree",external_event_id=event_id).first():
                return jsonify(ok=True,duplicate=True)
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
        return jsonify(ok=True,status=payment.status)

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
        _extend_payment_hold(hold, now)
        existing = PaymentRecord.query.filter_by(
            customer_id=booking.customer_id, source_type="booking", source_id=booking.id, gateway="cashfree"
        ).filter(PaymentRecord.status.in_(["created", "pending"])).order_by(PaymentRecord.id.desc()).first()
        gateway = CashfreeGateway.from_env()
        if existing and existing.gateway_order_id and _cashfree_checkout(existing).get("payment_session_id"):
            db.session.commit()
            return jsonify(ok=True, payment=_serialize_payment(existing), checkout=_cashfree_checkout(existing))
        payment_public_id=str(uuid.uuid4())
        context=_cashfree_order_context(payment_public_id,payer_customer,{"source_type":"booking","booking_id":booking.public_id,"payer_customer_public_id":payer_customer.public_id,"payment_context":"parent_share"})
        try:
            order = gateway.create_order(booking.amount_due_now_minor,"INR",context["order_id"],context["customer"],context["notes"],context["return_url"],context["notify_url"])
        except Exception:
            return error("Payment provider is unavailable.", 503, "payment_provider_unavailable")
        metadata = {
            "payer_customer_public_id": payer_customer.public_id,
            "payer_mobile": payer_customer.primary_mobile or "",
            "payment_context": "parent_share",
            "payment_session_id":str(order.get("payment_session_id") or ""),
            "cf_order_id":str(order.get("cf_order_id") or ""),
            "cashfree_mode":gateway.environment,
        }
        payment = PaymentRecord(
            public_id=payment_public_id, customer_id=booking.customer_id, source_type="booking", source_id=booking.id,
            gateway="cashfree", gateway_order_id=str(order.get("order_id") or context["order_id"]), amount_minor=booking.amount_due_now_minor,
            currency=str(order.get("order_currency") or "INR"), status="created", metadata_json=json.dumps(metadata, separators=(",", ":")),
        )
        if booking.status == "held":
            booking.status = "pending_payment"
        db.session.add(payment)
        db.session.commit()
        return jsonify(ok=True, payment=_serialize_payment(payment), checkout=_cashfree_checkout(payment)), 201

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

    @api.post("/me/referrals/claim")
    def claim_referral():
        _session_row, customer=session_for_request()
        if not customer:
            return error("Authentication required.",401,"authentication_required")
        payload=request.get_json(silent=True) or {};code=normalize_referral_code(payload.get("code"))
        if not code:
            return error("Enter a valid referral code.",400,"invalid_referral_code")
        identity=ReferralIdentity.query.filter_by(code=code,status="active").first()
        if not identity:
            return error("Referral code was not found.",404,"referral_not_found")
        if identity.customer_id==customer.id:
            return error("You cannot claim your own referral code.",400,"self_referral_not_allowed")
        existing=ReferralEvent.query.filter_by(referred_customer_id=customer.id).first()
        if existing:
            if existing.referral_identity_id==identity.id:
                return jsonify(ok=True,status=existing.status)
            return error("A referral has already been linked to this account.",409,"referral_already_claimed")
        row=ReferralEvent(public_id=str(uuid.uuid4()),referral_identity_id=identity.id,referrer_customer_id=identity.customer_id,referred_customer_id=customer.id,status="claimed",effect_key=f"referral_claim:{customer.id}")
        db.session.add(row);db.session.commit()
        return jsonify(ok=True,status=row.status),201

    @api.get("/me/rewards")
    def my_rewards():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        account = LoyaltyAccount.query.filter_by(customer_id=customer.id).first()
        if not account:
            account = _loyalty_account(customer.id)
        identity=_referral_identity(customer.id)
        db.session.commit()
        entries = LoyaltyLedgerEntry.query.filter_by(account_id=account.id).order_by(LoyaltyLedgerEntry.id.desc()).all()
        current_balance = balance([(row.direction, row.points) for row in entries])
        referral_rows=ReferralEvent.query.filter_by(referrer_customer_id=customer.id).order_by(ReferralEvent.created_at.desc()).all()
        booking,property_row,onboarding,_capabilities,_policy=_resident_context(customer)
        tenancy_type=str(getattr(onboarding,"tenancy_type","") or "")
        now=datetime.datetime.utcnow();offer_rows=ResidentOffer.query.filter_by(status="published").order_by(ResidentOffer.id.desc()).all();offers=[]
        for row in offer_rows:
            if row.starts_at and row.starts_at>now: continue
            if row.ends_at and row.ends_at<=now: continue
            if row.property_id and (not property_row or row.property_id!=property_row.id): continue
            try: audience=json.loads(row.audience_tenancy_json or "[]")
            except Exception: audience=[]
            if isinstance(audience,list) and audience and tenancy_type not in {str(v) for v in audience}: continue
            offers.append({"id":row.public_id,"code":row.code,"title":row.title,"description":row.description or "","scope":row.scope,"discount_type":row.discount_type,"discount_value":int(row.discount_value or 0),"ends_at":row.ends_at.isoformat() if row.ends_at else None})
        property_room_delivery=bool(_eligible_property_room_delivery(customer.id))
        return jsonify(ok=True, rewards={
            "status": account.status or "active",
            "balance": current_balance,
            "referral_code": identity.code,
            "referrals": [{"id":row.public_id,"status":row.status,"reward_points":int(row.reward_points or 0),"created_at":row.created_at.isoformat() if row.created_at else None} for row in referral_rows],
            "offers":offers,
            "property_room_delivery":property_room_delivery,
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


    def _serialize_customer_agreement(row):
        if not row:
            return None
        return {
            "id": row.public_id,
            "status": row.status or "generated",
            "agreement_sha256": row.agreement_sha256 or "",
            "pdf_available": bool(getattr(row, "pdf_storage_key", "")),
            "accepted_at": row.accepted_at.isoformat() if row.accepted_at else None,
            "acceptance_method": row.acceptance_method or "",
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    def _latest_customer_agreement(customer):
        return CustomerAgreement.query.filter_by(customer_id=customer.id).filter(
            CustomerAgreement.status.notin_(["cancelled", "superseded"])
        ).order_by(CustomerAgreement.created_at.desc(), CustomerAgreement.id.desc()).first()

    @api.get("/me/agreement")
    def my_agreement():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        agreement = _latest_customer_agreement(customer)
        if not agreement:
            return jsonify(ok=True, agreement=None)
        return jsonify(ok=True, agreement=_serialize_customer_agreement(agreement))

    @api.get("/me/agreement/pdf")
    def my_agreement_pdf():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        agreement = CustomerAgreement.query.filter_by(customer_id=customer.id).filter(
            CustomerAgreement.status.notin_(["cancelled", "superseded"])
        ).order_by(CustomerAgreement.created_at.desc(), CustomerAgreement.id.desc()).first()
        if not agreement or not getattr(agreement, "pdf_storage_key", ""):
            return error("Agreement PDF is not available yet.", 404, "agreement_not_available")
        try:
            signed_url = storage.signed_get_url(agreement.pdf_storage_key, expires_seconds=300)
        except Exception:
            return error("Agreement storage is temporarily unavailable.", 503, "storage_unavailable")
        return jsonify(ok=True, url=signed_url, expires_in_seconds=300, agreement_sha256=agreement.agreement_sha256)

    @api.post("/me/agreement/accept")
    def accept_my_agreement():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        agreement = _latest_customer_agreement(customer)
        if not agreement:
            return error("Agreement is not available yet.", 404, "agreement_not_available")
        payload = request.get_json(silent=True) or {}
        agreement_sha256 = str(payload.get("agreement_sha256") or "").strip().lower()
        if not agreement_sha256 or not hmac.compare_digest(agreement_sha256, agreement.agreement_sha256 or ""):
            return error("The agreement changed. Review the latest PDF before accepting it.", 409, "stale_agreement")
        if agreement.status == "accepted" and agreement.accepted_at:
            return jsonify(ok=True, agreement=_serialize_customer_agreement(agreement))
        accepted_at = datetime.datetime.utcnow()
        secret = str(os.getenv("LIVENZA_AGREEMENT_ACCEPTANCE_SECRET") or app.config.get("SECRET_KEY") or "").encode("utf-8")
        fingerprint_material = "|".join([
            customer.public_id or str(customer.id),
            agreement.public_id or str(agreement.id),
            agreement.agreement_sha256 or "",
            accepted_at.isoformat(),
            str(request.remote_addr or ""),
            str(request.headers.get("User-Agent") or "")[:300],
        ]).encode("utf-8")
        acceptance_fingerprint = hmac.new(secret, fingerprint_material, hashlib.sha256).hexdigest()
        agreement.status = "accepted"
        agreement.accepted_at = accepted_at
        agreement.acceptance_method = "web_acceptance"
        agreement.acceptance_fingerprint = acceptance_fingerprint
        onboarding = TenantOnboarding.query.get(agreement.onboarding_id)
        if onboarding and onboarding.customer_id == customer.id:
            onboarding.current_step = "complete"
            onboarding.status = "complete"
            onboarding.completed_at = accepted_at
        db.session.commit()
        try:
            notify("agreement_accepted", customer=customer, agreement=agreement)
        except Exception:
            pass
        return jsonify(ok=True, agreement=_serialize_customer_agreement(agreement))

    @api.get("/me/dues")
    def my_dues():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        rows = TenantDue.query.filter_by(customer_id=customer.id).order_by(
            TenantDue.due_date.asc(), TenantDue.created_at.asc(), TenantDue.id.asc()
        ).all()
        items = [_serialize_tenant_due(row) for row in rows]
        summary = {
            "outstanding_minor": sum(int(item["outstanding_minor"] or 0) for item in items),
            "open_count": sum(1 for item in items if item["status"] in {"open", "part_paid"} and int(item["outstanding_minor"] or 0) > 0),
            "currency": "INR",
        }
        return jsonify(ok=True, items=items, summary=summary)

    @api.post("/me/dues/<public_id>/payments")
    def create_tenant_due_payment(public_id):
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        due = TenantDue.query.filter_by(public_id=public_id, customer_id=customer.id).first()
        if not due:
            return error("Due not found.", 404, "due_not_found")
        if due.status in {"waived", "cancelled"}:
            return error("This due is not payable.", 409, "due_not_payable")
        allocated = _tenant_due_allocated_minor(due)
        remaining = outstanding_minor(due.amount_minor, allocated)
        if remaining <= 0:
            due.status = "paid"
            db.session.commit()
            return error("This due is already paid.", 409, "due_already_paid")
        existing = PaymentRecord.query.filter_by(
            customer_id=customer.id, source_type="tenant_due", source_id=due.id, gateway="cashfree"
        ).filter(PaymentRecord.status.in_(["created", "pending"])).order_by(PaymentRecord.id.desc()).first()
        if existing and existing.gateway_order_id and _cashfree_checkout(existing).get("payment_session_id"):
            return jsonify(ok=True, due=_serialize_tenant_due(due), payment=_serialize_payment(existing), checkout=_cashfree_checkout(existing))
        gateway = CashfreeGateway.from_env()
        payment_public_id = str(uuid.uuid4())
        context = _cashfree_order_context(payment_public_id, customer, {
            "source_type":"tenant_due", "tenant_due_id":due.public_id, "due_type":due.due_type, "customer_id":customer.public_id,
        })
        try:
            order = gateway.create_order(remaining, "INR", **context)
        except (ValueError, RuntimeError) as exc:
            return error(str(exc), 503, "payment_gateway_unavailable")
        metadata = {
            "payment_session_id":str(order.get("payment_session_id") or ""),
            "cf_order_id":str(order.get("cf_order_id") or ""),
            "cashfree_mode":gateway.environment,
            "tenant_due_public_id":due.public_id,
        }
        payment = PaymentRecord(
            public_id=payment_public_id, customer_id=customer.id, source_type="tenant_due", source_id=due.id,
            gateway="cashfree", gateway_order_id=str(order.get("order_id") or context["order_id"]),
            amount_minor=remaining, currency="INR", status="created", metadata_json=json.dumps(metadata),
        )
        db.session.add(payment)
        db.session.commit()
        return jsonify(ok=True, due=_serialize_tenant_due(due), payment=_serialize_payment(payment), checkout=_cashfree_checkout(payment)), 201

    def _serialize_meter_recharge(row):
        payment = PaymentRecord.query.get(row.payment_id) if row.payment_id else None
        return {
            "id": row.public_id,
            "meter_id": TenantMeterAccount.query.get(row.meter_account_id).public_id if TenantMeterAccount.query.get(row.meter_account_id) else None,
            "amount_minor": int(row.amount_minor or 0),
            "currency": row.currency or "INR",
            "status": row.status or "payment_pending",
            "payment_id": payment.public_id if payment else None,
            "provider_reference": row.provider_reference or "",
            "failure_code": row.failure_code or "",
            "message": "Payment received. Meter recharge needs review. Do not pay again." if row.status == "review_required" else "",
            "credited_at": row.credited_at.isoformat() if row.credited_at else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    def _serialize_meter_account(row, radius):
        prop = StayProperty.query.get(row.property_id)
        unit = StayInventoryUnit.query.get(row.inventory_unit_id) if row.inventory_unit_id else None
        try:
            snapshot = radius.get_snapshot(row.provider_account_id, row.provider_meter_id)
            snapshot = {key: snapshot.get(key) for key in ("available","balance_minor","currency","reading","reading_unit","status","source_breakdown")}
        except Exception:
            snapshot = {"available": False, "balance_minor": None, "currency": "INR", "reading": "", "reading_unit": "kWh", "status": "provider_unavailable", "source_breakdown": []}
        return {
            "id": row.public_id,
            "display_name": row.display_name or masked_meter_label(row.provider_meter_id),
            "status": row.status or "active",
            "property": {"slug": prop.slug, "name": prop.name, "city": prop.city, "area": prop.area or ""} if prop else None,
            "room": {"code": unit.code, "display_name": unit.display_name or unit.code} if unit else None,
            "snapshot": snapshot,
        }

    @api.get("/me/electricity")
    def my_electricity():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        radius = RadiusAdapter.from_env()
        meters = TenantMeterAccount.query.filter_by(customer_id=customer.id, status="active").order_by(TenantMeterAccount.created_at.asc(), TenantMeterAccount.id.asc()).all()
        recharges = MeterRecharge.query.filter_by(customer_id=customer.id).order_by(MeterRecharge.created_at.desc(), MeterRecharge.id.desc()).limit(100).all()
        return jsonify(ok=True, meters=[_serialize_meter_account(row, radius) for row in meters], recharges=[_serialize_meter_recharge(row) for row in recharges])

    @api.post("/me/electricity/meters/<meter_public_id>/recharges")
    def create_meter_recharge(meter_public_id):
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        meter = TenantMeterAccount.query.filter_by(public_id=meter_public_id, customer_id=customer.id, status="active").first()
        if not meter:
            return error("Meter not found.", 404, "meter_not_found")
        payload = request.get_json(silent=True) or {}
        try:
            amount = normalize_recharge_amount(payload.get("amount_minor"), minimum_minor=_int_env("METER_RECHARGE_MIN_MINOR", 1000), maximum_minor=_int_env("METER_RECHARGE_MAX_MINOR", 5000000))
        except (TypeError, ValueError) as exc:
            return error(str(exc), 400, "invalid_recharge_amount")
        existing = MeterRecharge.query.filter_by(customer_id=customer.id, meter_account_id=meter.id).filter(MeterRecharge.status.in_(["payment_pending","paid","radius_processing","review_required"])).order_by(MeterRecharge.id.desc()).all()
        if not recharge_can_start([row.status for row in existing]):
            current = existing[0]
            return error("A recharge is already in progress for this meter. Check its status before paying again.", 409, "recharge_in_progress")
        recharge = MeterRecharge(
            public_id=str(uuid.uuid4()), meter_account_id=meter.id, customer_id=customer.id,
            amount_minor=amount, currency="INR", status="payment_pending", idempotency_key=f"meter-recharge-{uuid.uuid4().hex}",
        )
        db.session.add(recharge); db.session.flush()
        gateway = CashfreeGateway.from_env()
        payment_public_id = str(uuid.uuid4())
        context = _cashfree_order_context(payment_public_id, customer, {
            "source_type":"meter_recharge", "meter_recharge_id":recharge.public_id, "customer_id":customer.public_id,
        })
        try:
            order = gateway.create_order(amount, "INR", **context)
        except (ValueError, RuntimeError) as exc:
            db.session.rollback()
            return error(str(exc), 503, "payment_gateway_unavailable")
        metadata = {
            "payment_session_id":str(order.get("payment_session_id") or ""), "cf_order_id":str(order.get("cf_order_id") or ""),
            "cashfree_mode":gateway.environment, "meter_recharge_public_id":recharge.public_id,
        }
        payment = PaymentRecord(
            public_id=payment_public_id, customer_id=customer.id, source_type="meter_recharge", source_id=recharge.id,
            gateway="cashfree", gateway_order_id=str(order.get("order_id") or context["order_id"]), amount_minor=amount,
            currency="INR", status="created", metadata_json=json.dumps(metadata),
        )
        db.session.add(payment); db.session.flush(); recharge.payment_id=payment.id
        db.session.commit()
        return jsonify(ok=True, recharge=_serialize_meter_recharge(recharge), payment=_serialize_payment(payment), checkout=_cashfree_checkout(payment)), 201

    @api.get("/me/payments")
    def my_payments():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        rows = PaymentRecord.query.filter_by(customer_id=customer.id).order_by(PaymentRecord.created_at.desc()).all()
        return jsonify(items=[_serialize_payment(row) for row in rows])

    @api.get("/me/resident-services")
    def my_resident_services():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        booking, property_row, onboarding, capabilities, _policy = _resident_context(customer)
        return jsonify(ok=True, property=(
            {"id": property_row.id, "slug": property_row.slug, "name": property_row.name, "city": property_row.city, "area": property_row.area or ""}
            if property_row else None
        ), booking_id=booking.public_id if booking else None, tenancy_type=(onboarding.tenancy_type if onboarding else None), capabilities=list(capabilities))

    @api.get("/me/notices")
    def my_notices():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        _booking, property_row, onboarding, capabilities, _policy = _resident_context(customer)
        if not property_row or not capability_enabled(capabilities, "notices"):
            return jsonify(items=[])
        now = datetime.datetime.utcnow()
        tenancy_type = str(getattr(onboarding, "tenancy_type", "") or "")
        rows = ResidentNotice.query.filter_by(property_id=property_row.id, status="published").order_by(ResidentNotice.publish_at.desc(), ResidentNotice.id.desc()).all()
        items=[]
        for row in rows:
            if row.customer_id and row.customer_id != customer.id:
                continue
            if row.publish_at and row.publish_at > now:
                continue
            if row.expires_at and row.expires_at <= now:
                continue
            try:
                audience=json.loads(row.audience_tenancy_json or "[]")
            except Exception:
                audience=[]
            if isinstance(audience,list) and audience and tenancy_type not in {str(v) for v in audience}:
                continue
            items.append({"id":row.public_id,"title":row.title,"body":row.body,"publish_at":row.publish_at.isoformat() if row.publish_at else None,"expires_at":row.expires_at.isoformat() if row.expires_at else None})
        return jsonify(items=items)

    @api.get("/me/leave-requests")
    def my_leave_requests():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        rows=ResidentLeaveRequest.query.filter_by(customer_id=customer.id).order_by(ResidentLeaveRequest.created_at.desc()).all()
        return jsonify(items=[{"id":row.public_id,"request_type":row.request_type,"start_at":row.start_at.isoformat() if row.start_at else None,"end_at":row.end_at.isoformat() if row.end_at else None,"reason":row.reason,"status":row.status,"staff_note":row.staff_note or "","created_at":row.created_at.isoformat() if row.created_at else None} for row in rows])

    @api.post("/me/leave-requests")
    def create_leave_request():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        booking, property_row, _onboarding, capabilities, _policy = _resident_context(customer)
        if not booking or not property_row:
            return error("An active Livenza stay is required.", 409, "active_stay_required")
        payload=request.get_json(silent=True) or {}
        request_type=str(payload.get("request_type") or "leave").strip().lower()
        if request_type not in {"leave", "late_entry"}:
            return error("Unsupported resident request type.",400,"invalid_request_type")
        required_capability="late_entry" if request_type=="late_entry" else "leave"
        if not capability_enabled(capabilities, required_capability):
            return error("This resident service is not enabled for your property.",403,"invalid_resident_capability")
        try:
            start_at=_parse_client_datetime(payload.get("start_at"))
            end_at=_parse_client_datetime(payload.get("end_at")) if payload.get("end_at") else None
        except ValueError as exc:
            return error(str(exc),400,"invalid_datetime")
        if end_at and end_at < start_at:
            return error("End time cannot be before start time.",400,"invalid_datetime_range")
        reason=str(payload.get("reason") or "").strip()[:500]
        row=ResidentLeaveRequest(public_id=str(uuid.uuid4()),customer_id=customer.id,booking_id=booking.id,property_id=property_row.id,request_type=request_type,start_at=start_at,end_at=end_at,reason=reason,status="submitted")
        db.session.add(row);db.session.commit()
        try: notify("resident.request.submitted",customer,{"request_id":row.public_id,"request_type":request_type},["email","whatsapp"])
        except Exception: pass
        return jsonify(ok=True,request={"id":row.public_id,"request_type":row.request_type,"status":row.status}),201

    @api.get("/me/guest-requests")
    def my_guest_requests():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        rows=ResidentGuestRequest.query.filter_by(customer_id=customer.id).order_by(ResidentGuestRequest.created_at.desc()).all()
        return jsonify(items=[{"id":row.public_id,"guest_name":row.guest_name,"guest_mobile":row.guest_mobile,"visit_at":row.visit_at.isoformat() if row.visit_at else None,"purpose":row.purpose,"status":row.status,"staff_note":row.staff_note or "","created_at":row.created_at.isoformat() if row.created_at else None} for row in rows])

    @api.post("/me/guest-requests")
    def create_guest_request():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        booking, property_row, _onboarding, capabilities, _policy = _resident_context(customer)
        if not booking or not property_row:
            return error("An active Livenza stay is required.",409,"active_stay_required")
        if not capability_enabled(capabilities, "guest"):
            return error("This resident service is not enabled for your property.",403,"invalid_resident_capability")
        payload=request.get_json(silent=True) or {}
        guest_name=str(payload.get("guest_name") or "").strip()[:180]
        if not guest_name:
            return error("Guest name is required.",400,"guest_name_required")
        try: visit_at=_parse_client_datetime(payload.get("visit_at"))
        except ValueError as exc: return error(str(exc),400,"invalid_datetime")
        row=ResidentGuestRequest(public_id=str(uuid.uuid4()),customer_id=customer.id,booking_id=booking.id,property_id=property_row.id,guest_name=guest_name,guest_mobile=str(payload.get("guest_mobile") or "").strip()[:40],visit_at=visit_at,purpose=str(payload.get("purpose") or "").strip()[:500],status="submitted")
        db.session.add(row);db.session.commit()
        try: notify("resident.guest.submitted",customer,{"request_id":row.public_id},["email","whatsapp"])
        except Exception: pass
        return jsonify(ok=True,request={"id":row.public_id,"guest_name":row.guest_name,"status":row.status}),201

    @api.get("/me/menu")
    def my_menu():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        _booking, property_row, _onboarding, capabilities, _policy = _resident_context(customer)
        if not property_row or not capability_enabled(capabilities,"food"):
            return jsonify(items=[])
        now=datetime.datetime.utcnow();today=now.date();cutoff=today+datetime.timedelta(days=7)
        rows=PropertyMenu.query.filter_by(property_id=property_row.id,status="published").filter(PropertyMenu.service_date>=today,PropertyMenu.service_date<=cutoff).order_by(PropertyMenu.service_date,PropertyMenu.meal_type,PropertyMenu.id).all()
        items=[]
        for row in rows:
            if row.publish_at and row.publish_at>now: continue
            if row.expires_at and row.expires_at<=now: continue
            try: menu_items=json.loads(row.items_json or "[]")
            except Exception: menu_items=[]
            if not isinstance(menu_items,list): menu_items=[]
            items.append({"id":row.public_id,"service_date":row.service_date.isoformat(),"meal_type":row.meal_type,"title":row.title,"items":[str(v) for v in menu_items]})
        return jsonify(items=items)

    @api.get("/me/documents")
    def my_documents():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        rows = CustomerDocument.query.filter_by(customer_id=customer.id).order_by(CustomerDocument.created_at.desc()).all()
        return jsonify(items=[{
            "id": row.public_id or row.id, "booking_id": row.booking_id, "document_type": row.document_type,
            "display_name": row.display_name, "private": bool(row.private),
            "verification_status": getattr(row, "verification_status", "submitted") or "submitted",
            "masked_identifier": getattr(row, "masked_identifier", "") or "",
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
            "description": row.description, "status": row.status, "priority": getattr(row,"priority","normal") or "normal",
            "staff_note": getattr(row,"staff_note","") or "",
            "created_at": row.created_at.isoformat() if row.created_at else None,
        } for row in rows])

    @api.post("/me/support")
    def create_support_ticket():
        _session_row, customer = session_for_request()
        if not customer:
            return error("Authentication required.", 401, "authentication_required")
        payload = request.get_json(silent=True) or {}
        category = str(payload.get("category") or "").strip().lower()
        allowed = {"stay", "maintenance", "service", "payment", "store", "account", "other"}
        if category not in allowed:
            return error("Unsupported support category.", 400, "invalid_support_category")
        subject = str(payload.get("subject") or "").strip()
        description = str(payload.get("description") or "").strip()
        if not subject or len(subject) > 180:
            return error("Subject must be 1 to 180 characters.", 400, "invalid_subject")
        if not description or len(description) > 5000:
            return error("Description must be 1 to 5000 characters.", 400, "invalid_description")
        booking, property_row, _onboarding, capabilities, _policy = _resident_context(customer)
        if category in {"maintenance","service"} and not capability_enabled(capabilities,"maintenance"):
            return error("Maintenance requests are not enabled for your property.",403,"invalid_resident_capability")
        priority=str(payload.get("priority") or "normal").strip().lower()
        if priority not in {"low","normal","urgent"}:
            return error("Unsupported priority.",400,"invalid_priority")
        row = SupportTicket(
            public_id=str(uuid.uuid4()), customer_id=customer.id, booking_id=booking.id if booking else None,
            property_id=property_row.id if property_row else None, category=category, priority=priority,
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
