"""
Unit and integration tests for Authentication Module
Project: AgenticTravelTech
"""

import os
import sys
from pathlib import Path
from peewee import SqliteDatabase
from fastapi.testclient import TestClient

# Ensure root directory is on PYTHONPATH
root_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_path))

TEST_DB_FILE = "test_auth_temp.db"
test_db = SqliteDatabase(TEST_DB_FILE)

from app.models.user import User
from app.models.base import BaseModel
# Rebind User and BaseModel to test_db before app initializes
User._meta.database = test_db
BaseModel._meta.database = test_db

from app.main import app
from app.dependencies import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

def override_get_db():
    if test_db.is_closed():
        test_db.connect(reuse_if_open=True)
    try:
        yield test_db
    finally:
        pass

def setup_module():
    """Bind models to test database and create schema."""
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass
    test_db.connect(reuse_if_open=True)
    test_db.create_tables([User], safe=True)
    app.dependency_overrides[get_db] = override_get_db

def teardown_module():
    """Drop schema, close test database, and reset dependency overrides."""
    app.dependency_overrides.clear()
    if not test_db.is_closed():
        test_db.close()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass

def test_password_hashing():
    raw_pw = "mysecretpassword123"
    hashed = hash_password(raw_pw)
    assert hashed != raw_pw
    assert verify_password(raw_pw, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_token_generation_and_decoding():
    payload = {"sub": "42"}
    access_token = create_access_token(payload)
    decoded_access = decode_token(access_token)
    assert decoded_access["sub"] == "42"
    assert decoded_access["type"] == "access"
    assert "exp" in decoded_access

    refresh_token = create_refresh_token(payload)
    decoded_refresh = decode_token(refresh_token)
    assert decoded_refresh["sub"] == "42"
    assert decoded_refresh["type"] == "refresh"
    assert "exp" in decoded_refresh

def test_auth_api_flow():
    client = TestClient(app)

    # 1. Register new user
    register_payload = {
        "email": "testuser@example.com",
        "password": "securepassword123"
    }
    res = client.post("/api/v1/auth/register", json=register_payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["email"] == "testuser@example.com"
    assert "id" in data
    user_id = data["id"]

    # 2. Duplicate registration returns 400
    res_dup = client.post("/api/v1/auth/register", json=register_payload)
    assert res_dup.status_code == 400
    assert "already registered" in res_dup.json()["detail"]

    # 3. Login with incorrect password returns 401
    bad_login = client.post("/api/v1/auth/login", json={
        "email": "testuser@example.com",
        "password": "incorrectpassword"
    })
    assert bad_login.status_code == 401

    # 4. Login with correct credentials returns 200 and tokens
    good_login = client.post("/api/v1/auth/login", json=register_payload)
    assert good_login.status_code == 200
    tokens = good_login.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 5. Access protected /me endpoint with Bearer token
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["id"] == user_id
    assert me_data["email"] == "testuser@example.com"

    # 6. Access protected /me endpoint without token returns 403
    unauth_res = client.get("/api/v1/auth/me")
    assert unauth_res.status_code in (401, 403)

    # 7. Refresh access token
    refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    refresh_data = refresh_res.json()
    assert "access_token" in refresh_data
    new_access_token = refresh_data["access_token"]

    # 8. Access /me endpoint with refreshed token
    me_refreshed_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert me_refreshed_res.status_code == 200
    assert me_refreshed_res.json()["email"] == "testuser@example.com"

    # 9. Invalid refresh token returns 401
    bad_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid.jwt.token"})
    assert bad_refresh.status_code == 401

if __name__ == "__main__":
    setup_module()
    try:
        test_password_hashing()
        print("PASS: test_password_hashing")
        test_token_generation_and_decoding()
        print("PASS: test_token_generation_and_decoding")
        test_auth_api_flow()
        print("PASS: test_auth_api_flow")
        print("\nALL AUTHENTICATION TESTS PASSED.")
    finally:
        teardown_module()
