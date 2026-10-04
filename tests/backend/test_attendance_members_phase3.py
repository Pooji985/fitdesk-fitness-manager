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


class TestAttendanceAndMembersPhase3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings.JWT_SECRET_KEY = "phase-three-attendance-test-secret-32chars"
        init_db()
        init_auth_db()
        cls.client = TestClient(app)
        db = SessionLocal()
        try:
            cls.seed_users = [(u.id, u.email, u.role) for u in db.query(User).order_by(User.id).all()]
            cls.seed_classes = [(c.id, c.title) for c in db.query(FitnessClass).order_by(FitnessClass.id).all()]
            cls.seed_bookings = [(b.id, b.user_id, b.class_id, b.status) for b in db.query(Booking).order_by(Booking.id).all()]
        finally:
            db.close()

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    @classmethod
    def _headers(cls, user_id):
        return {"Authorization": f"Bearer {create_access_token(user_id)}"}

    def setUp(self):
        self.suffix = uuid.uuid4().hex
        db = SessionLocal()
        try:
            self.admin = self._new_user("admin", "Admin")
            self.trainer = self._new_user("trainer", "Assigned Trainer")
            self.other_trainer = self._new_user("trainer", "Other Trainer")
            self.member = self._new_user("member", "Attendance Member")
            self.other_member = self._new_user("member", "Other Member")
            db.add_all([self.admin, self.trainer, self.other_trainer, self.member, self.other_member])
            db.flush()
            self.admin_id = self.admin.id
            self.trainer_id = self.trainer.id
            self.other_trainer_id = self.other_trainer.id
            self.member_id = self.member.id
            self.other_member_id = self.other_member.id
            self.admin_headers = self._headers(self.admin_id)
            self.trainer_headers = self._headers(self.trainer_id)
            self.other_trainer_headers = self._headers(self.other_trainer_id)
            self.member_headers = self._headers(self.member_id)

            self.class_ids = []
            self.booking_ids = []
            starts_at = datetime.now(timezone.utc) + timedelta(days=2)
            self.assigned_class_id = self._new_class(db, self.trainer_id, "Assigned Session", starts_at)
            self.other_class_id = self._new_class(db, self.other_trainer_id, "Other Session", starts_at + timedelta(days=1))
            self.booking = Booking(user_id=self.member_id, class_id=self.assigned_class_id, status="booked")
            db.add(self.booking)
            db.flush()
            self.booking_id = self.booking.id
            self.booking_ids.append(self.booking_id)
            self.cancelled_booking = Booking(user_id=self.other_member_id, class_id=self.assigned_class_id, status="cancelled")
            db.add(self.cancelled_booking)
            db.flush()
            self.cancelled_booking_id = self.cancelled_booking.id
            self.booking_ids.append(self.cancelled_booking_id)
            db.commit()
        finally:
            db.close()

    def _new_user(self, role, name):
        return User(
            name=f"{name} {self.suffix[:6]}",
            email=f"{role}-{name.lower().replace(' ', '-')}-{self.suffix}@example.test",
            role=role,
            role_title=role.title(),
            membership_tier="Basic Tier" if role == "member" else None,
            is_active=True,
        )

    def _new_class(self, db, trainer_id, title, starts_at):
        fitness_class = FitnessClass(
            title=f"{title} {self.suffix[:6]}",
            description="Phase 3 test class",
            category="Strength",
            class_type="indoor",
            trainer_id=trainer_id,
            location_name="Test Studio",
            capacity=10,
            start_time=starts_at,
            end_time=starts_at + timedelta(hours=1),
            is_cancelled=False,
        )
        db.add(fitness_class)
        db.flush()
        self.class_ids.append(fitness_class.id)
        return fitness_class.id

    def tearDown(self):
        db = SessionLocal()
        try:
            db.query(Booking).filter(
                or_(
                    Booking.user_id.in_([self.member_id, self.other_member_id]),
                    Booking.class_id.in_(self.class_ids),
                    Booking.id.in_(self.booking_ids),
                )
            ).delete(synchronize_session=False)
            db.query(FitnessClass).filter(FitnessClass.id.in_(self.class_ids)).delete(synchronize_session=False)
            db.query(User).filter(User.id.in_([
                self.admin_id,
                self.trainer_id,
                self.other_trainer_id,
                self.member_id,
                self.other_member_id,
            ])).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

    def test_admin_can_view_roster_and_mark_valid_booking_attended(self):
        roster = self.client.get(f"/api/v1/attendance/classes/{self.assigned_class_id}", headers=self.admin_headers)
        self.assertEqual(roster.status_code, 200)
        self.assertEqual([row["member_id"] for row in roster.json()], [self.member_id])

        response = self.client.patch(
            f"/api/v1/attendance/bookings/{self.booking_id}",
            json={"status": "attended"},
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "attended")

    def test_assigned_trainer_can_view_and_mark_roster(self):
        roster = self.client.get(f"/api/v1/attendance/classes/{self.assigned_class_id}", headers=self.trainer_headers)
        self.assertEqual(roster.status_code, 200)
        response = self.client.patch(
            f"/api/v1/attendance/bookings/{self.booking_id}",
            json={"status": "no_show"},
            headers=self.trainer_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "no_show")

    def test_trainer_cannot_access_another_trainers_class_attendance(self):
        roster = self.client.get(f"/api/v1/attendance/classes/{self.other_class_id}", headers=self.trainer_headers)
        self.assertEqual(roster.status_code, 403)

        other_class_booking = Booking(user_id=self.member_id, class_id=self.other_class_id, status="booked")
        db = SessionLocal()
        try:
            db.add(other_class_booking)
            db.commit()
            other_booking_id = other_class_booking.id
            self.booking_ids.append(other_booking_id)
        finally:
            db.close()

        response = self.client.patch(
            f"/api/v1/attendance/bookings/{other_booking_id}",
            json={"status": "attended"},
            headers=self.trainer_headers,
        )
        self.assertEqual(response.status_code, 403)

    def test_member_cannot_view_or_mark_attendance_even_with_role_query(self):
        roster = self.client.get(
            f"/api/v1/attendance/classes/{self.assigned_class_id}?role=admin&user_id={self.admin_id}",
            headers=self.member_headers,
        )
        self.assertEqual(roster.status_code, 403)
        response = self.client.patch(
            f"/api/v1/attendance/bookings/{self.booking_id}?role=admin&user_id={self.admin_id}",
            json={"status": "attended"},
            headers=self.member_headers,
        )
        self.assertEqual(response.status_code, 403)

    def test_attendance_rejects_missing_and_cancelled_bookings(self):
        missing = self.client.patch(
            "/api/v1/attendance/bookings/99999999",
            json={"status": "attended"},
            headers=self.admin_headers,
        )
        cancelled = self.client.patch(
            f"/api/v1/attendance/bookings/{self.cancelled_booking_id}",
            json={"status": "attended"},
            headers=self.admin_headers,
        )
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(cancelled.status_code, 409)

    def test_attendance_accepts_only_specified_marking_statuses(self):
        response = self.client.patch(
            f"/api/v1/attendance/bookings/{self.booking_id}",
            json={"status": "cancelled"},
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 422)

    def test_members_list_is_admin_only_and_excludes_staff(self):
        admin_response = self.client.get("/api/v1/members", headers=self.admin_headers)
        self.assertEqual(admin_response.status_code, 200)
        listed_ids = {member["id"] for member in admin_response.json()}
        roles_are_members = all(member["role"] == "member" for member in admin_response.json())
        self.assertTrue(roles_are_members)
        self.assertIn(self.member_id, listed_ids)
        self.assertNotIn(self.trainer_id, listed_ids)
        self.assertIn("emergency_contact_phone", admin_response.json()[0])

        self.assertEqual(self.client.get("/api/v1/members?role=admin", headers=self.trainer_headers).status_code, 403)
        self.assertEqual(self.client.get("/api/v1/members?role=admin", headers=self.member_headers).status_code, 403)

    def test_admin_can_update_member_status_tier_and_contact_details(self):
        response = self.client.patch(
            f"/api/v1/members/{self.member_id}",
            json={
                "is_active": False,
                "membership_tier": "Premium",
                "phone": " 555-0100 ",
                "emergency_contact_name": " Casey Contact ",
                "emergency_contact_phone": " 555-0199 ",
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_active"])
        self.assertEqual(response.json()["membership_tier"], "Premium")
        self.assertEqual(response.json()["phone"], "555-0100")
        self.assertEqual(response.json()["emergency_contact_name"], "Casey Contact")
        self.assertEqual(response.json()["emergency_contact_phone"], "555-0199")

        invalid_status = self.client.patch(
            f"/api/v1/members/{self.member_id}",
            json={"is_active": None},
            headers=self.admin_headers,
        )
        self.assertEqual(invalid_status.status_code, 422)

    def test_member_can_view_and_update_only_their_own_contact_profile(self):
        profile = self.client.get(
            f"/api/v1/members/me?user_id={self.other_member_id}",
            headers=self.member_headers,
        )
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.json()["id"], self.member_id)

        updated = self.client.patch(
            f"/api/v1/members/me?user_id={self.other_member_id}",
            json={"phone": "555-0140", "emergency_contact_name": "Emergency Contact"},
            headers=self.member_headers,
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["id"], self.member_id)
        self.assertEqual(updated.json()["phone"], "555-0140")
        self.assertEqual(updated.json()["emergency_contact_name"], "Emergency Contact")

        forbidden = self.client.patch(
            "/api/v1/members/me",
            json={"is_active": False, "membership_tier": "Premium", "role": "admin", "user_id": self.other_member_id},
            headers=self.member_headers,
        )
        self.assertEqual(forbidden.status_code, 422)
        self.assertEqual(self.client.get("/api/v1/members/me", headers=self.admin_headers).status_code, 403)
        self.assertEqual(self.client.get("/api/v1/members/me", headers=self.trainer_headers).status_code, 403)

    def test_non_admin_cannot_update_members_and_members_cannot_target_other_members(self):
        trainer_response = self.client.patch(
            f"/api/v1/members/{self.member_id}",
            json={"is_active": False},
            headers=self.trainer_headers,
        )
        member_response = self.client.patch(
            f"/api/v1/members/{self.other_member_id}?role=admin&user_id={self.admin_id}",
            json={"membership_tier": "Premium"},
            headers=self.member_headers,
        )
        self.assertEqual(trainer_response.status_code, 403)
        self.assertEqual(member_response.status_code, 403)

    def test_seeded_business_records_remain_unchanged(self):
        db = SessionLocal()
        try:
            current_users = {(user_id, email, role) for user_id, email, role in self.seed_users}
            current_classes = set(self.seed_classes)
            current_bookings = set(self.seed_bookings)
            self.assertEqual(set(db.query(User.id, User.email, User.role).filter(User.id.in_([item[0] for item in self.seed_users])).all()), current_users)
            self.assertEqual(set(db.query(FitnessClass.id, FitnessClass.title).filter(FitnessClass.id.in_([item[0] for item in self.seed_classes])).all()), current_classes)
            self.assertEqual(set(db.query(Booking.id, Booking.user_id, Booking.class_id, Booking.status).filter(Booking.id.in_([item[0] for item in self.seed_bookings])).all()), current_bookings)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()