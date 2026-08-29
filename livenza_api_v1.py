"""Versioned consumer API for Livenza.life V1.

This module deliberately avoids importing app.py or Flask at module-import time.
The back-office injects db/models/provider adapters through register_api_v1().
"""
import datetime
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

    api = Blueprint("livenza_api_v1", __name__, url_prefix="/api/v1")

    def error(message, status=400, code="invalid_request"):
        return jsonify(ok=False, error=message, code=code), status

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
        body["room_categories"] = [
            {
                "slug": item.slug,
                "name": item.name,
                "occupancy": item.occupancy,
                "summary": item.summary or "",
            }
            for item in categories
        ]
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
        count = len(units)
        return jsonify(
            property=prop.slug,
            room_category=category.slug,
            start=start.isoformat(),
            end=end.isoformat(),
            available_count=count,
            availability_state=availability_state(count, 0),
            allocatable_unit_type=allocatable_unit_type,
        )

    app.register_blueprint(api)
    return api
