# Livenza.life V1 Platform Foundation & Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the shared customer identity, property/inventory domain, versioned public API, and safe migration foundations required by the Livenza.life consumer platform without breaking the existing Flask back-office.

**Architecture:** Keep existing operational models such as `User`, `City`, `Room`, and `Tenant` intact. Add new customer-facing models additively in `app.py`, place pure domain logic in focused root-level `livenza_*_core.py` modules consistent with the existing `agreement_core.py` / `integrations_core.py` pattern, and register versioned API routes through `livenza_api_v1.py` using explicit dependencies to avoid circular imports.

**Tech Stack:** Python 3, Flask, Flask-SQLAlchemy, PostgreSQL production, SQLite test compatibility where practical, pytest, existing Vault/Integrations Center conventions.

**Spec:** `docs/superpowers/specs/2026-08-27-livenza-life-platform-design.md`

## Global Constraints

- Existing staff `User` authentication and `can_access()` permissions remain operational.
- New customer identity must not reuse staff password records.
- Customer OTP values are never stored in plaintext.
- New schema changes are additive; no destructive rename/drop of legacy room/tenant tables in this plan.
- PostgreSQL is authoritative in production; tests may use SQLite for pure/model tests when behavior is equivalent.
- Consumer API responses never expose secrets, password hashes, OTP hashes, private KYC contents, or Vault values.
- API version prefix is `/api/v1`.

---

## File Structure

**Create:**
- `livenza_customer_core.py` — customer identity normalization, OTP hashing/verification, session-token helpers.
- `livenza_inventory_core.py` — hierarchy validation and pure availability-state helpers.
- `livenza_api_v1.py` — API blueprint registration with dependency injection.
- `migrations/livenza_v1_foundation.sql` — additive PostgreSQL migration for new foundation tables/indexes.
- `tests/test_livenza_customer_core.py`
- `tests/test_livenza_inventory_core.py`
- `tests/test_livenza_foundation_models.py`
- `tests/test_livenza_api_v1.py`
- `tests/test_livenza_foundation_regression.py`

**Modify:**
- `app.py:94-123` — preserve `User` and `City`; add customer models after `User` and new stay models after `City`/before legacy `Room`.
- `app.py:340-410` — preserve Vault/Integration models; no credential duplication.
- `app.py:1517-1540` — add `content`, `customers`, `stays_admin` module labels only if corresponding admin routes are introduced in later plans; do not expose empty Dock apps now.
- `app.py` application bootstrap near existing route/helper registration — register the new API after all model classes/helpers exist.
- `requirements.txt` — add only dependencies actually required by the implementation; prefer Python stdlib hashing/HMAC for OTP helpers.

---

### Task 1: Add customer-domain pure helpers

**Files:**
- Create: `livenza_customer_core.py`
- Test: `tests/test_livenza_customer_core.py`

**Interfaces:**
- Consumes: Python stdlib `hashlib`, `hmac`, `secrets`, `datetime`.
- Produces:
  - `normalize_mobile(value: str, default_country_code: str = "+91") -> str`
  - `normalize_email(value: str) -> str`
  - `hash_otp(identifier: str, otp: str, salt: str) -> str`
  - `verify_otp(identifier: str, otp: str, salt: str, expected_hash: str) -> bool`
  - `new_session_token() -> str`
  - `hash_session_token(token: str) -> str`

- [ ] **Step 1: Write failing normalization and hashing tests**

```python
from livenza_customer_core import (
    normalize_mobile, normalize_email, hash_otp, verify_otp,
    new_session_token, hash_session_token,
)


def test_indian_mobile_is_normalized_to_e164():
    assert normalize_mobile("98765 43210") == "+919876543210"
    assert normalize_mobile("+91-98765-43210") == "+919876543210"


def test_email_is_trimmed_and_lowercased():
    assert normalize_email(" Rishabh@Example.COM ") == "rishabh@example.com"


def test_otp_hash_is_identifier_bound_and_verifiable():
    digest = hash_otp("+919876543210", "482913", "salt-1")
    assert verify_otp("+919876543210", "482913", "salt-1", digest)
    assert not verify_otp("+919876543210", "482914", "salt-1", digest)
    assert not verify_otp("+919999999999", "482913", "salt-1", digest)


def test_session_token_is_random_and_only_hash_is_persisted():
    first = new_session_token()
    second = new_session_token()
    assert first != second
    assert len(first) >= 32
    assert hash_session_token(first) != first
```

