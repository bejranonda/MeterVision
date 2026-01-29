#!/bin/sh

# Create password file from env vars if they exist
if [ ! -z "$MQTT_USERNAME" ] && [ ! -z "$MQTT_PASSWORD" ]; then
    echo "Creating password file for user: $MQTT_USERNAME"
    touch /mosquitto/config/passwd
    mosquitto_passwd -b /mosquitto/config/passwd "$MQTT_USERNAME" "$MQTT_PASSWORD"
else
    echo "MQTT_USERNAME or MQTT_PASSWORD not set, skipping password file creation."
fi

# Fix permissions
chown -R mosquitto:mosquitto /mosquitto/data
chown -R mosquitto:mosquitto /mosquitto/log

# Start Mosquitto
exec /usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf