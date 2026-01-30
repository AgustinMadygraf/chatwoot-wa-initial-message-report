from __future__ import annotations

from datetime import datetime

from infrastructure.CLI import ui


def test_print_tables_and_screens() -> None:
    ui.print_accounts_table(
        [
            {
                "id": 1,
                "name": "A",
                "status": "active",
                "locale": "es",
                "domain": "x",
                "support_email": "x@y",
                "created_at": "2024-01-01T00:00:00Z",
                "latest_chatwoot_version": "1.0",
            }
        ]
    )
    ui.print_inboxes_table(
        [
            {
                "id": 1,
                "account_id": 1,
                "name": "Inbox",
                "channel_type": "WhatsApp",
                "address": "123",
                "last_synced_at": datetime.now(),
            }
        ]
    )
    ui.print_conversations_table(
        [
            {
                "id": 1,
                "inbox_id": 1,
                "status": "open",
                "meta__sender__id": 10,
                "meta__sender__name": "Ana",
                "created_at": 0,
                "last_activity_at": 0,
            }
        ]
    )
    ui.print_messages_table(
        [
            {
                "id": 1,
                "conversation_id": 1,
                "inbox_id": 1,
                "message_type": 0,
                "sender_type": "User",
                "sender__name": "Ana",
                "created_at": 0,
                "content": "Hola",
            }
        ]
    )
    ui.print_health_screen({"ok": True, "chatwoot": {"ok": True}, "mysql": {"ok": True}})
    ui.print_sync_screen({"accounts_upserted": 1}, started_at=datetime.now())
    ui.build_sync_progress_screen({"phase": "x"}, started_at=datetime.now())