- [ ] **Step 2: Run the tests and verify RED**

Run:
```bash
python -m pytest tests/test_livenza_customer_core.py -q
```
Expected: FAIL because `livenza_customer_core.py` does not exist.

- [ ] **Step 3: Implement the helpers**

```python
import hashlib
import hmac
import re
import secrets


def normalize_mobile(value: str, default_country_code: str = "+91") -> str:
    raw = (value or "").strip()
    has_plus = raw.startswith("+")
    digits = re.sub(r"\D", "", raw)
    if not digits:
        raise ValueError("mobile is required")
    if has_plus:
        normalized = "+" + digits
    elif len(digits) == 10:
        normalized = default_country_code + digits
    elif digits.startswith("91") and len(digits) == 12:
        normalized = "+" + digits
    else:
        raise ValueError("unsupported mobile format")
    if len(re.sub(r"\D", "", normalized)) < 10:
        raise ValueError("mobile is too short")
    return normalized


def normalize_email(value: str) -> str:
    email = (value or "").strip().lower()
    if not email or "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ValueError("valid email is required")
    return email


def hash_otp(identifier: str, otp: str, salt: str) -> str:
    message = f"{identifier}\0{otp}\0{salt}".encode("utf-8")
    return hashlib.sha256(message).hexdigest()


def verify_otp(identifier: str, otp: str, salt: str, expected_hash: str) -> bool:
    actual = hash_otp(identifier, otp, salt)
    return hmac.compare_digest(actual, expected_hash or "")


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()
```

- [ ] **Step 4: Run unit tests and verify GREEN**

Run:
```bash
python -m pytest tests/test_livenza_customer_core.py -q
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add livenza_customer_core.py tests/test_livenza_customer_core.py
git commit -m "feat: add customer identity core helpers"
```

---

### Task 2: Add additive customer identity models and migration

**Files:**
- Modify: `app.py:94-123`
- Create: `migrations/livenza_v1_foundation.sql`
- Create: `tests/test_livenza_foundation_models.py`

**Interfaces:**
- Consumes: existing `db`, existing staff `User` model.
- Produces SQLAlchemy models:
  - `Customer`
  - `CustomerIdentity`
  - `CustomerOtpChallenge`
  - `CustomerSession`
  - `CustomerAddress`

- [ ] **Step 1: Write failing model-contract tests**

```python
def test_customer_models_exist(app_module):
    for name in [
        "Customer", "CustomerIdentity", "CustomerOtpChallenge",
        "CustomerSession", "CustomerAddress",
    ]:
        assert hasattr(app_module, name)


def test_customer_identity_is_unique_per_provider_and_identifier(app_module):
    table = app_module.CustomerIdentity.__table__
    unique_names = {c.name for c in table.constraints if getattr(c, "name", None)}
    assert "uq_customer_identity_provider_identifier" in unique_names


def test_staff_user_table_is_unchanged(app_module):
    assert app_module.User.__tablename__ == "user"
    assert "password_hash" in app_module.User.__table__.columns
```

Use the repository's existing app-module fixture if present; otherwise define a fixture that imports `app.py` with `DATABASE_URL=sqlite:///:memory:` before import.

- [ ] **Step 2: Run model tests and verify RED**

Run:
```bash
python -m pytest tests/test_livenza_foundation_models.py -q
```
Expected: FAIL because the customer models do not exist.

- [ ] **Step 3: Add models in `app.py` and matching SQL migration**

