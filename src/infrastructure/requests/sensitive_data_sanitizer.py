"""
Path: src/infrastructure/requests/sensitive_data_sanitizer.py
"""

import re
from typing import Any

SENSITIVE_KEYS = {
    "api_key",
    "webhook_verify_token",
    "phone_number_id",
    "business_account_id",
    "website_token",
    "hmac_token",
    "imap_password",
    "smtp_password",
    "imap_login",
    "smtp_login",
}
SENSITIVE_KEY_PARTS = ("password", "token", "secret", "api_key", "authorization")


def sanitize_payload(value: Any, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {k: sanitize_payload(v, key=k) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_payload(item, key=key) for item in value]
    if isinstance(value, str):
        normalized_key = key.lower() if isinstance(key, str) else ""
        if key in SENSITIVE_KEYS or any(part in normalized_key for part in SENSITIVE_KEY_PARTS):
            return _mask_secret(value)
        return _truncate_long_numeric_sequences(value)
    return value


def _truncate_text(value: str) -> str:
    if len(value) <= 10:
        return value
    return f"{value[:4]}...{value[-4:]}"


def _mask_secret(value: str) -> str:
    if not value:
        return value
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}...{value[-2:]}"


def _truncate_long_numeric_sequences(value: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        return _truncate_text(match.group(0))

    masked = re.sub(r"\d{8,}", _replace, value)
    return re.sub(
        r"(websiteToken:\s*['\"])([^'\"]+)(['\"])",
        lambda m: f"{m.group(1)}{_truncate_text(m.group(2))}{m.group(3)}",
        masked,
    )
