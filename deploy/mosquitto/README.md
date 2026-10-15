# OmniNode Mosquitto Deployment Guidelines

## Security Requirements
- All connections require mutual TLS (mTLS) with TLS 1.3 (`tls_version tlsv1.3`, `require_certificate true`).
- Client certificate common names / usernames are strictly mapped via `use_identity_as_username true`.
- Ports: `8883` for standard MQTT over TLS, `8443` for MQTT over Secure WebSockets (WSS).
- NO sensitive keys, `.env`, tokens or passwords are tracked in this repository.