Add after the existing `User` class:

```python
class Customer(db.Model):
    __tablename__ = "customer"
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(180), default="")
    primary_mobile = db.Column(db.String(40), default="", index=True)
    primary_email = db.Column(db.String(220), default="", index=True)
    status = db.Column(db.String(32), default="active", index=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class CustomerIdentity(db.Model):
    __tablename__ = "customer_identity"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False, index=True)
    provider = db.Column(db.String(32), nullable=False, index=True)
    identifier = db.Column(db.String(220), nullable=False, index=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint("provider", "identifier", name="uq_customer_identity_provider_identifier"),
    )


class CustomerOtpChallenge(db.Model):
    __tablename__ = "customer_otp_challenge"
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(220), nullable=False, index=True)
    purpose = db.Column(db.String(32), nullable=False, default="login")
    otp_hash = db.Column(db.String(64), nullable=False)
    salt = db.Column(db.String(64), nullable=False)
    attempts = db.Column(db.Integer, default=0)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    consumed_at = db.Column(db.DateTime, nullable=True)
    requested_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)


class CustomerSession(db.Model):
    __tablename__ = "customer_session"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False, index=True)
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class CustomerAddress(db.Model):
    __tablename__ = "customer_address"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False, index=True)
    label = db.Column(db.String(80), default="Home")
    recipient_name = db.Column(db.String(180), default="")
    mobile = db.Column(db.String(40), default="")
    line1 = db.Column(db.String(240), default="")
    line2 = db.Column(db.String(240), default="")
    city = db.Column(db.String(120), default="")
    state = db.Column(db.String(120), default="")
    postal_code = db.Column(db.String(20), default="")
    country = db.Column(db.String(80), default="India")
    active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
```

In `migrations/livenza_v1_foundation.sql`, create the same tables/indexes with `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS`. Do not alter `user`, `room`, or `tenant`.

- [ ] **Step 4: Run model tests and a migration parse check**

Run:
```bash
python -m pytest tests/test_livenza_foundation_models.py -q
python - <<'PY'
from pathlib import Path
sql = Path('migrations/livenza_v1_foundation.sql').read_text()
for required in ['customer', 'customer_identity', 'customer_otp_challenge', 'customer_session', 'customer_address']:
    assert required in sql
assert 'DROP TABLE' not in sql.upper()
assert 'DROP COLUMN' not in sql.upper()
print('migration contract ok')
PY
```
Expected: PASS and `migration contract ok`.

- [ ] **Step 5: Commit**

```bash
git add app.py migrations/livenza_v1_foundation.sql tests/test_livenza_foundation_models.py
git commit -m "feat: add unified customer identity schema"
```

---

### Task 3: Add property and hierarchical inventory models

**Files:**
- Modify: `app.py:118-242`
- Modify: `migrations/livenza_v1_foundation.sql`
- Create: `livenza_inventory_core.py`
- Create: `tests/test_livenza_inventory_core.py`
- Modify: `tests/test_livenza_foundation_models.py`

**Interfaces:**
- Produces models:
  - `StayProperty`
  - `StayRoomCategory`
  - `StayInventoryUnit`
- Produces helpers:
  - `validate_unit_type(unit_type: str) -> str`
  - `can_parent(parent_type: str | None, child_type: str) -> bool`
  - `availability_state(total_allocatable: int, unavailable: int) -> str`

- [ ] **Step 1: Write failing hierarchy tests**

```python
from livenza_inventory_core import validate_unit_type, can_parent, availability_state


def test_inventory_hierarchy_rules():
    assert can_parent(None, "building")
    assert can_parent("building", "floor")
    assert can_parent("floor", "room")
    assert can_parent("room", "bed")
    assert not can_parent("bed", "room")


def test_availability_state_is_derived_from_allocatable_count():
    assert availability_state(10, 10) == "sold_out"
    assert availability_state(10, 9) == "limited"
    assert availability_state(10, 3) == "available"
```

