import unittest
from fastapi.testclient import TestClient
import sys
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

# Ensure backend directory is in python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from app.db.base import init_db
from app.db.session import SessionLocal
from app.models.user import User
from app.models.fitness_class import FitnessClass
from app.models.booking import Booking


class TestDashboardStage3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings.JWT_SECRET_KEY = "phase-one-dashboard-test-secret-more-than-32-chars"
        init_db()
        cls.client = TestClient(app)

    @classmethod
    def auth_headers(cls, user_id):
        return {"Authorization": f"Bearer {create_access_token(user_id)}"}

    def test_database_seeded_models(self):
        """Verify models and idempotent seeding populated database."""
        db = SessionLocal()
        try:
            user_count = db.query(User).count()
            class_count = db.query(FitnessClass).count()
            booking_count = db.query(Booking).count()

            self.assertGreaterEqual(user_count, 3, "Should have at least the 3 primary personas")
            self.assertGreaterEqual(class_count, 3, "Should have scheduled indoor/outdoor classes")
            self.assertGreaterEqual(booking_count, 3, "Should have sample booking records")

            # Check core personas
            admin = db.query(User).filter(User.role == "admin").first()
            trainer = db.query(User).filter(User.role == "trainer").first()
            member = db.query(User).filter(User.role == "member").first()

            self.assertIsNotNone(admin)
            self.assertIsNotNone(trainer)
            self.assertIsNotNone(member)
        finally:
            db.close()

    def test_admin_dashboard_metrics(self):
        """Verify Admin receives gym-wide metrics and activity log."""
        response = self.client.get("/api/v1/dashboard/metrics", headers=self.auth_headers(1))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["role"], "admin")
        self.assertEqual(data["user_id"], 1)
        self.assertEqual(len(data["stats"]), 8)
        labels = [s["label"] for s in data["stats"]]
        self.assertIn("Active Members", labels)
        self.assertIn("Scheduled Classes", labels)
        self.assertIn("Total Bookings", labels)
        self.assertIn("Weather Alerts", labels)
        self.assertIsInstance(data["recent_activities"], list)

    def test_admin_dashboard_status_report_uses_real_booking_statuses(self):
        response = self.client.get("/api/v1/dashboard/metrics", headers=self.auth_headers(1))
        self.assertEqual(response.status_code, 200)
        stats = {item["label"]: item["value"] for item in response.json()["stats"]}
        db = SessionLocal()
        try:
            counts = {
                status: db.query(Booking).filter(Booking.status == status).count()
                for status in ("booked", "attended", "no_show", "cancelled")
            }
            active_members = db.query(User).filter(User.role == "member", User.is_active.is_(True)).count()
            active_classes = db.query(FitnessClass).filter(FitnessClass.is_cancelled.is_(False)).count()
        finally:
            db.close()

        self.assertEqual(stats["Active Members"], str(active_members))
        self.assertEqual(stats["Scheduled Classes"], str(active_classes))
        self.assertEqual(stats["Total Bookings"], str(sum(counts.values())))
        self.assertEqual(stats["Attended"], str(counts["attended"]))
        self.assertEqual(stats["No-Show"], str(counts["no_show"]))
        self.assertEqual(stats["Cancelled Bookings"], str(counts["cancelled"]))
        denominator = counts["attended"] + counts["no_show"]
        expected_rate = f"{round(counts['attended'] / denominator * 100, 1)}%" if denominator else "N/A"
        self.assertEqual(stats["Attendance Rate"], expected_rate)

    def test_trainer_dashboard_metrics(self):
        """Verify Trainer receives assigned class metrics and check-in stats."""
        response = self.client.get("/api/v1/dashboard/metrics", headers=self.auth_headers(2))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["role"], "trainer")
        self.assertEqual(data["user_id"], 2)
        self.assertEqual(len(data["stats"]), 4)
        labels = [s["label"] for s in data["stats"]]
        self.assertIn("Assigned Classes", labels)
        self.assertIn("Total Attendees", labels)
        self.assertIn("Check-In Rate", labels)

    def test_member_dashboard_metrics(self):
        """Verify Member receives personal bookings, attended workouts, and tier."""
        response = self.client.get("/api/v1/dashboard/metrics", headers=self.auth_headers(3))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["role"], "member")
        self.assertEqual(data["user_id"], 3)
        self.assertEqual(len(data["stats"]), 4)
        labels = [s["label"] for s in data["stats"]]
        self.assertIn("My Active Bookings", labels)
        self.assertIn("Membership Status", labels)
        self.assertIn("Classes Attended", labels)

    def test_dashboard_requires_authentication(self):
        response = self.client.get("/api/v1/dashboard/metrics?role=admin&user_id=1")
        self.assertEqual(response.status_code, 401)

    def test_member_cannot_impersonate_admin_or_another_member(self):
        headers = self.auth_headers(3)
        another_user = self.client.get("/api/v1/dashboard/metrics?user_id=4", headers=headers)
        admin_role = self.client.get("/api/v1/dashboard/metrics?role=admin", headers=headers)

        for response in (another_user, admin_role):
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["role"], "member")
            self.assertEqual(response.json()["user_id"], 3)

    def test_trainer_cannot_change_role_or_identity_with_query_parameters(self):
        response = self.client.get(
            "/api/v1/dashboard/metrics?role=admin&user_id=1",
            headers=self.auth_headers(2),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "trainer")
        self.assertEqual(response.json()["user_id"], 2)

    def test_invalid_token_is_rejected(self):
        response = self.client.get(
            "/api/v1/dashboard/metrics",
            headers={"Authorization": "Bearer invalid-token"},
        )
        self.assertEqual(response.status_code, 401)

    def test_expired_token_is_rejected(self):
        token = create_access_token(1)
        future_now = datetime.now(timezone.utc) + timedelta(hours=2)
        with patch("app.core.security.datetime") as mocked_datetime:
            mocked_datetime.now.return_value = future_now
            response = self.client.get(
                "/api/v1/dashboard/metrics",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
