"""Test script for password reset functionality"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api"


def register_user(username: str, email: str, password: str) -> Dict[str, Any]:
    """Register a new user for testing"""
    data = {"username": username, "email": email, "password": password}
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    return response.json(), response.status_code


def login_user(username: str, password: str) -> str:
    """Login and get access token"""
    data = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/auth/login", data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def forgot_password(email: str) -> Dict[str, Any]:
    """Request password reset"""
    data = {"email": email}
    response = requests.post(f"{BASE_URL}/auth/forgot-password", json=data)
    return response.json(), response.status_code


def reset_password(token: str, new_password: str) -> Dict[str, Any]:
    """Reset password with token"""
    data = {"token": token, "new_password": new_password}
    response = requests.post(f"{BASE_URL}/auth/reset-password", json=data)
    return response.json(), response.status_code


def get_cache_stats(token: str) -> Dict[str, Any]:
    """Get cache statistics"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/cache/stats", headers=headers)
    return response.json(), response.status_code


def test_password_reset():
    """Main test function for password reset functionality"""
    print("🔐 Testing Password Reset Functionality\n")

    # Test user details
    test_email = "resettest@example.com"
    test_username = "resettest"
    original_password = "originalpass123"
    new_password = "newpass123"

    # Step 1: Register test user
    print("1. Registering test user...")
    user_response, status = register_user(test_username, test_email, original_password)
    if status == 201:
        print("✅ User registered successfully")
    elif status == 409:
        print("ℹ️  User already exists, continuing with test")
    else:
        print(f"❌ Registration failed: {user_response}")
        return

    # Step 2: Test initial login
    print("\n2. Testing original login...")
    token = login_user(test_username, original_password)
    if token:
        print("✅ Original login successful")
    else:
        print("❌ Original login failed")
        return

    # Step 3: Test password reset request
    print("\n3. Requesting password reset...")
    reset_response, status = forgot_password(test_email)
    if status == 200:
        print(f"✅ Password reset requested: {reset_response.get('message')}")
    else:
        print(f"❌ Password reset request failed: {reset_response}")
        return

    # Step 4: Test rate limiting (multiple requests)
    print("\n4. Testing rate limiting...")
    for i in range(4):  # Should hit rate limit after 3 requests
        response, status = forgot_password(test_email)
        print(f"   Request {i+1}: {status} - {response.get('message', 'No message')}")
        time.sleep(0.5)  # Small delay between requests

    # Step 5: Check cache stats
    print("\n5. Checking cache statistics...")
    cache_stats, status = get_cache_stats(token)
    if status == 200:
        print(f"   📈 Cache enabled: {cache_stats.get('enabled', False)}")
        if cache_stats.get("enabled"):
            print(f"   📊 Cache hits: {cache_stats.get('keyspace_hits', 'N/A')}")
            print(f"   📊 Cache misses: {cache_stats.get('keyspace_misses', 'N/A')}")

    # Step 6: Simulate invalid token reset
    print("\n6. Testing invalid token...")
    invalid_token = "invalid-token-12345"
    reset_response, status = reset_password(invalid_token, new_password)
    if status == 400:
        print(f"✅ Invalid token correctly rejected: {reset_response.get('detail')}")
    else:
        print(f"❌ Invalid token handling failed: {reset_response}")

    # Step 7: Test weak password
    print("\n7. Testing weak password validation...")
    # Note: We can't easily get a real token without email access,
    # but we can test the validation with a dummy token
    weak_password = "123"
    reset_response, status = reset_password("dummy-token", weak_password)
    print(f"   Weak password response: {status} - {reset_response}")

    # Step 8: Test that original password still works
    print("\n8. Verifying original password still works...")
    token_check = login_user(test_username, original_password)
    if token_check:
        print("✅ Original password still works (as expected without valid reset)")
    else:
        print("⚠️  Original password no longer works")

    print("\n🎉 Password reset testing completed!")
    print("\nNote: To complete the full test, you would need:")
    print("- Access to the email to get the actual reset token")
    print("- Or check the application logs for the generated token")
    print("- Or implement a test endpoint that returns tokens (for testing only)")


def test_password_reset_security():
    """Test security aspects of password reset"""
    print("\n🛡️  Testing Password Reset Security Features\n")

    test_emails = ["nonexistent@example.com", "test@example.com", "admin@example.com"]

    print("Testing response consistency (timing attack prevention):")
    for email in test_emails:
        start_time = time.time()
        response, status = forgot_password(email)
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # Convert to ms
        print(
            f"   {email}: {status} - {response_time:.2f}ms - {response.get('message')}"
        )

    print("\n✅ All responses should be similar to prevent email enumeration")


if __name__ == "__main__":
    test_password_reset()
    test_password_reset_security()
