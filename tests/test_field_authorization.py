import unittest

from backend.app import user_can_reference_field


class FakeCursor:
    def __init__(self, row):
        self.row = row

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, _query, _params):
        return None

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, row):
        self.row = row

    def cursor(self):
        return FakeCursor(self.row)


class FieldAuthorizationTests(unittest.TestCase):
    def test_agronomist_requires_explicit_assignment(self):
        unassigned = FakeConnection(
            {"owner_user_id": 1, "linked_to_user": False, "assigned_to_agronomist": False}
        )
        assigned = FakeConnection(
            {"owner_user_id": 1, "linked_to_user": False, "assigned_to_agronomist": True}
        )
        user = {"user_id": 3, "role": "Agronomist"}
        self.assertFalse(user_can_reference_field(unassigned, 1, user))
        self.assertTrue(user_can_reference_field(assigned, 1, user))

    def test_farmer_must_own_or_have_linked_image(self):
        denied = FakeConnection(
            {"owner_user_id": 7, "linked_to_user": False, "assigned_to_agronomist": False}
        )
        linked = FakeConnection(
            {"owner_user_id": 7, "linked_to_user": True, "assigned_to_agronomist": False}
        )
        user = {"user_id": 9, "role": "Farmer"}
        self.assertFalse(user_can_reference_field(denied, 1, user))
        self.assertTrue(user_can_reference_field(linked, 1, user))


if __name__ == "__main__":
    unittest.main()
