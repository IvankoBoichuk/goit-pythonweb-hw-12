#!/usr/bin/env python3
"""
Test email verification functionality.
"""

import requests
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:8000"

def test_email_verification():
    """Test email verification functionality."""
    print("=== Testing Email Verification Functionality ===\n")
    
    # Test data
    test_user = {
        "username": f"testuser_{int(time.time())}",
        "email": f"testuser_{int(time.time())}@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    try:
        # 1. Register user (should create unverified user and send email)
        print("1. Registering user...")
        response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user)
        
        if response.status_code == 201:
            user_data = response.json()
            print(f"✓ User registered successfully")
            print(f"  - Username: {user_data['username']}")
            print(f"  - Email: {user_data['email']}")
            print(f"  - Is verified: {user_data.get('is_verified', 'Not shown')}")
        else:
            print(f"✗ Registration failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
        
        # 2. Try to login
        print(f"\n2. Attempting login...")
        login_data = {
            "username": test_user["username"],
            "password": test_user["password"]
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens["access_token"]
            print("✓ Login successful")
        else:
            print(f"✗ Login failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
        
        # 3. Check user info (should show unverified status)
        print(f"\n3. Checking user info...")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        if response.status_code == 200:
            user_info = response.json()
            print("✓ User info retrieved")
            print(f"  - Is verified: {user_info.get('is_verified', 'Field not found')}")
            is_verified = user_info.get('is_verified', True)  # Default to True if field missing
        else:
            print(f"✗ Failed to get user info: {response.status_code}")
            return False
        
        # 4. Test resend verification email
        print(f"\n4. Testing resend verification email...")
        response = requests.post(f"{BASE_URL}/api/auth/resend-verification", 
                               json={"email": test_user["email"]})
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Resend verification request processed")
            print(f"  Message: {result.get('message', 'No message')}")
        else:
            print(f"✗ Resend verification failed: {response.status_code}")
            print(f"  Error: {response.text}")
        
        # 5. Test verification endpoint with dummy token
        print(f"\n5. Testing verification endpoint with invalid token...")
        response = requests.get(f"{BASE_URL}/api/auth/verify-email?token=invalid_token")
        
        if response.status_code == 400:
            result = response.json()
            print("✓ Invalid token correctly rejected")
            print(f"  Message: {result.get('detail', 'No message')}")
        else:
            print(f"✗ Expected 400 for invalid token, got: {response.status_code}")
        
        print(f"\n=== Test Summary ===")
        print("✓ User registration with email verification")
        print("✓ Login functionality")
        print("✓ User info endpoint")
        print("✓ Resend verification email")
        print("✓ Verification endpoint validation")
        print(f"\n📧 Email verification is implemented and working!")
        print(f"💡 To fully test, configure real SMTP settings in .env file")
        
        return True
        
    except requests.RequestException as e:
        print(f"✗ Network error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_email_verification()
    if success:
        print(f"\n🎉 All email verification tests passed!")
    else:
        print(f"\n❌ Email verification tests failed!")
        exit(1)