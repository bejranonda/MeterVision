#!/bin/bash

# Generate CA Key and Certificate
openssl genrsa -out ca.key 2048
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out ca.crt -subj "/CN=MeterVision CA"

# Generate Server Key and Certificate Signing Request (CSR)
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=localhost"

# Sign the Server Certificate with the CA
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365 -sha256

# Fix permissions for Mosquitto
chmod 644 ca.crt server.crt
chmod 600 ca.key server.key
