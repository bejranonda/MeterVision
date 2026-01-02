import requests
import os

BASE_URL = "http://127.0.0.1:8000"

def test_everything():
    # 1. Create Project
    print("Creating Project...")
    resp = requests.post(f"{BASE_URL}/projects/", json={"name": "Test Project", "description": "Demo"})
    assert resp.status_code == 200
    project_id = resp.json()["id"]
    print(f"Project created with ID: {project_id}")

    # 2. Create Customer
    print("Creating Customer...")
    resp = requests.post(f"{BASE_URL}/customers/", json={"name": "Test Customer", "project_id": project_id})
    assert resp.status_code == 200
    customer_id = resp.json()["id"]
    print(f"Customer created with ID: {customer_id}")

    # 3. Create Building
    print("Creating Building...")
    resp = requests.post(f"{BASE_URL}/buildings/", json={"name": "HQ", "address": "123 Main St", "customer_id": customer_id})
    assert resp.status_code == 200
    building_id = resp.json()["id"]
    print(f"Building created with ID: {building_id}")

    # 4. Create Place
    print("Creating Place...")
    resp = requests.post(f"{BASE_URL}/places/", json={"name": "Basement", "building_id": building_id})
    assert resp.status_code == 200
    place_id = resp.json()["id"]
    print(f"Place created with ID: {place_id}")

    # 5. Create Meter
    print("Creating Meter...")
    serial = "TEST-12345"
    resp = requests.post(f"{BASE_URL}/meters/", json={
        "serial_number": serial, 
        "meter_type": "Gas", 
        "unit": "m3", 
        "place_id": place_id
    })
    assert resp.status_code == 200
    meter_id = resp.json()["id"]
    print(f"Meter created with ID: {meter_id}")

    # 6. Upload Reading
    print("Uploading Reading...")
    # Create a dummy file
    dummy_file = "test_image.jpg"
    with open(dummy_file, "wb") as f:
        f.write(b"fake image content")
    
    with open(dummy_file, "rb") as f:
        files = {"file": (dummy_file, f, "image/jpeg")}
        resp = requests.post(f"{BASE_URL}/meters/{serial}/reading", files=files)
    
    # assert resp.status_code == 200
    if resp.status_code != 200:
        print(resp.text)
    
    reading_data = resp.json()
    print(f"Reading created: {reading_data}")
    assert reading_data["value"] == 12345.67
    assert reading_data["status"] == "Verified"

    print("ALL TESTS PASSED")

if __name__ == "__main__":
    test_everything()
