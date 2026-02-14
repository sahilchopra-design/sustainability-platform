"""
Test Authentication Endpoints - Email/Password JWT Flow
Tests: register, login, /me, logout
Google OAuth session exchange is MOCKED (requires real Emergent Auth redirect flow)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable not set")


class TestHealthCheck:
    """Verify API is reachable before running auth tests"""
    
    def test_api_health(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ API health check passed")


class TestRegister:
    """POST /api/auth/register - Creates new user and returns session_token"""
    
    def test_register_creates_user_returns_session_token(self):
        """Register with unique email, verify session_token returned"""
        unique_email = f"TEST_register_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": unique_email,
            "password": "testpass123",
            "name": "Test Register User"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "session_token" in data, "Response should include session_token"
        assert "user_id" in data, "Response should include user_id"
        assert data["email"] == unique_email
        assert data["name"] == "Test Register User"
        assert data["session_token"].startswith("sess_")
        print(f"✓ Register successful: {data['user_id']}, token: {data['session_token'][:20]}...")
    
    def test_register_returns_400_duplicate_email(self):
        """Register with existing email should return 400"""
        # Use the known test user email
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Duplicate User"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        
        assert response.status_code == 400, f"Expected 400 for duplicate email, got {response.status_code}"
        data = response.json()
        assert "already registered" in data.get("detail", "").lower() or "duplicate" in str(data).lower()
        print(f"✓ Register duplicate email correctly returns 400: {data.get('detail')}")
    
    def test_register_returns_422_missing_fields(self):
        """Register with missing required fields should return 422"""
        payload = {"email": "incomplete@test.com"}  # Missing password and name
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        
        assert response.status_code == 422, f"Expected 422 for missing fields, got {response.status_code}"
        print("✓ Register with missing fields correctly returns 422")


class TestLogin:
    """POST /api/auth/login - Authenticates with email/password"""
    
    def test_login_success_returns_session_token(self):
        """Login with valid credentials returns session_token"""
        payload = {
            "email": "test@example.com",
            "password": "test123456"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "session_token" in data, "Response should include session_token"
        assert "user_id" in data, "Response should include user_id"
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["session_token"].startswith("sess_")
        print(f"✓ Login successful, token: {data['session_token'][:20]}...")
    
    def test_login_returns_401_wrong_password(self):
        """Login with wrong password returns 401"""
        payload = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        
        assert response.status_code == 401, f"Expected 401 for wrong password, got {response.status_code}"
        data = response.json()
        assert "invalid" in data.get("detail", "").lower() or "credentials" in data.get("detail", "").lower()
        print(f"✓ Login wrong password correctly returns 401: {data.get('detail')}")
    
    def test_login_returns_401_nonexistent_user(self):
        """Login with non-existent user returns 401"""
        payload = {
            "email": "nonexistent@example.com",
            "password": "anypassword"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        
        assert response.status_code == 401, f"Expected 401 for non-existent user, got {response.status_code}"
        print("✓ Login non-existent user correctly returns 401")


class TestGetCurrentUser:
    """GET /api/auth/me - Returns user data with valid session token"""
    
    @pytest.fixture
    def session_token(self):
        """Get a valid session token via login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123456"
        })
        if response.status_code != 200:
            pytest.skip("Could not get session token - login failed")
        return response.json()["session_token"]
    
    def test_me_returns_user_with_valid_token(self, session_token):
        """GET /api/auth/me with valid token returns user data"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {session_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify user data structure
        assert "user_id" in data
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert "picture" in data  # Should have picture field (empty string for JWT users)
        print(f"✓ /me returns user data: {data['user_id']}, {data['email']}")
    
    def test_me_returns_401_without_token(self):
        """GET /api/auth/me without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 401, f"Expected 401 without token, got {response.status_code}"
        print("✓ /me without token correctly returns 401")
    
    def test_me_returns_401_invalid_token(self):
        """GET /api/auth/me with invalid token returns 401"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": "Bearer invalid_session_token_12345"}
        )
        
        assert response.status_code == 401, f"Expected 401 for invalid token, got {response.status_code}"
        print("✓ /me with invalid token correctly returns 401")


class TestLogout:
    """POST /api/auth/logout - Clears session"""
    
    def test_logout_clears_session(self):
        """Logout should invalidate the session token"""
        # First login to get a token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123456"
        })
        assert login_response.status_code == 200
        session_token = login_response.json()["session_token"]
        
        # Verify token works before logout
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {session_token}"}
        )
        assert me_response.status_code == 200, "Token should be valid before logout"
        
        # Logout
        logout_response = requests.post(
            f"{BASE_URL}/api/auth/logout",
            headers={"Authorization": f"Bearer {session_token}"}
        )
        assert logout_response.status_code == 200
        data = logout_response.json()
        assert "logged out" in data.get("message", "").lower()
        print(f"✓ Logout successful: {data.get('message')}")
        
        # Verify token no longer works
        me_after_logout = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {session_token}"}
        )
        assert me_after_logout.status_code == 401, "Token should be invalid after logout"
        print("✓ Session invalidated after logout")


class TestFullAuthFlow:
    """End-to-end authentication flow test"""
    
    def test_register_login_me_logout_flow(self):
        """Complete auth flow: register → login → me → logout → me (should fail)"""
        unique_email = f"TEST_flow_{uuid.uuid4().hex[:8]}@example.com"
        
        # 1. Register
        register_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "flowtest123",
            "name": "Flow Test User"
        })
        assert register_resp.status_code == 200
        session_token = register_resp.json()["session_token"]
        print(f"✓ Step 1/4: Registered {unique_email}")
        
        # 2. Login with same credentials
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": unique_email,
            "password": "flowtest123"
        })
        assert login_resp.status_code == 200
        new_token = login_resp.json()["session_token"]
        assert new_token != session_token, "Login should create new session"
        print(f"✓ Step 2/4: Logged in, got new token")
        
        # 3. Get current user with new token
        me_resp = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        assert me_resp.status_code == 200
        user_data = me_resp.json()
        assert user_data["email"] == unique_email
        print(f"✓ Step 3/4: /me returns correct user data")
        
        # 4. Logout and verify session cleared
        logout_resp = requests.post(
            f"{BASE_URL}/api/auth/logout",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        assert logout_resp.status_code == 200
        
        # 5. Verify token no longer works
        me_after = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        assert me_after.status_code == 401
        print(f"✓ Step 4/4: Logged out, session invalidated")
        
        print("✓ Full auth flow completed successfully")


# Cleanup test users created during tests
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_users():
    """Cleanup: delete TEST_ prefixed users after all tests"""
    yield
    # Note: In production, would delete test users here
    # For now, they stay in DB but have unique emails
    print("\n[Cleanup] Test users with TEST_ prefix created during this run remain in DB")
