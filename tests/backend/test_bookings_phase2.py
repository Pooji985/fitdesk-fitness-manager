import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import or_

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.core.config import settings
from app.core.security import create_access_token
from app.db.auth_store import init_auth_db
from app.db.base import init_db
from app.db.session import SessionLocal
from app.main import app
from app.models.booking import Booking
from app.models.fitness_class import FitnessClass
from app.models.user import User


class TestBookingsPhase2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings.JWT_SECRET_KEY = "phase-two-booking-test-secret-over-32-chars"
        init_db()
        init_auth_db()
        cls.client = TestClient(app)
        db = SessionLocal()
        try:
            cls.seed_booking_count = db.query(Booking).count()
        finally:
            db.close()
        cls.assertion_client_ready = True

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def setUp(self):
        self.suffix = uuid.uuid4().hex
        db = SessionLocal()
        try:
            self.member = User(
                name="Booking Test Member",
                email=f"booking-member-{self.suffix}@example.test",
                role="member",
                role_title="Member",
                membership_tier="Basic Tier",
                is_active=True,
            )
            self.other_member = User(
                name="Other Booking Member",
                email=f"other-booking-member-{self.suffix}@example.test",
                role="member",
                role_title="Member",
                membership_tier="Basic Tier",
                is_active=True,
            )
            self.admin = User(
                name="Booking Test Admin",
                email=f"booking-admin-{self.suffix}@example.test",
                role="admin",
                role_title="Admin",
                is_active=True,
            )
            db.add_all([self.member, self.other_member, self.admin])
            db.flush()
            self.member_id = self.member.id
            self.other_member_id = self.other_member.id
            self.admin_id = self.admin.id
            self.member_headers = self._headers(self.member_id)
            self.other_member_headers = self._headers(self.other_member_id)
            self.admin_headers = self._headers(self.admin_id)
            self.class_ids = []
            self.booking_ids = []
            self.default_class_id = self._create_class(db, "Default", capacity=5)
            db.commit()
        finally:
            db.close()

    def tearDown(self):
        db = SessionLocal()
        try:
            db.query(Booking).filter(
                or_(
                    Booking.user_id.in_([self.member_id, self.other_member_id, self.admin_id]),
                    Booking.class_id.in_(self.class_ids or [-1]),
                    Booking.id.in_(self.booking_ids or [-1]),
                )
            ).delete(synchronize_session=False)
            if self.class_ids:
                db.query(FitnessClass).filter(FitnessClass.id.in_(self.class_ids)).delete(synchronize_session=False)
            db.query(User).filter(User.id.in_([self.member_id, self.other_member_id, self.admin_id])).delete(
                synchronize_session=False
            )
            db.commit()
        finally:
            db.close()

    @classmethod
    def _headers(cls, user_id):
        return {"Authorization": f"Bearer {create_access_token(user_id)}"}

    def _create_class(self, db, title, capacity=5, starts_at=None, ends_at=None):
        starts_at = starts_at or datetime.now(timezone.utc) + timedelta(days=5)
        ends_at = ends_at or starts_at + timedelta(hours=1)
        fitness_class = FitnessClass(
            title=f"{title} {self.suffix}",
            description="Temporary booking test class",
            category="Strength",
            class_type="indoor",
            trainer_id=2,
            location_name="Test Studio",
            capacity=capacity,
            start_time=starts_at,
            end_time=ends_at,
            is_cancelled=False,
        )
        db.add(fitness_class)
        db.flush()
        self.class_ids.append(fitness_class.id)
        return fitness_class.id

    def _book(self, class_id=None, headers=None, query=""):
        response = self.client.post(
            f"/api/v1/bookings{query}",
            json={"class_id": class_id or self.default_class_id},
            headers=headers or self.member_headers,
        )
        if response.status_code == 201:
            self.booking_ids.append(response.json()["id"])
        return response

    def test_successful_booking_uses_authenticated_member_and_lists_only_own(self):
        response = self._book(query=f"?user_id={self.other_member_id}&role=admin")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["user_id"], self.member_id)
        self.assertEqual(data["class_id"], self.default_class_id)
        self.assertEqual(data["status"], "booked")
        self.assertEqual(data["fitness_class"]["title"].split()[0], "Default")

        listing = self.client.get(
            f"/api/v1/bookings?user_id={self.other_member_id}",
            headers=self.member_headers,
        )
        self.assertEqual(listing.status_code, 200)
        self.assertEqual([item["id"] for item in listing.json()], [data["id"]])
        self.assertEqual(listing.json()[0]["user_id"], self.member_id)

    def test_unauthenticated_booking_rejected(self):
        response = self.client.post("/api/v1/bookings", json={"class_id": self.default_class_id})
        self.assertEqual(response.status_code, 401)

    def test_only_member_can_create_normal_booking(self):
        response = self._book(headers=self.admin_headers)
        self.assertEqual(response.status_code, 403)

    def test_duplicate_booking_rejected(self):
        first = self._book()
        second = self._book()
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 409)

    def test_full_class_rejected(self):
        db = SessionLocal()
        try:
            class_id = self._create_class(db, "Capacity One", capacity=1)
            db.commit()
        finally:
            db.close()

        first = self._book(class_id, self.other_member_headers)
        second = self._book(class_id, self.member_headers)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 409)

    def test_booking_after_class_start_rejected(self):
        db = SessionLocal()
        try:
            start = datetime.now(timezone.utc) - timedelta(minutes=30)
            class_id = self._create_class(db, "Already Started", starts_at=start, ends_at=start + timedelta(hours=1))
            db.commit()
        finally:
            db.close()

        response = self._book(class_id)
        self.assertEqual(response.status_code, 409)

    def test_overlapping_bookings_rejected(self):
        first = self._book()
        self.assertEqual(first.status_code, 201)
        db = SessionLocal()
        try:
            overlap_id = self._create_class(
                db,
                "Overlapping",
                starts_at=datetime.now(timezone.utc) + timedelta(days=5, minutes=30),
                ends_at=datetime.now(timezone.utc) + timedelta(days=5, hours=1, minutes=30),
            )
            db.commit()
        finally:
            db.close()

        response = self._book(overlap_id)
        self.assertEqual(response.status_code, 409)

    def test_client_cannot_supply_another_member_identity(self):
        response = self.client.post(
            "/api/v1/bookings",
            json={"class_id": self.default_class_id, "user_id": self.other_member_id},
            headers=self.member_headers,
        )
        self.assertEqual(response.status_code, 422)

    def test_member_cannot_cancel_another_members_booking(self):
        created = self._book(headers=self.other_member_headers)
        response = self.client.post(
            f"/api/v1/bookings/{created.json()['id']}/cancel",
            headers=self.member_headers,
        )
        self.assertEqual(response.status_code, 403)

    def test_successful_cancellation_updates_status_and_releases_unique_booking(self):
        created = self._book()
        response = self.client.post(
            f"/api/v1/bookings/{created.json()['id']}/cancel",
            headers=self.member_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "cancelled")

        rebooked = self._book()
        self.assertEqual(rebooked.status_code, 201)
        self.assertEqual(rebooked.json()["status"], "booked")

    def test_only_booked_reservations_can_be_cancelled(self):
        created = self._book()
        db = SessionLocal()
        try:
            db.query(Booking).filter(Booking.id == created.json()["id"]).update({"status": "attended"})
            db.commit()
        finally:
            db.close()

        response = self.client.post(
            f"/api/v1/bookings/{created.json()['id']}/cancel",
            headers=self.member_headers,
        )
        self.assertEqual(response.status_code, 409)

    def test_existing_seed_bookings_remain_present(self):
        db = SessionLocal()
        try:
            self.assertEqual(db.query(Booking).count(), self.seed_booking_count + len(self.booking_ids))
            self.assertGreaterEqual(self.seed_booking_count, 10)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()