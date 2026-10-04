import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.auth_store import AuthSessionLocal, UserCredential, init_auth_db
from app.db.base import init_db
from app.db.session import SessionLocal
from app.main import app
from app.models.user import User


class TestAuthStage5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings.JWT_SECRET_KEY = "phase-one-test-key-with-more-than-32-chars"
        init_db()
        init_auth_db()
        cls.client = TestClient(app)
        cls.email_suffix = uuid.uuid4().hex
        cls.admin_id = cls._create_user("admin", "auth-admin", "Admin")
        cls.member_id = cls._create_user("member", "auth-member", "Member")

    @classmethod
    def _create_user(cls, role, prefix, name):
        email = f"{prefix}-{cls.email_suffix}@example.test"
        db = SessionLocal()
        try:
            user = User(
                name=name,
                email=email,
                role=role,
                role_title=role.title(),
                membership_tier="Basic Tier" if role == "member" else None,
                avatar=name[:2].upper(),
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            user_id = user.id
        finally:
            db.close()

        auth_db = AuthSessionLocal()
        try:
            auth_db.add(
                UserCredential(
                    email=email,
                    user_id=user_id,
                    password_hash=hash_password("PhaseOnePassword!2026"),
                )
            )
            auth_db.commit()
        finally:
            auth_db.close()
        return user_id

    @classmethod
    def _headers(cls, user_id):
        return {"Authorization": f"Bearer {create_access_token(user_id)}"}

    def _registration_payload(self, suffix):
        return {
            "name": "New Member",
            "email": f"new-{suffix}-{self.email_suffix}@example.test",
            "password": "StrongPassword!2026",
        }

    def _class_payload(self, trainer_id=2):
        starts_at = datetime.now(timezone.utc) + timedelta(days=3)
        return {
            "title": "Authorized Test Class",
            "category": "Strength",
            "class_type": "indoor",
            "trainer_id": trainer_id,
            "location_name": "Studio A",
            "capacity": 10,
            "start_time": starts_at.isoformat(),
            "end_time": (starts_at + timedelta(hours=1)).isoformat(),
        }

    def test_registration_creates_member_and_password_hash(self):
        payload = self._registration_payload("registration")
        response = self.client.post("/api/v1/auth/register", json=payload)

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["user"]["role"], "member")
        self.assertNotIn("password", data["user"])
        self.assertTrue(data["access_token"])

        auth_db = AuthSessionLocal()
        try:
            credential = auth_db.query(UserCredential).filter_by(email=payload["email"]).one()
            self.assertNotEqual(credential.password_hash, payload["password"])
            self.assertTrue(credential.password_hash.startswith("scrypt$"))
        finally:
            auth_db.close()

    def test_registration_rejects_client_assigned_privileged_role(self):
        payload = self._registration_payload("role")
        payload["role"] = "admin"
        response = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_successful_login_and_invalid_credentials(self):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == self.member_id).one()
            email = user.email
        finally:
            db.close()

        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": email.upper(), "password": "PhaseOnePassword!2026"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["id"], self.member_id)
        self.assertEqual(response.json()["token_type"], "bearer")

        invalid = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "not-the-password"},
        )
        self.assertEqual(invalid.status_code, 401)

    def test_authenticated_identity_comes_from_verified_token(self):
        response = self.client.get(
            "/api/v1/auth/me?role=admin&user_id=1",
            headers=self._headers(self.member_id),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.member_id)
        self.assertEqual(response.json()["role"], "member")

        unauthenticated = self.client.get("/api/v1/auth/me")
        self.assertEqual(unauthenticated.status_code, 401)

    def test_authenticated_dashboard_ignores_impersonation_query(self):
        response = self.client.get(
            "/api/v1/dashboard/metrics?role=admin&user_id=1",
            headers=self._headers(self.member_id),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user_id"], self.member_id)
        self.assertEqual(response.json()["role"], "member")

    def test_class_creation_requires_authenticated_admin_or_trainer(self):
        url = "/api/v1/classes?creator_role=admin&creator_id=1"
        unauthenticated = self.client.post(url, json=self._class_payload())
        self.assertEqual(unauthenticated.status_code, 401)

        member_response = self.client.post(
            url,
            json=self._class_payload(),
            headers=self._headers(self.member_id),
        )
        self.assertEqual(member_response.status_code, 403)

    def test_creator_query_parameters_cannot_grant_or_revoke_authority(self):
        member_response = self.client.post(
            "/api/v1/classes?creator_role=admin&creator_id=1",
            json=self._class_payload(),
            headers=self._headers(self.member_id),
        )
        self.assertEqual(member_response.status_code, 403)

        admin_response = self.client.post(
            "/api/v1/classes?creator_role=member&creator_id=3",
            json=self._class_payload(),
            headers=self._headers(self.admin_id),
        )
        self.assertEqual(admin_response.status_code, 201)

    def test_trainer_cannot_create_a_class_assigned_to_another_trainer(self):
        response = self.client.post(
            "/api/v1/classes",
            json=self._class_payload(trainer_id=1),
            headers=self._headers(2),
        )
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()