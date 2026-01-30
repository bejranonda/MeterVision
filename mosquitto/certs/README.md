# Mosquitto Certificates

This directory is intended for MQTTS certificates. 
Private keys (`*.key`) and serial files (`*.srl`) are ignored by git for security.

To generate new certificates for local development:

```bash
./generate_certs.sh
```

Ensure that the `CN` (Common Name) in the server certificate matches your server's hostname if you are connecting from external clients.
