# Phase 17 — Continue here

Checkpoint: 2026-10-15 09:46 CEST. This document is a handoff, not production certification. Revalidate all live state before changing anything.

## Read first

Read docs/PHASE_17_ORACLE_HANDOFF.md on branch docs/phase-17-oracle-handoff (original handoff commit 5c9c962214463a7f11c37bf2b52459470eb9a605). It records Oracle setup, Python tests, the Go resource incident, reboot, and known integration blockers. This checkpoint supplements rather than replaces it.

Repository: ZooL-OhKi/omninode. Tracking issue: #4. PR #3 was squash-merged; main at that earlier verification was 1b7b97f3e931635bd7fa7e767a0db31dcf7b12ee. Verify current origin/main, issue and PR state; local main may be stale. Do not reset, force-push or overwrite other agents' work.

## Latest implementation branch evidence

Branch: feature/phase-17-mqtt-integration-fix. Last verified commit: e57a54db31b2a7bd5e215930f36b81b7553065c1.

Remote commit history verified through GitHub:
- a3a361325c4e29e922b9b44dd547b8e461c7f2e6: broker configuration and deployment files.
- 41fed3926cc71342596019825c2d6fb9cbca53b3: ACL v1 changes.
- 7ba503f0fe9155986f809a0d47b1e9b1a0bb28fb: resiliency guidelines.
- 678cb91eb0ff89123bcedd25565fea0062b4a7d3: adds scripts/oracle_bootstrap.py, 39 lines.
- e57a54db31b2a7bd5e215930f36b81b7553065c1: adds docs/LIVE_PILOT_CERTIFICATION.md, 72 lines only; no application changes in this commit.

Operator-provided Windows PowerShell output at 678cb91 showed main...feature diff of seven files, 126 additions and six deletions: deploy/mosquitto/README.md, acl.conf, mosquitto.conf, deploy/systemd gateway and worker units, docs/LIVE_PILOT_MILESTONE_2_RESILIENCY.md, scripts/oracle_bootstrap.py. This was a cumulative comparison against local main, not the stats of the last commit and not an independently verified comparison against current origin/main. Recompute after fetching.

The full contents of oracle_bootstrap.py and LIVE_PILOT_CERTIFICATION.md were NOT reviewed during this checkpoint. Their filenames and commit messages do not prove safety, idempotence or certification. Inspect their actual contents before judging them.

## Tests and operational state

Operator supplied output from A:\omninode\node1-gateway: Python 3.14.7, .\venv\Scripts\python.exe -m pytest -q, 118 passed, 2 skipped, 51 warnings in 26.50s, LASTEXITCODE 0. This is local Windows evidence, not an independent rerun. Obtain skipped test identities/reasons with pytest -ra before comparing with Linux.

Earlier Oracle Linux session: 120 passed, four warnings after installing Playwright and Chromium headless shell. Different environments/results must not be treated as identical coverage. Audit signing key was ephemeral in test/development; provision persistent production key outside Git only after reviewing code requirements.

Gemini reported bootstrap written/static-checked and NOT executed on Oracle. No subsequent Oracle deployment was verified. No live broker mTLS/ACL/dispatch/reconnect proof is available. Go vet/test were not completed on the micro VM.

Oracle region eu-milan-1. Orchestrator public IP observed 129.152.6.17, private 10.0.0.237; archivist public IP observed 92.4.172.19, private 10.0.0.226. Revalidate addresses. SSH user ubuntu. Both observed E2.1.Micro with 1 GB RAM, no swap. Never run heavy Go builds there: an earlier build plus unattended upgrades caused severe I/O pressure. After orderly reboot: kernel 7.0.0-1010-oracle, zero failed systemd units; updates remained pending.

Clone/venv on orchestrator: /home/ubuntu/omninode and node1-gateway/venv. Playwright browser cache belongs to ubuntu; do not presume service user access. Original handoff contains route/security details. Do not expose new public ports or request private SSH keys. GitHub access does not imply SSH access. Archivist software state is not inspected.

## Work still required