- [ ] **Step 2: Run tests and verify RED**

```bash
python -m pytest tests/test_livenza_inventory_core.py -q
```
Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement helpers and additive models**

`livenza_inventory_core.py`:

```python
UNIT_TYPES = ("building", "wing", "floor", "unit", "room", "bed")
ALLOWED_CHILDREN = {
    None: {"building", "wing", "floor", "unit", "room", "bed"},
    "building": {"wing", "floor", "unit", "room"},
    "wing": {"floor", "unit", "room"},
    "floor": {"unit", "room"},
    "unit": {"room", "bed"},
    "room": {"bed"},
    "bed": set(),
}


def validate_unit_type(unit_type: str) -> str:
    value = (unit_type or "").strip().lower()
    if value not in UNIT_TYPES:
        raise ValueError("unsupported inventory unit type")
    return value


def can_parent(parent_type, child_type: str) -> bool:
    child = validate_unit_type(child_type)
    parent = None if parent_type is None else validate_unit_type(parent_type)
    return child in ALLOWED_CHILDREN[parent]


def availability_state(total_allocatable: int, unavailable: int) -> str:
    total = max(int(total_allocatable), 0)
    blocked = min(max(int(unavailable), 0), total)
    free = total - blocked
    if free <= 0:
        return "sold_out"
    if total >= 4 and free <= max(1, total // 4):
        return "limited"
    return "available"
```

Add to `app.py`:

```python
class StayProperty(db.Model):
    __tablename__ = "stay_property"
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    name = db.Column(db.String(220), nullable=False, index=True)
    city = db.Column(db.String(120), nullable=False, index=True)
    area = db.Column(db.String(160), default="", index=True)
    stay_types_json = db.Column(db.Text, default='["student"]')
    summary = db.Column(db.Text, default="")
    active = db.Column(db.Boolean, default=True, index=True)
    public = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class StayRoomCategory(db.Model):
    __tablename__ = "stay_room_category"
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("stay_property.id"), nullable=False, index=True)
    slug = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(180), nullable=False)
    occupancy = db.Column(db.Integer, default=1)
    summary = db.Column(db.Text, default="")
    active = db.Column(db.Boolean, default=True, index=True)
    __table_args__ = (db.UniqueConstraint("property_id", "slug", name="uq_room_category_property_slug"),)


class StayInventoryUnit(db.Model):
    __tablename__ = "stay_inventory_unit"
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("stay_property.id"), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("stay_inventory_unit.id"), nullable=True, index=True)
    room_category_id = db.Column(db.Integer, db.ForeignKey("stay_room_category.id"), nullable=True, index=True)
    unit_type = db.Column(db.String(24), nullable=False, index=True)
    code = db.Column(db.String(80), nullable=False)
    display_name = db.Column(db.String(180), default="")
    allocatable = db.Column(db.Boolean, default=False, index=True)
    active = db.Column(db.Boolean, default=True, index=True)
    __table_args__ = (db.UniqueConstraint("property_id", "parent_id", "code", name="uq_inventory_unit_path_code"),)
```

Mirror tables/indexes in the migration file.

- [ ] **Step 4: Run inventory/model tests**

```bash
python -m pytest tests/test_livenza_inventory_core.py tests/test_livenza_foundation_models.py -q
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py livenza_inventory_core.py migrations/livenza_v1_foundation.sql tests/test_livenza_inventory_core.py tests/test_livenza_foundation_models.py
git commit -m "feat: add stay property and inventory foundation"
```

---

### Task 4: Implement OTP challenge and customer-session service in Flask

**Files:**
- Create: `livenza_api_v1.py`
- Modify: `app.py` bootstrap section
- Create: `tests/test_livenza_api_v1.py`

**Interfaces:**
- Consumes model map containing `Customer`, `CustomerIdentity`, `CustomerOtpChallenge`, `CustomerSession`.
- Produces routes:
  - `POST /api/v1/auth/otp/request`
  - `POST /api/v1/auth/otp/verify`
  - `POST /api/v1/auth/logout`
  - `GET /api/v1/me`
