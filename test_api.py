"""
Test script for Organization Management API
Run this after starting the FastAPI server
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def print_response(response, description):
    """Helper function to print formatted response"""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}\n")
    return response.json() if response.status_code < 400 else None

def test_health_check():
    """Test health check endpoint"""
    response = requests.get(f"{BASE_URL}/")
    print_response(response, "Health Check")
    return response.status_code == 200

def test_create_organization():
    """Test creating an organization"""
    data = {
        "organization_name": "TestOrg",
        "email": "admin@testorg.com",
        "password": "TestPass123"
    }
    response = requests.post(f"{BASE_URL}/org/create", json=data)
    result = print_response(response, "Create Organization")
    return response.status_code == 201

def test_get_organization():
    """Test getting organization details"""
    response = requests.get(f"{BASE_URL}/org/get", params={"organization_name": "TestOrg"})
    print_response(response, "Get Organization")
    return response.status_code == 200

def test_admin_login():
    """Test admin login"""
    data = {
        "email": "admin@testorg.com",
        "password": "TestPass123"
    }
    response = requests.post(f"{BASE_URL}/admin/login", json=data)
    result = print_response(response, "Admin Login")
    if response.status_code == 200:
        return result.get("access_token")
    return None

def test_update_organization(token):
    """Test updating organization"""
    data = {
        "organization_name": "TestOrg",
        "new_organization_name": "TestOrgUpdated",
        "email": "admin@testorg.com",
        "password": "TestPass123"
    }
    response = requests.put(f"{BASE_URL}/org/update", json=data)
    print_response(response, "Update Organization")
    return response.status_code == 200

def test_delete_organization(token):
    """Test deleting organization"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {"organization_name": "TestOrgUpdated"}
    response = requests.delete(f"{BASE_URL}/org/delete", json=data, headers=headers)
    print_response(response, "Delete Organization")
    return response.status_code == 200

def test_duplicate_organization():
    """Test creating duplicate organization (should fail)"""
    data = {
        "organization_name": "TestOrg2",
        "email": "admin@testorg2.com",
        "password": "TestPass123"
    }
    # Create first time
    requests.post(f"{BASE_URL}/org/create", json=data)
    
    # Try to create again (should fail)
    response = requests.post(f"{BASE_URL}/org/create", json=data)
    print_response(response, "Create Duplicate Organization (Should Fail)")
    return response.status_code == 400

def test_invalid_login():
    """Test login with wrong password"""
    data = {
        "email": "admin@testorg2.com",
        "password": "WrongPassword"
    }
    response = requests.post(f"{BASE_URL}/admin/login", json=data)
    print_response(response, "Invalid Login (Should Fail)")
    return response.status_code == 401

def cleanup():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    try:
        # Login as admin@testorg2.com
        login_data = {
            "email": "admin@testorg2.com",
            "password": "TestPass123"
        }
        response = requests.post(f"{BASE_URL}/admin/login", json=login_data)
        if response.status_code == 200:
            token = response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Delete TestOrg2
            delete_data = {"organization_name": "TestOrg2"}
            requests.delete(f"{BASE_URL}/org/delete", json=delete_data, headers=headers)
            print("✅ Cleaned up TestOrg2")
    except:
        pass

def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "="*60)
    print("🚀 Starting API Tests")
    print("="*60)
    
    results = []
    
    # Test 1: Health Check
    results.append(("Health Check", test_health_check()))
    
    # Test 2: Create Organization
    results.append(("Create Organization", test_create_organization()))
    
    # Test 3: Get Organization
    results.append(("Get Organization", test_get_organization()))
    
    # Test 4: Admin Login
    token = test_admin_login()
    results.append(("Admin Login", token is not None))
    
    if token:
        # Test 5: Update Organization
        results.append(("Update Organization", test_update_organization(token)))
        
        # Need to login again after update to get new token
        login_data = {
            "email": "admin@testorg.com",
            "password": "TestPass123"
        }
        response = requests.post(f"{BASE_URL}/admin/login", json=login_data)
        if response.status_code == 200:
            token = response.json().get("access_token")
        
        # Test 6: Delete Organization
        results.append(("Delete Organization", test_delete_organization(token)))
    
    # Test 7: Duplicate Organization
    results.append(("Duplicate Organization", test_duplicate_organization()))
    
    # Test 8: Invalid Login
    results.append(("Invalid Login", test_invalid_login()))
    
    # Cleanup
    cleanup()
    
    # Print Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("🎉 All tests passed successfully!")
    else:
        print("⚠️ Some tests failed. Please check the output above.")

if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server.")
        print("Make sure the FastAPI server is running on http://localhost:8000")
        print("Run: uvicorn main:app --reload")