Treat the original handoff's code findings as observations to revalidate against current files, not proof that every current file is unchanged.

1. Inspect gateway main.py, mqtt_service.py, mqtt_topics.py, task/envelope/control modules, autonomy_app.py, work_loop.py and autonomy_core.py; inspect Go main.go, mqtt_client.go, heartbeat.go and actual handlers; inspect broker config, ACL, systemd units, bootstrap and CI. Trace real entrypoints and calls.
2. Implement fail-closed TLS for every MQTT path: trusted CA, client certificate/key, hostname verification, checked certificate-loading errors, no insecure/plaintext fallback. If TLS 1.3-only is required, enforce and test both bounds; do not infer exclusivity from a single config directive.
3. Unify v1 topics and existing task/envelope contracts with broker ACL identities. Implement actual task subscription, heartbeat invocation, structured JSON response, reconnect/resubscription and MQTT readiness separate from HTTP. Preserve existing validation, policy, lease and idempotency controls; no arbitrary shell shortcuts.
4. Align systemd units with actual executable entrypoints, environment variables, identities, ports and paths. Earlier worker flags were not read by observed main, node2/9001 mismatched ACL/broker, and gateway used main.py instead of autonomy entrypoint. Revalidate and fix. Missing credentials/configuration must fail clearly. Keep API localhost initially.
5. Review and harden bootstrap BEFORE running it: idempotence, preflight, protected permissions, existing key preservation, backup/rollback, no unintended service activation or firewall changes. Test in disposable environment, not production. Do not claim a 39-line script is safe without review.
6. Add reproducible dependencies and tests: explain skipped tests, test TLS and topics, JSON and reconnect; run Go vet/test/build off the micro VM with compatible target. Run real-broker integration for valid client, missing/untrusted client cert, wrong hostname, ACL cross-talk denial, task/response, heartbeat, reconnect and duplicate handling. Distinguish mocks from live evidence.
7. Commit code and tests in reviewable increments; provide full SHA, diff, commands, output, exit codes and unresolved risks. Draft PR only with required approval, no merge or Oracle rollout without explicit approval. Review against current origin/main, not stale local main.
8. Only after code review and explicit deployment approval: staged Oracle provisioning with rollback and health checks, inspect archivist before assigning duties, then record actual operational evidence. Do not declare production-ready early.

No GitHub issue consumer or automatic remote executor was demonstrated. Creating issue #4 does not launch work. Desired always-on autonomy is a goal, not established capability.

## Prompt for a fresh AI

You are the implementation engineer taking over ZooL-OhKi/omninode Phase 17 with no prior conversation. Read this file and PHASE_17_ORACLE_HANDOFF.md on docs/phase-17-oracle-handoff completely. Fetch and inspect current origin/main and feature/phase-17-mqtt-integration-fix; last verified implementation SHA is e57a54db31b2a7bd5e215930f36b81b7553065c1. Preserve other agents' work. Read issue #4, actual code, bootstrap, deployment files and tests. Do not rebuild the project from scratch: reconstruct context and complete the missing implementation.

Your deliverable is working reviewed application code and tests, not another certification document. First publish a concise findings/plan with concrete files, then implement the smallest coherent patches for fail-closed MQTT mTLS, v1 contracts, real worker subscription/heartbeat/response, reconnect/readiness, matching systemd configuration, and safe idempotent bootstrap. Reuse existing policy, task validation, lease and idempotence controls. Explain the two Windows skipped tests and run Go checks in a suitable non-micro environment. Separate static, unit, integration and live evidence.

Do not execute Oracle bootstrap, change firewall/network, rotate credentials, merge, force-push or push to main without required explicit approval. Do not ask for private keys or commit secrets. Keep APIs private and ACL restrictive. If you lack execution access, say exactly what is missing; never invent tests or deployments. Seek narrowly scoped approval only when necessary and minimize manual operator work. End each implementation increment with commit SHA, exact diff scope, test commands/results, remaining blockers and next action. Continue implementation until acceptance criteria are met or a concrete permission/access blocker is reached.