- Cookie name: `livenza_customer_session`.

- [ ] **Step 1: Write failing API tests for OTP, session, and rate behavior**

```python
def test_otp_request_does_not_return_code_in_normal_mode(client, monkeypatch):
    monkeypatch.delenv("CUSTOMER_AUTH_TEST_MODE", raising=False)
    res = client.post("/api/v1/auth/otp/request", json={"mobile": "9876543210"})
    assert res.status_code == 202
    body = res.get_json()
    assert body["ok"] is True
    assert "otp" not in body


def test_verify_creates_customer_and_session_cookie(client, monkeypatch):
    monkeypatch.setenv("CUSTOMER_AUTH_TEST_MODE", "1")
    req = client.post("/api/v1/auth/otp/request", json={"mobile": "9876543210"})
    otp = req.get_json()["test_otp"]
    verify = client.post("/api/v1/auth/otp/verify", json={"mobile": "9876543210", "otp": otp})
    assert verify.status_code == 200
    assert "livenza_customer_session=" in verify.headers.get("Set-Cookie", "")
    me = client.get("/api/v1/me")
    assert me.status_code == 200
    assert me.get_json()["customer"]["primary_mobile"] == "+919876543210"


def test_wrong_otp_is_rejected(client, monkeypatch):
    monkeypatch.setenv("CUSTOMER_AUTH_TEST_MODE", "1")
    client.post("/api/v1/auth/otp/request", json={"mobile": "9876543210"})
    res = client.post("/api/v1/auth/otp/verify", json={"mobile": "9876543210", "otp": "000000"})
    assert res.status_code == 401
```

- [ ] **Step 2: Run API tests and verify RED**

```bash
python -m pytest tests/test_livenza_api_v1.py -q
```
Expected: FAIL because API routes are not registered.

- [ ] **Step 3: Implement `register_api_v1()` and dependency injection**

Use a registration signature that does not import `app.py`:

```python
def register_api_v1(app, db, models, send_otp):
    from flask import Blueprint, jsonify, request, make_response
    api = Blueprint("livenza_api_v1", __name__, url_prefix="/api/v1")
    # route closures use db/models/send_otp passed from app.py
    app.register_blueprint(api)
    return api
```

OTP request behavior:
- normalize mobile;
- reject more than 5 requests for the identifier within 15 minutes;
- generate a 6-digit code with `secrets.randbelow(1_000_000)` formatted to 6 digits;
- create random salt with `secrets.token_hex(16)`;
- persist only `hash_otp(...)`;
- expiry = UTC now + 5 minutes;
- call `send_otp(identifier, otp)`;
- only include `test_otp` when `CUSTOMER_AUTH_TEST_MODE=1` **and** `FLASK_ENV`/deployment is not production.

Verify behavior:
- latest unconsumed, unexpired challenge;
- max 5 attempts;
- on success, create/find `CustomerIdentity(provider="mobile")` and `Customer`;
- mark challenge consumed;
- issue random session token, persist only SHA-256 hash;
- session expiry = 30 days;
- set `HttpOnly`, `Secure` when HTTPS is forced, `SameSite=Lax`, path `/`.

Register from `app.py` only after models exist:

```python
from livenza_api_v1 import register_api_v1

register_api_v1(app, db, {
    "Customer": Customer,
    "CustomerIdentity": CustomerIdentity,
    "CustomerOtpChallenge": CustomerOtpChallenge,
    "CustomerSession": CustomerSession,
    "StayProperty": StayProperty,
    "StayRoomCategory": StayRoomCategory,
    "StayInventoryUnit": StayInventoryUnit,
}, send_customer_otp)
```

Define `send_customer_otp(identifier, otp)` in `app.py` as a thin adapter that routes through the Integrations Center/notification implementation when configured and raises a controlled `RuntimeError("customer OTP delivery is not configured")` outside test mode if no provider exists.

