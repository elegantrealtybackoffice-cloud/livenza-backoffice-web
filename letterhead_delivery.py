"""Pure delivery-state helpers for Livenza Letterhead Studio."""
from __future__ import annotations

from dataclasses import dataclass

DELIVERY_STATES = {"pending", "sent", "failed"}


@dataclass(frozen=True)
class DeliveryResult:
    ok: bool
    state: str
    provider_name: str = ""
    provider_reference: str = ""
    error_code: str = ""


def normalize_delivery_result(channel: str, provider_result: dict | None) -> DeliveryResult:
    channel = str(channel or "").strip().lower()
    raw = provider_result if isinstance(provider_result, dict) else {}
    accepted = bool(raw.get("accepted"))
    state = "sent" if accepted else "failed"
    provider = str(raw.get("provider") or f"configured-{channel}" or "provider")[:80]
    reference = str(raw.get("reference") or "")[:240] if accepted else ""
    error = "" if accepted else str(raw.get("error_code") or "provider_failed")[:120]
    return DeliveryResult(accepted, state, provider, reference, error)


def can_retry_delivery(state: str) -> bool:
    return str(state or "").strip().lower() == "failed"
