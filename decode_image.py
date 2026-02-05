import json
import base64
import os
import sys

def decode_and_save_image(json_payload_str):
    try:
        payload = json.loads(json_payload_str)
        
        dev_mac = payload['values']['devMac'].replace(':', '-')
        timestamp = payload['ts']
        snap_type = payload['values']['snapType']
        base64_image = payload['values']['image']

        # Remove the data URL prefix
        if base64_image.startswith("data:image/jpeg;base64,"):
            base64_image = base64_image.split("data:image/jpeg;base64,")[1]
        
        # Decode the base64 string
        image_data = base64.b64decode(base64_image)

        # Create filename
        filename = f"snapshot_{dev_mac}_{timestamp}_{snap_type}.jpeg"
        filepath = os.path.join("uploads", filename)

        # Ensure the uploads directory exists
        os.makedirs("uploads", exist_ok=True)

        # Save the image
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        print(f"Image saved to {filepath}")
        return filepath
    except Exception as e:
        print(f"Error processing image: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_str = sys.argv[1]
        decode_and_save_image(json_str)
    else:
        print("Usage: python script.py <json_payload_string>", file=sys.stderr)
        sys.exit(1)
