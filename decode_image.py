import json
import base64
import os
import sys
import requests
from datetime import datetime

import time
from dotenv import load_dotenv

# Load environment variables explicitly to ensure admin creds are available
load_dotenv("/home/ogema/MeterReading/.env.local")

def log_message(level, message, details):
    """Sends a log message to the logging API endpoint with a retry mechanism."""
    log_data = {
        "level": level,
        "message": message,
        "details": details
    }
    
    max_retries = 3
    retry_delay = 2 # seconds

    for attempt in range(max_retries):
        try:
            # Use 127.0.0.1 to avoid ipv6/ipv4 resolution issues in some environments
            response = requests.post("http://127.0.0.1:8000/api/logs/", json=log_data, timeout=5)
            if response.status_code == 201:
                return # Success
            else:
                print(f"Failed to log message (status {response.status_code}): {response.text}", file=sys.stderr)
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to logging service (attempt {attempt + 1}/{max_retries}): {e}", file=sys.stderr)
        
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    
    print("Giving up on logging message after multiple retries.", file=sys.stderr)

def decode_and_save_image(json_payload_str):
    try:
        payload = json.loads(json_payload_str)
        
        dev_mac_raw = payload['values']['devMac']
        dev_mac_sanitized = dev_mac_raw.replace(':', '-')
        timestamp = payload['ts']
        snap_type = payload['values']['snapType']
        base64_image = payload['values']['image']
        
        # Convert timestamp to a readable datetime string for the filename
        capture_time = datetime.fromtimestamp(timestamp / 1000)
        time_str = capture_time.strftime('%Y%m%d_%H%M%S')

        # Remove the data URL prefix
        if base64_image.startswith("data:image/jpeg;base64,"):
            base64_image = base64_image.split("data:image/jpeg;base64,")[1]
        
        # Decode the base64 string
        image_data = base64.b64decode(base64_image)

        # Create device-specific directory
        device_dir = os.path.join("uploads", dev_mac_sanitized)
        os.makedirs(device_dir, exist_ok=True)

        # Create filename
        filename = f"{time_str}_{snap_type}.jpeg"
        filepath = os.path.join(device_dir, filename)

        # Save the image
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        print(f"Image saved to {filepath}")
        
        # Log success
        log_details = {
            "device_mac": dev_mac_raw,
            "filepath": filepath,
            "capture_time": capture_time.isoformat(),
            "snap_type": snap_type
        }
        log_message("INFO", "Successfully converted MQTT message to photo.", log_details)

        # Simulate meter reading for logging purposes
        # In a real scenario, this would call the OCR service
        # For this prototype, we simulate a reading value incrementing based on time or random
        import random
        mock_value = 12345.0 + random.uniform(0, 100)
        reading_data = {"value": round(mock_value, 2), "confidence": 0.95, "error": None}
        
        # ACTUALLY SAVE THE READING VIA API
        # We assume the dev_mac_raw acts as the serial number for now, or mapped to one.
        # Ensure the meter exists first (optional, or relying on API to handle/error)
        try:
            # Post reading to API
            # Endpoint: /meters/{serial_number}/reading
            # We need to construct the reading payload
            api_reading_payload = {
                "value": reading_data["value"],
                "timestamp": capture_time.isoformat(),
                "image_path": f"/uploads/{dev_mac_sanitized}/{filename}"
            }
            
            # Authenticate
            token = get_auth_token()
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            # Using 127.0.0.1 for reliability
            read_res = requests.post(
                f"http://127.0.0.1:8000/meters/{dev_mac_raw}/reading_data", 
                json=api_reading_payload,
                headers=headers,
                timeout=5
            )
            if read_res.status_code == 200: # success for explicit data creation
                log_message("INFO", f"Reading saved for {dev_mac_raw}: {reading_data['value']}", {"api_response": read_res.json()})
            else:
                log_message("WARNING", f"Failed to save reading for {dev_mac_raw}", {"status": read_res.status_code, "text": read_res.text})
                
                # Auto-create meter if not exists (simple auto-provisioning logic)
                if read_res.status_code == 404 and token:
                    log_message("INFO", f"Meter {dev_mac_raw} not found. Attempting auto-provisioning.", {})
                    create_meter_payload = {
                        "serial_number": dev_mac_raw,
                        "meter_type": "Electricity", # Default
                        "unit": "kWh",
                        "organization_id": 1 # Default legacy org
                    }
                    create_res = requests.post(
                        "http://127.0.0.1:8000/meters/", 
                        json=create_meter_payload, 
                        headers=headers,
                        timeout=5
                    )
                    
                    log_message("INFO", f"Auto-provisioning status for {dev_mac_raw}: {create_res.status_code}", {"response": create_res.text})

                    if create_res.status_code in [200, 201]:
                         # Retry reading post
                         retry_res = requests.post(
                            f"http://127.0.0.1:8000/meters/{dev_mac_raw}/reading_data", 
                            json=api_reading_payload,
                            headers=headers,
                            timeout=5
                        )
                         if retry_res.status_code == 200:
                             log_message("INFO", f"Retry reading saved for {dev_mac_raw}: {reading_data['value']}", {"api_response": retry_res.json()})
                         else:
                             log_message("WARNING", f"Retry reading failed for {dev_mac_raw}", {"status": retry_res.status_code, "text": retry_res.text})
        except Exception as api_err:
             log_message("ERROR", f"API Error saving reading: {api_err}", {})

        log_details["meter_reading"] = reading_data
        log_message("INFO", f"Meter reading processed for {dev_mac_raw}.", log_details)

        return filepath

    except Exception as e:
        error_message = f"Error processing image: {e}"
        print(error_message, file=sys.stderr)
        log_message("ERROR", error_message, {"payload": json_payload_str})
        sys.exit(1)

def get_auth_token():
    """Authenticates as admin and returns the access token."""
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "securepassword123")
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/token",
            data={"username": username, "password": password},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"Auth failed: {response.text}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Auth error: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_str = sys.argv[1]
        
        # Decode and save image (this part was already working)
        filepath = decode_and_save_image(json_str)
        # Note: decode_and_save_image calls the API inside it now.
        # But we need to pass the token TO decode_and_save_image or have it call get_auth_token()
        
    else:
        print("Usage: python script.py <json_payload_string>", file=sys.stderr)
        sys.exit(1)
