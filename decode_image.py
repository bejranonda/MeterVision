import json
import base64
import os
import sys
import requests
from datetime import datetime

import time

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
            response = requests.post("http://localhost:8000/api/logs/", json=log_data)
            if response.status_code == 201:
                return # Success
            else:
                print(f"Failed to log message (attempt {attempt + 1}/{max_retries}): {response.text}", file=sys.stderr)
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
        reading_data = {"value": "12345.67", "confidence": 0.95, "error": None}
        log_details["meter_reading"] = reading_data
        log_message("INFO", f"Meter reading processed for {dev_mac_raw}.", log_details)

        return filepath

    except Exception as e:
        error_message = f"Error processing image: {e}"
        print(error_message, file=sys.stderr)
        log_message("ERROR", error_message, {"payload": json_payload_str})
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_str = sys.argv[1]
        decode_and_save_image(json_str)
    else:
        print("Usage: python script.py <json_payload_string>", file=sys.stderr)
        sys.exit(1)