- [ ] **Step 4: Run API tests plus staff-login regression**

```bash
python -m pytest tests/test_livenza_api_v1.py tests/test_livenza_foundation_regression.py -q
```
Expected: PASS. Regression must include at least one existing staff login/dashboard permission assertion.

- [ ] **Step 5: Commit**

```bash
git add app.py livenza_api_v1.py tests/test_livenza_api_v1.py tests/test_livenza_foundation_regression.py
git commit -m "feat: add passwordless customer auth API"
```

---

### Task 5: Add public city/property serializers and list/detail APIs

**Files:**
- Modify: `livenza_api_v1.py`
- Create: `tests/test_livenza_public_stays_api.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/cities`
  - `GET /api/v1/properties?city=&q=&stay_type=`
  - `GET /api/v1/properties/<slug>`
- Public property API returns only rows with `active=True` and `public=True`.

- [ ] **Step 1: Write failing list/detail visibility tests**

```python
def test_private_property_is_not_publicly_listed(client, seeded_properties):
    res = client.get("/api/v1/properties?city=Jaipur")
    names = [row["name"] for row in res.get_json()["items"]]
    assert "Public Jaipur Home" in names
    assert "Draft Jaipur Home" not in names


def test_property_detail_404s_for_nonpublic_slug(client, seeded_properties):
    res = client.get("/api/v1/properties/draft-jaipur-home")
    assert res.status_code == 404


def test_city_list_is_derived_from_public_properties(client, seeded_properties):
    res = client.get("/api/v1/cities")
    assert {row["name"] for row in res.get_json()["items"]} == {"Jaipur", "Gurugram"}
```

- [ ] **Step 2: Run and verify RED**

```bash
python -m pytest tests/test_livenza_public_stays_api.py -q
```
Expected: FAIL because routes are missing.

- [ ] **Step 3: Implement explicit public serializers and query filters**

Add pure local serializer functions inside `livenza_api_v1.py`:

```python
def serialize_property(row):
    return {
        "id": row.id,
        "slug": row.slug,
        "name": row.name,
        "city": row.city,
        "area": row.area,
        "summary": row.summary,
        "stay_types": row.stay_types,
    }
```

If `StayProperty` does not yet expose `stay_types`, add a safe property that parses `stay_types_json` into a list. Query only `active=True, public=True`. `q` should case-insensitively match `name`, `city`, `area`, and `summary` using SQLAlchemy `or_`/`ilike` on PostgreSQL-compatible expressions.

- [ ] **Step 4: Run API tests**

```bash
python -m pytest tests/test_livenza_public_stays_api.py -q
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py livenza_api_v1.py tests/test_livenza_public_stays_api.py
git commit -m "feat: expose public stays discovery API"
```

---

### Task 6: Add availability query contract without booking holds yet

**Files:**
- Modify: `livenza_api_v1.py`
- Modify: `livenza_inventory_core.py`
- Create: `tests/test_livenza_availability_api.py`

**Interfaces:**
- Produces `GET /api/v1/availability?property=<slug>&room_category=<slug>&start=YYYY-MM-DD&end=YYYY-MM-DD`.
- Returns `available_count`, `availability_state`, `room_category`, and `allocatable_unit_type`.
- In this plan, availability subtracts inactive inventory only; booking/hold subtraction is added in Plan 3.

- [ ] **Step 1: Write failing availability tests**

```python
def test_availability_counts_only_active_allocatable_units(client, seeded_inventory):
    res = client.get(
        "/api/v1/availability?property=oasis-test&room_category=deluxe-twin&start=2026-09-01&end=2026-09-30"
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["available_count"] == 3
    assert body["availability_state"] == "available"


def test_invalid_date_range_is_rejected(client, seeded_inventory):
    res = client.get(
        "/api/v1/availability?property=oasis-test&room_category=deluxe-twin&start=2026-09-30&end=2026-09-01"
    )
    assert res.status_code == 400
```

