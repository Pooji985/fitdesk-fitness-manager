import unittest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
import sys
import os

# Ensure backend directory is in python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from app.db.auth_store import init_auth_db
from app.db.base import init_db
from app.db.session import SessionLocal
from app.models.fitness_class import FitnessClass
from app.models.user import User
from app.services.weather_service import get_outdoor_class_weather, _forecast_cache


class TestClassesStage4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings.JWT_SECRET_KEY = "phase-four-test-key-with-more-than-32-chars"
        init_db()
        init_auth_db()
        cls.client = TestClient(app)
        cls.created_class_ids = []

    @classmethod
    def auth_headers(cls, user_id):
        return {"Authorization": f"Bearer {create_access_token(user_id)}"}

    @classmethod
    def tearDownClass(cls):
        # Clean up any test-created classes
        if cls.created_class_ids:
            db = SessionLocal()
            try:
                db.query(FitnessClass).filter(FitnessClass.id.in_(cls.created_class_ids)).delete(synchronize_session=False)
                db.commit()
            finally:
                db.close()

    def test_list_all_classes(self):
        """Verify GET /api/v1/classes returns scheduled classes with capacity and booking metrics."""
        response = self.client.get("/api/v1/classes")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 5)

        for c in data:
            self.assertIn("id", c)
            self.assertIn("title", c)
            self.assertIn("category", c)
            self.assertIn("class_type", c)
            self.assertIn("capacity", c)
            self.assertIn("booked_count", c)
            self.assertIn("remaining_spots", c)
            self.assertEqual(c["remaining_spots"], max(0, c["capacity"] - c["booked_count"]))

    def test_filter_classes_by_type(self):
        """Verify class_type filter correctly isolates indoor vs. outdoor classes."""
        # Outdoor filter
        out_res = self.client.get("/api/v1/classes?class_type=outdoor")
        self.assertEqual(out_res.status_code, 200)
        outdoor_classes = out_res.json()
        self.assertGreaterEqual(len(outdoor_classes), 2)
        for c in outdoor_classes:
            self.assertEqual(c["class_type"], "outdoor")
            self.assertIsNotNone(c["weather"], "Outdoor classes must have weather forecast attached")
            self.assertIn(c["weather"]["status"], ["optimal", "warning", "inclement", "unavailable"])

        # Indoor filter
        in_res = self.client.get("/api/v1/classes?class_type=indoor")
        self.assertEqual(in_res.status_code, 200)
        indoor_classes = in_res.json()
        self.assertGreaterEqual(len(indoor_classes), 3)
        for c in indoor_classes:
            self.assertEqual(c["class_type"], "indoor")
            self.assertIsNone(c["weather"], "Indoor classes should not have weather forecast")

    def test_filter_classes_by_category_and_search(self):
        """Verify filtering by category and search keyword."""
        # Category filter
        bootcamp_res = self.client.get("/api/v1/classes?category=Bootcamp")
        self.assertEqual(bootcamp_res.status_code, 200)
        classes = bootcamp_res.json()
        self.assertTrue(all("bootcamp" in c["category"].lower() for c in classes))

        # Search filter
        search_res = self.client.get("/api/v1/classes?search=Central Park")
        self.assertEqual(search_res.status_code, 200)
        search_classes = search_res.json()
        self.assertTrue(any("central park" in c["location_name"].lower() for c in search_classes))

    def test_trainer_and_upcoming_only_filters(self):
        now = datetime.now(timezone.utc)
        db = SessionLocal()
        try:
            future_class = FitnessClass(
                title="Upcoming Filter Test Class",
                category="Strength",
                class_type="indoor",
                trainer_id=2,
                location_name="Filter Test Studio",
                capacity=10,
                start_time=now + timedelta(days=3),
                end_time=now + timedelta(days=3, hours=1),
                is_cancelled=False,
            )
            past_class = FitnessClass(
                title="Past Filter Test Class",
                category="Strength",
                class_type="indoor",
                trainer_id=2,
                location_name="Filter Test Studio",
                capacity=10,
                start_time=now - timedelta(days=3),
                end_time=now - timedelta(days=3) + timedelta(hours=1),
                is_cancelled=False,
            )
            other_trainer_class = FitnessClass(
                title="Other Trainer Filter Test Class",
                category="Strength",
                class_type="indoor",
                trainer_id=1,
                location_name="Filter Test Studio",
                capacity=10,
                start_time=now + timedelta(days=4),
                end_time=now + timedelta(days=4, hours=1),
                is_cancelled=False,
            )
            db.add_all([future_class, past_class, other_trainer_class])
            db.commit()
            for fitness_class in (future_class, past_class, other_trainer_class):
                db.refresh(fitness_class)
                self.created_class_ids.append(fitness_class.id)
            future_id, past_id, other_trainer_id = future_class.id, past_class.id, other_trainer_class.id
        finally:
            db.close()

        response = self.client.get("/api/v1/classes?trainer_id=2&upcoming_only=true&include_weather=false")
        self.assertEqual(response.status_code, 200)
        result_ids = {item["id"] for item in response.json()}
        self.assertIn(future_id, result_ids)
        self.assertNotIn(past_id, result_ids)
        self.assertNotIn(other_trainer_id, result_ids)

    def test_weather_service_structure_and_caching(self):
        """Verify Open-Meteo weather service returns required schema and uses caching."""
        target_time = datetime.now(timezone.utc) + timedelta(days=1)
        weather_1 = get_outdoor_class_weather(40.785091, -73.968285, target_time)
        self.assertIn("status", weather_1)
        self.assertIn("temperature", weather_1)
        self.assertIn("precipitation_probability", weather_1)
        self.assertIn("wind_speed", weather_1)
        self.assertIn("condition", weather_1)
        self.assertIn("alert_message", weather_1)
        self.assertIn("badge_color", weather_1)

        # Caching check
        cache_key = f"{round(40.785091, 2)}:{round(-73.968285, 2)}:{target_time.strftime('%Y%m%d%H')}"
        self.assertIn(cache_key, _forecast_cache)
        cached_result = get_outdoor_class_weather(40.785091, -73.968285, target_time)
        self.assertEqual(weather_1, cached_result)

    def test_weather_service_fallback_on_network_failure(self):
        """Verify weather service returns safe fallback when network or API fails."""
        with patch("httpx.Client.get", side_effect=Exception("Simulated connection timeout")):
            # Use unique coordinates to bypass cache
            target_time = datetime.now(timezone.utc) + timedelta(days=5)
            fallback = get_outdoor_class_weather(51.5074, -0.1278, target_time)
            self.assertEqual(fallback["status"], "unavailable")
            self.assertIn("unavailable", fallback["alert_message"].lower())
            self.assertIn("alert_message", fallback)
            self.assertIn("badge_color", fallback)

    def test_get_available_trainers(self):
        """Verify GET /api/v1/classes/trainers returns staff for scheduling modal."""
        response = self.client.get("/api/v1/classes/trainers")
        self.assertEqual(response.status_code, 200)
        trainers = response.json()
        self.assertGreaterEqual(len(trainers), 2)
        names = [t["name"] for t in trainers]
        self.assertIn("Marcus Vance", names)
        self.assertIn("Alex Morgan", names)

    def test_member_role_forbidden_from_class_creation(self):
        """Verify Members are forbidden (403) from creating classes."""
        now = datetime.now(timezone.utc)
        payload = {
            "title": "Unauthorized Member Class",
            "category": "Strength",
            "class_type": "indoor",
            "trainer_id": 2,
            "location_name": "Studio A",
            "capacity": 10,
            "start_time": (now + timedelta(days=2)).isoformat(),
            "end_time": (now + timedelta(days=2, hours=1)).isoformat(),
        }
        response = self.client.post(
            "/api/v1/classes?creator_role=admin&creator_id=1",
            json=payload,
            headers=self.auth_headers(3),
        )
        self.assertEqual(response.status_code, 403)

    def test_class_creation_validation_errors(self):
        """Verify input validation: end_time must be after start_time, capacity > 0."""
        now = datetime.now(timezone.utc)
        # End time before start time
        invalid_time_payload = {
            "title": "Invalid Time Class",
            "category": "Yoga",
            "class_type": "indoor",
            "trainer_id": 2,
            "location_name": "Studio B",
            "capacity": 15,
            "start_time": (now + timedelta(days=2, hours=2)).isoformat(),
            "end_time": (now + timedelta(days=2, hours=1)).isoformat(),
        }
        res1 = self.client.post(
            "/api/v1/classes",
            json=invalid_time_payload,
            headers=self.auth_headers(1),
        )
        self.assertEqual(res1.status_code, 422)

        # Non-existent trainer ID
        invalid_trainer_payload = {
            "title": "Invalid Trainer Class",
            "category": "Yoga",
            "class_type": "indoor",
            "trainer_id": 99999,
            "location_name": "Studio B",
            "capacity": 15,
            "start_time": (now + timedelta(days=2)).isoformat(),
            "end_time": (now + timedelta(days=2, hours=1)).isoformat(),
        }
        res2 = self.client.post(
            "/api/v1/classes",
            json=invalid_trainer_payload,
            headers=self.auth_headers(1),
        )
        self.assertEqual(res2.status_code, 400)
        self.assertIn("Active trainer with ID 99999 does not exist", res2.json()["detail"])

    def test_admin_can_create_class_and_trainer_is_forbidden(self):
        """Only authenticated Admins may create classes."""
        now = datetime.now(timezone.utc)
        admin_payload = {
            "title": "Admin Stage 4 Kettlebell Circuit",
            "description": "Technique and explosive power intervals with Russian kettlebells.",
            "category": "Strength",
            "class_type": "indoor",
            "trainer_id": 2,
            "location_name": "Studio C Annex",
            "capacity": 16,
            "start_time": (now + timedelta(days=4, hours=14)).isoformat(),
            "end_time": (now + timedelta(days=4, hours=15)).isoformat(),
        }
        admin_response = self.client.post(
            "/api/v1/classes?creator_role=member&creator_id=3",
            json=admin_payload,
            headers=self.auth_headers(1),
        )
        self.assertEqual(admin_response.status_code, 201)
        admin_data = admin_response.json()
        self.assertEqual(admin_data["title"], "Admin Stage 4 Kettlebell Circuit")
        self.assertEqual(admin_data["class_type"], "indoor")
        self.assertIsNone(admin_data["weather"])
        self.created_class_ids.append(admin_data["id"])

        trainer_response = self.client.post(
            "/api/v1/classes?creator_role=admin&creator_id=1",
            json=admin_payload,
            headers=self.auth_headers(2),
        )
        member_response = self.client.post(
            "/api/v1/classes?creator_role=admin&creator_id=1",
            json=admin_payload,
            headers=self.auth_headers(3),
        )
        anonymous_response = self.client.post("/api/v1/classes", json=admin_payload)
        self.assertEqual(trainer_response.status_code, 403)
        self.assertEqual(member_response.status_code, 403)
        self.assertEqual(anonymous_response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
