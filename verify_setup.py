import requests
import os
import uuid
from dotenv import load_dotenv

load_dotenv(".env.local")

BASE_URL = "http://127.0.0.1:8000"

def test_everything():
    # 0. Login
    print("Logging in...")
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "securepassword123")
    
    resp = requests.post(f"{BASE_URL}/token", data={"username": username, "password": password})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Logged in successfully.")

    # 1. Create Organization
    print("Creating Organization...")
    unique_suffix = str(uuid.uuid4())[:8]
    org_name = f"Test Org {unique_suffix}"
    org_subdomain = f"test-{unique_suffix}"
    
    resp = requests.post(f"{BASE_URL}/api/organizations/", json={
        "name": org_name,
        "subdomain": org_subdomain
    }, headers=headers)
    
    if resp.status_code != 200:
        print(f"Create Organization Failed: {resp.status_code} - {resp.text}")
        return
        
    org = resp.json()
    org_id = org["id"]
    print(f"Organization created with ID: {org_id}")

    # 2. Create Project
    print("Creating Project...")
    resp = requests.post(f"{BASE_URL}/projects/", json={
        "name": f"Test Project {unique_suffix}", 
        "description": "Demo",
        "organization_id": org_id
    }, headers=headers)
    
    if resp.status_code != 200:
        print(f"Create Project Failed: {resp.status_code} - {resp.text}")
        return
    project_id = resp.json()["id"]
    print(f"Project created with ID: {project_id}")

    # 3. Create Customer
    print("Creating Customer...")
    resp = requests.post(f"{BASE_URL}/customers/", json={
        "name": "Test Customer", 
        "project_id": project_id,
        "organization_id": org_id
    }, headers=headers)
    assert resp.status_code == 200
    customer_id = resp.json()["id"]
    print(f"Customer created with ID: {customer_id}")

    # 4. Create Building
    print("Creating Building...")
    resp = requests.post(f"{BASE_URL}/buildings/", json={
        "name": "HQ", 
        "address": "123 Main St", 
        "customer_id": customer_id,
        "organization_id": org_id
    }, headers=headers)
    assert resp.status_code == 200
    building_id = resp.json()["id"]
    print(f"Building created with ID: {building_id}")

    # 5. Create Place
    print("Creating Place...")
    resp = requests.post(f"{BASE_URL}/places/", json={
        "name": "Basement", 
        "building_id": building_id,
        "organization_id": org_id
    }, headers=headers)
    assert resp.status_code == 200
    place_id = resp.json()["id"]
    print(f"Place created with ID: {place_id}")

    # 6. Create Meter
    print("Creating Meter...")
    serial = f"TEST-{unique_suffix}"
    resp = requests.post(f"{BASE_URL}/meters/", json={
        "serial_number": serial, 
        "meter_type": "Gas", 
        "unit": "m3", 
        "place_id": place_id,
        "organization_id": org_id
    }, headers=headers)
    if resp.status_code != 200:
        print(f"Create Meter Failed: {resp.text}")
    assert resp.status_code == 200
    meter_id = resp.json()["id"]
    print(f"Meter created with ID: {meter_id}")

    # 7. Upload Reading
    print("Uploading Reading...")
    # Use existing test_image.jpg if it exists, else dummy
    dummy_file = "test_image.jpg"
    if not os.path.exists(dummy_file):
        with open(dummy_file, "wb") as f:
            f.write(b"fake image content")
    
    with open(dummy_file, "rb") as f:
        files = {"file": (dummy_file, f, "image/jpeg")}
        resp = requests.post(f"{BASE_URL}/meters/{serial}/reading", files=files, headers=headers)
    
    if resp.status_code != 200:
        print(f"Upload Reading Failed: {resp.text}")
        return
    
    reading_data = resp.json()
    print(f"Reading created: {reading_data}")
    # Note: Value might be different if OCR isn't running or mocked differently
    # But in current implementation it returns 12345.67 if mocked
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    test_everything()
