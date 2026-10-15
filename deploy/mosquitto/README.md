# OmniNode Mosquitto Deployment Guidelines & ACL Verification

## v1 Topic Contract & Identity-Based ACLs
- Gateway (`gateway`) has write access to tasks and control channels, and read access to responses, heartbeats, and ACKs across all nodes (`+`).
- Workers (`worker-1`, `worker-2`) are strictly sandboxed: they can only read and write to their own designated node path (`omninode/v1/nodes/{node_id}/...`). Cross-talk or unauthorized publishing is rejected by Mosquitto ACL engine.

## Security Constraints
- Mutual TLS (mTLS) with TLS 1.3 (`tls_version tlsv1.3`, `require_certificate true`).
- Identity extraction via `use_identity_as_username true`.
- NO secrets, passwords, or private keys stored in Git.