- [ ] **Step 2: Run and verify RED**

```bash
python -m pytest tests/test_livenza_availability_api.py -q
```
Expected: FAIL because route does not exist.

- [ ] **Step 3: Implement date validation and category-scoped counts**

Use `datetime.date.fromisoformat`. Require `end > start`. Query `StayProperty` by public slug, `StayRoomCategory` by property + slug, and count `StayInventoryUnit` rows where `room_category_id` matches, `allocatable=True`, `active=True`. Return the derived state from `availability_state(total_allocatable, unavailable=0)`.

- [ ] **Step 4: Run availability and public API tests**

```bash
python -m pytest tests/test_livenza_availability_api.py tests/test_livenza_public_stays_api.py -q
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add livenza_api_v1.py livenza_inventory_core.py tests/test_livenza_availability_api.py
git commit -m "feat: add stays availability contract"
```

---

### Task 7: Run foundation regression, migration safety, and API contract audit

**Files:**
- Create: `tests/test_livenza_foundation_regression.py`
- Create: `tests/test_livenza_api_contracts.py`
- Modify: `README.md`

**Interfaces:**
- Produces the stable contracts consumed by Plans 2–5.

- [ ] **Step 1: Add regression/contract tests**

Include assertions that:
- existing `User`, `Room`, `Tenant`, `IntegrationProvider`, `VaultSecret`, and `AuditEvent` models still import;
- `MODULES` still contains all pre-existing module keys;
- `can_access("agreements", user)` behavior still delegates to existing permissions;
- public APIs never return `otp_hash`, `token_hash`, `password_hash`, `ciphertext`, `nonce`, or `permissions_json`;
- migration contains no `DROP TABLE`, `DROP COLUMN`, or rename of legacy tables.

Example serializer leak test:

```python
SENSITIVE_KEYS = {"otp_hash", "token_hash", "password_hash", "ciphertext", "nonce"}


def walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            assert key not in SENSITIVE_KEYS
            walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)


def test_public_property_payload_has_no_sensitive_keys(client, seeded_properties):
    walk(client.get("/api/v1/properties").get_json())
```

- [ ] **Step 2: Run the complete foundation suite**

```bash
python -m pytest \
  tests/test_livenza_customer_core.py \
  tests/test_livenza_inventory_core.py \
  tests/test_livenza_foundation_models.py \
  tests/test_livenza_api_v1.py \
  tests/test_livenza_public_stays_api.py \
  tests/test_livenza_availability_api.py \
  tests/test_livenza_foundation_regression.py \
  tests/test_livenza_api_contracts.py -q
```
Expected: PASS.

- [ ] **Step 3: Compile and parse source**

```bash
python -m py_compile app.py livenza_customer_core.py livenza_inventory_core.py livenza_api_v1.py
```
Expected: no output and exit code 0.

- [ ] **Step 4: Document new environment variables and migration order**

Add a README section containing exactly these variables and meanings:

```text
CUSTOMER_AUTH_TEST_MODE=0        # 1 only in local/test; never production
CUSTOMER_SESSION_DAYS=30         # customer session lifetime
CUSTOMER_OTP_EXPIRY_MINUTES=5    # OTP validity
CUSTOMER_OTP_MAX_REQUESTS_15M=5  # identifier rate window
```

Document that `migrations/livenza_v1_foundation.sql` is applied to staging before any Plan 2 consumer traffic is connected.

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_livenza_foundation_regression.py tests/test_livenza_api_contracts.py
git commit -m "test: lock livenza platform foundation contracts"
```

## Plan 1 Completion Gate

Plan 1 is complete only when:
- all tests above pass;
- the existing back-office starts normally;
- staff login/permissions remain working;
- OTP test mode works only outside production;
- customer session cookie is HttpOnly and production-secure;
- public city/property/availability APIs return only public data;
- the additive migration has been applied and smoke-tested on staging PostgreSQL.
