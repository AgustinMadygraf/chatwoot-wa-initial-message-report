"""
Path: tests/test_chatwoot_contacts_query.py
"""

import unittest
from typing import Any

from src.use_case.chatwoot_contacts_query import (
    fetch_all_contacts_paginated,
    find_contact_in_paginated_contacts,
)


class ChatwootContactsQueryTest(unittest.TestCase):
    def test_find_contact_in_first_page(self) -> None:
        pages = {
            1: {
                "payload": [{"id": 10, "name": "A"}, {"id": 11, "name": "B"}],
                "meta": {"count": 2},
            }
        }

        found = find_contact_in_paginated_contacts(
            fetch_page=lambda page: pages[page],
            contact_id=11,
            page_size=15,
        )

        self.assertIsNotNone(found)
        assert found is not None
        self.assertEqual(found.id, 11)
        self.assertEqual(found.raw["name"], "B")

    def test_find_contact_in_second_page(self) -> None:
        pages = {
            1: {"payload": [{"id": 1}], "meta": {"count": 16}},
            2: {"payload": [{"id": 25, "name": "Found"}], "meta": {"count": 16}},
        }

        found = find_contact_in_paginated_contacts(
            fetch_page=lambda page: pages[page],
            contact_id=25,
            page_size=15,
        )

        self.assertIsNotNone(found)
        assert found is not None
        self.assertEqual(found.id, 25)

    def test_find_contact_not_found(self) -> None:
        pages = {
            1: {"payload": [{"id": 1}], "meta": {"count": 16}},
            2: {"payload": [{"id": 2}], "meta": {"count": 16}},
        }

        found = find_contact_in_paginated_contacts(
            fetch_page=lambda page: pages[page],
            contact_id=999,
            page_size=15,
        )

        self.assertIsNone(found)

    def test_find_contact_invalid_payload_raises_value_error(self) -> None:
        def fetch_page(_page: int) -> dict[str, Any]:
            return {"payload": {"id": 1}, "meta": {"count": 1}}

        with self.assertRaises(ValueError):
            find_contact_in_paginated_contacts(
                fetch_page=fetch_page,
                contact_id=1,
                page_size=15,
            )

    def test_fetch_all_contacts_paginated(self) -> None:
        pages = {
            1: {"payload": [{"id": 1}], "meta": {"count": 31}},
            2: {"payload": [{"id": 2}], "meta": {"count": 31}},
            3: {"payload": [{"id": 3}], "meta": {"count": 31}},
        }

        contacts = fetch_all_contacts_paginated(
            fetch_page=lambda page: pages[page],
            page_size=15,
        )

        self.assertEqual([item["id"] for item in contacts], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
