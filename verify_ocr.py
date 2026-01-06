from app.services.ocr import SmartMeterReader
from dotenv import load_dotenv
import os

load_dotenv(".env.local")

# Ensure API key is present
print(f"Checking API Key: {'Found' if os.getenv('GEMINI_API_KEY') else 'Not Found'}")

reader = SmartMeterReader()
image_path = "test_image.jpg"

if not os.path.exists(image_path):
    print(f"Error: {image_path} does not exist.")
else:
    print(f"Analyzing {image_path}...")
    result = reader.read_meter(image_path)
    print(f"Final Result: {result}")
