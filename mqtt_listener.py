import paho.mqtt.client as mqtt
import json
import os
import subprocess
from dotenv import load_dotenv

# Load configuration
load_dotenv(".env.local")

MQTT_BROKER = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USERNAME")
MQTT_PASS = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC = "v1/devices/me/telemetry" # Standard topic for these types of sensing cameras

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"✅ Connected to MQTT Broker at {MQTT_BROKER}", flush=True)
        client.subscribe(MQTT_TOPIC)
        print(f"📡 Subscribed to topic: {MQTT_TOPIC}", flush=True)
    else:
        print(f"❌ Connection failed with code {rc}", flush=True)

def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode()
        print(f"📩 Received message on {msg.topic}", flush=True)
        
        # Call the existing decoding script
        result = subprocess.run(
            ["/home/ogema/MeterReading/venv/bin/python3", "decode_image.py", payload_str],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully processed message: {result.stdout.strip()}", flush=True)
            if result.stderr:
                print(f"⚠️ Warnings: {result.stderr.strip()}", flush=True)
        else:
            print(f"❌ Error processing message: {result.stderr.strip()}", flush=True)
            
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}", flush=True)

def run_listener():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    
    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"🚀 Starting MQTT Listener (Broker: {MQTT_BROKER}:{MQTT_PORT})...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    run_listener()
