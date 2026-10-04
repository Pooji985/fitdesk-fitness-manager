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


class TestClassEditCancelPhase4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings.JWT_SECRET_KEY = "phase-four-class-edit-cancel-test-key-32chars"
        init_db()
        init_auth_db()
        cls.client = TestClient(app)
        db = SessionLocal()
        try:
            cls.seed_users = [(u.id, u.email, u.role) for u in db.query(User).order_by(User.id).all()]
            cls.seed_classes = [(c.id, c.title, c.is_cancelled) for c in db.query(FitnessClass).order_by(FitnessClass.id).all()]
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
            self.admin = self._new_user("admin", "Phase 4 Admin")
            self.trainer = self._new_user("trainer", "Assigned Trainer")
            self.other_trainer = self._new_user("trainer", "Other Trainer")
            self.member = self._new_user("member", "Phase 4 Member")
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
            self.other_member_headers = self._headers(self.other_member_id)

            self.class_ids = []
            self.booking_ids = []
            first_start = datetime.now(timezone.utc) + timedelta(days=10)
            second_start = first_start + timedelta(days=2)
            self.first_class_id = self._new_class(db, self.trainer_id, "First Phase 4 Class", first_start, capacity=4)
            self.second_class_id = self._new_class(db, self.other_trainer_id, "Second Phase 4 Class", second_start, capacity=6)
            self.member_booking = Booking(user_id=self.member_id, class_id=self.first_class_id, status="booked")
            self.attended_booking = Booking(user_id=self.other_member_id, class_id=self.first_class_id, status="attended")
            db.add_all([self.member_booking, self.attended_booking])
            db.flush()
            self.member_booking_id = self.member_booking.id
            self.attended_booking_id = self.attended_booking.id
            self.booking_ids.extend([self.member_booking_id, self.attended_booking_id])
            db.commit()
        finally:
            db.close()

    def _new_user(self, role, label):
        return User(
            name=f"{label} {self.suffix[:6]}",
            email=f"{role}-{label.lower().replace(' ', '-')}-{self.suffix}@phase4.test",
            role=role,
            role_title=role.title(),
            membership_tier="Basic Tier" if role == "member" else None,
            is_active=True,
        )

    def _new_class(self, db, trainer_id, title, start_time, capacity):
        fitness_class = FitnessClass(
            title=f"{title} {self.suffix[:6]}",
            description="Phase 4 class test",
            category="Strength",
            class_type="indoor",
            trainer_id=trainer_id,
            location_name="Phase 4 Studio",
            capacity=capacity,
            start_time=start_time,
            end_time=start_time + timedelta(hours=1),
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

    def test_admin_can_edit_class_and_preserves_bookings(self):
        response = self.client.patch(
            f"/api/v1/classes/{self.first_class_id}",
            json={"title": "Updated Admin Class", "location_name": "New Studio"},
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Updated Admin Class")
        self.assertEqual(response.json()["trainer_id"], self.trainer_id)
        self.assertEqual(response.json()["booked_count"], 2)

        db = SessionLocal()
        try:
            statuses = {booking.id: booking.status for booking in db.query(Booking).filter(Booking.id.in_(self.booking_ids)).all()}
            self.assertEqual(statuses, {self.member_booking_id: "booked", self.attended_booking_id: "attended"})
        finally:
            db.close()

    def test_admin_can_reassign_class_to_active_trainer(self):
        response = self.client.patch(
            f"/api/v1/classes/{self.first_class_id}",
            json={"trainer_id": self.other_trainer_id},
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["trainer_id"], self.other_trainer_id)

    def test_trainer_cannot_edit_even_assigned_class_or_another_class(self):
        own_class = self.client.patch(
            f"/api/v1/classes/{self.first_class_id}",
            json={"title": "Trainer Edit Attempt"},
            headers=self.trainer_headers,
        )
        other_class = self.client.patch(
            f"/api/v1/classes/{self.second_class_id}",
            json={"title": "Trainer Edit Attempt"},
            headers=self.trainer_headers,
        )
        self.assertEqual(own_class.status_code, 403)
        self.assertEqual(other_class.status_code, 403)

    def test_member_and_unauthenticated_users_cannot_edit_class(self):
        member_response = self.client.patch(
            f"/api/v1/classes/{self.first_class_id}?role=admin&user_id={self.admin_id}",
            json={"title": "Member Edit Attempt"},
            headers=self.member_headers,
        )
        anonymous_response = self.client.patch(
            f"/api/v1/classes/{self.first_class_id}",
            json={"title": "Anonymous Edit Attempt"},
        )
        self.assertEqual(member_response.status_code, 403)
        self.assertEqual(anonymous_response.status_code, 401)

    def test_invalid_updates_and_capacity_reduction_are_rejected(self):
        invalid_window = self.client.patch(
            f"/api/v1/classes/{self.first_class_id}",
            json={"start_time": (datetime.now(timezone.utc) + timedelta(days=11)).isoformat(), "end_time": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()},
            headers=self.admin_headers,
        )
        too_small = self.client.patch(
            f"/api/v1/classes/{self.first_class_id}",
            json={"capacity": 1},
            headers=self.admin_headers,
        )
        bad_trainer = self.client.patch(
            f"/api/v1/classes/{self.first_class_id}",
            json={"trainer_id": 999999},
            headers=self.admin_headers,
        )
        self.assertEqual(invalid_window.status_code, 422)
        self.assertEqual(too_small.status_code, 409)
        self.assertEqual(bad_trainer.status_code, 400)

    def test_edit_cannot_create_overlap_for_enrolled_member(self):
        other_booking = Booking(user_id=self.member_id, class_id=self.second_class_id, status="booked")
        db = SessionLocal()
        try:
            db.add(other_booking)
            db.commit()
            self.booking_ids.append(other_booking.id)
        finally:
            db.close()

        db = SessionLocal()
        try:
            second = db.query(FitnessClass).filter(FitnessClass.id == self.second_class_id).one()
            proposed_start = second.start_time + timedelta(minutes=15)
            proposed_end = proposed_start + timedelta(hours=1)
        finally:
            db.close()
        response = self.client.patch(
            f"/api/v1/classes/{self.first_class_id}",
            json={"start_time": proposed_start.isoformat(), "end_time": proposed_end.isoformat()},
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 409)

    def test_admin_cancels_class_without_removing_bookings_or_attendance(self):
        response = self.client.post(f"/api/v1/classes/{self.first_class_id}/cancel", headers=self.admin_headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_cancelled"])

        booking_history = self.client.get("/api/v1/bookings", headers=self.member_headers)
        retained = next(row for row in booking_history.json() if row["class_id"] == self.first_class_id)
        self.assertEqual(retained["status"], "booked")
        self.assertTrue(retained["fitness_class"]["is_cancelled"])

        roster = self.client.get(f"/api/v1/attendance/classes/{self.first_class_id}", headers=self.trainer_headers)
        self.assertEqual(roster.status_code, 200)
        self.assertEqual({row["status"] for row in roster.json()}, {"booked", "attended"})

        active_schedule = self.client.get("/api/v1/classes?include_weather=false")
        self.assertNotIn(self.first_class_id, {row["id"] for row in active_schedule.json()})
        class_detail = self.client.get(f"/api/v1/classes/{self.first_class_id}?include_weather=false")
        self.assertTrue(class_detail.json()["is_cancelled"])

        db = SessionLocal()
        try:
            retained_rows = db.query(Booking).filter(Booking.id.in_(self.booking_ids)).all()
            self.assertEqual(len(retained_rows), 2)
            self.assertEqual({row.status for row in retained_rows}, {"booked", "attended"})
        finally:
            db.close()

    def test_trainer_member_and_anonymous_users_cannot_cancel_class(self):
        trainer_response = self.client.post(f"/api/v1/classes/{self.first_class_id}/cancel", headers=self.trainer_headers)
        member_response = self.client.post(
            f"/api/v1/classes/{self.first_class_id}/cancel?role=admin&user_id={self.admin_id}",
            headers=self.member_headers,
        )
        anonymous_response = self.client.post(f"/api/v1/classes/{self.first_class_id}/cancel")
        self.assertEqual(trainer_response.status_code, 403)
        self.assertEqual(member_response.status_code, 403)
        self.assertEqual(anonymous_response.status_code, 401)

    def test_cancelled_class_cannot_be_booked(self):
        cancelled = self.client.post(f"/api/v1/classes/{self.first_class_id}/cancel", headers=self.admin_headers)
        self.assertEqual(cancelled.status_code, 200)
        attempt = self.client.post(
            "/api/v1/bookings",
            json={"class_id": self.first_class_id},
            headers=self.other_member_headers,
        )
        self.assertEqual(attempt.status_code, 404)

    def test_seeded_users_classes_and_bookings_are_preserved(self):
        db = SessionLocal()
        try:
            users = set(db.query(User.id, User.email, User.role).filter(User.id.in_([row[0] for row in self.seed_users])).all())
            classes = set(db.query(FitnessClass.id, FitnessClass.title, FitnessClass.is_cancelled).filter(FitnessClass.id.in_([row[0] for row in self.seed_classes])).all())
            bookings = set(db.query(Booking.id, Booking.user_id, Booking.class_id, Booking.status).filter(Booking.id.in_([row[0] for row in self.seed_bookings])).all())
            self.assertEqual(users, set(self.seed_users))
            self.assertEqual(classes, set(self.seed_classes))
            self.assertEqual(bookings, set(self.seed_bookings))
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()