from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable


CREATE_ACCOUNTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS accounts (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    locale VARCHAR(32),
    domain VARCHAR(255),
    support_email VARCHAR(255),
    status VARCHAR(64),
    created_at DATETIME,
    latest_chatwoot_version VARCHAR(64),
    subscribed_features_csv TEXT,
    cache_key_label VARCHAR(64),
    cache_key_inbox VARCHAR(64),
    cache_key_team VARCHAR(64),
    setting_auto_resolve_after BIGINT,
    setting_auto_resolve_message TEXT,
    setting_auto_resolve_ignore_waiting TINYINT(1),
    last_synced_at DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


class AccountsRepository:
    def __init__(self, connection) -> None:
        self.connection = connection

    def ensure_table(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(CREATE_ACCOUNTS_TABLE_SQL)

    def list_accounts(self) -> list[Dict[str, Any]]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    status,
                    locale,
                    domain,
                    support_email,
                    created_at,
                    latest_chatwoot_version
                FROM accounts
                ORDER BY id ASC
                """
            )
            return list(cursor.fetchall() or [])

    def upsert_account(self, payload: Dict[str, Any]) -> None:
        flattened, dynamic_columns = self._flatten_payload(payload)
        if dynamic_columns:
            self._ensure_columns(dynamic_columns)

        columns = list(flattened.keys())
        insert_cols = ", ".join(columns)
        placeholders = ", ".join([f"%({col})s" for col in columns])
        update_cols = ", ".join([f"{col}=VALUES({col})" for col in columns if col != "id"])
        sql = f"""
            INSERT INTO accounts ({insert_cols})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_cols}
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, flattened)

    def _ensure_columns(self, columns: Dict[str, str]) -> None:
        existing = self._get_existing_columns()
        with self.connection.cursor() as cursor:
            for column, col_type in columns.items():
                if column in existing:
                    continue
                cursor.execute(f"ALTER TABLE accounts ADD COLUMN {column} {col_type}")

    def _get_existing_columns(self) -> set[str]:
        with self.connection.cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM accounts")
            rows = cursor.fetchall() or []
            return {row["Field"] for row in rows}

    def _flatten_payload(self, payload: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, str]]:
        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        created_at = _parse_iso_datetime(payload.get("created_at"))
        flattened: Dict[str, Any] = {
            "id": payload.get("id"),
            "name": payload.get("name"),
            "locale": payload.get("locale"),
            "domain": payload.get("domain"),
            "support_email": payload.get("support_email"),
            "status": payload.get("status"),
            "created_at": created_at,
            "latest_chatwoot_version": payload.get("latest_chatwoot_version"),
            "subscribed_features_csv": _join_csv(payload.get("subscribed_features")),
            "cache_key_label": None,
            "cache_key_inbox": None,
            "cache_key_team": None,
            "setting_auto_resolve_after": None,
            "setting_auto_resolve_message": None,
            "setting_auto_resolve_ignore_waiting": None,
            "last_synced_at": now,
        }

        dynamic_columns: Dict[str, str] = {}

        cache_keys = payload.get("cache_keys") or {}
        if isinstance(cache_keys, dict):
            for key, value in cache_keys.items():
                col = f"cache_key_{_sanitize_key(key)}"
                flattened[col] = value
                dynamic_columns[col] = "VARCHAR(64)"

        settings = payload.get("settings") or {}
        if isinstance(settings, dict):
            for key, value in settings.items():
                col = f"setting_{_sanitize_key(key)}"
                flattened[col] = _normalize_scalar(value)
                dynamic_columns[col] = _infer_column_type(value)

        features = payload.get("features") or {}
        if isinstance(features, dict):
            for key, value in features.items():
                col = f"feature_{_sanitize_key(key)}"
                flattened[col] = _bool_to_int(value)
                dynamic_columns[col] = "TINYINT(1)"

        return flattened, dynamic_columns


def _sanitize_key(value: str) -> str:
    return re.sub(r"[^0-9a-zA-Z_]+", "_", str(value)).strip("_").lower()


def _bool_to_int(value: Any) -> int | None:
    if value is None:
        return None
    return 1 if bool(value) else 0


def _join_csv(values: Any) -> str | None:
    if not values:
        return None
    if isinstance(values, (list, tuple, set)):
        return ",".join(str(item) for item in values)
    return str(values)


def _normalize_scalar(value: Any) -> Any:
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float, str)) or value is None:
        return value
    return str(value)


def _infer_column_type(value: Any) -> str:
    if isinstance(value, bool):
        return "TINYINT(1)"
    if isinstance(value, int):
        return "BIGINT"
    if isinstance(value, float):
        return "DOUBLE"
    return "TEXT"


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    return None
