# Shared gateway test prerequisites

Verified before this patch: at 89ec3642e8d2c4dd315a853aba096c5481f3f694 the native-browser integration, Windows/Linux desktop unit jobs, extension, Go and secret scan were successful. The legacy Python Gateway & Scripts Pytest job remained failed while Recovery's python job passed.

Source inspection proved that test_browser_runtime.py imports Playwright and launches Chromium; the legacy job installed only requirements.txt, which did not declare Playwright or pytest-asyncio and did not install Chromium. Recovery already installed these prerequisites separately. Full remote logs were unavailable, so this is a proven configuration defect, not a claim that it is the only possible failure.

Both gateway CI paths now use node1-gateway/requirements-test.txt and install Chromium explicitly. Runtime requirements.txt is unchanged. Version ranges are declared, not a fully locked environment. Nothing is installed globally on the user's PC. No gateway code, TLS, ACL, shell policy, test assertions or existing Go/security-scan jobs are changed.

Validation in assistant environment: original workflow blob hashes matched the remote files exactly; updated YAML parsed; embedded Python hygiene script parsed; secret-scan and Go job structures were unchanged. Expected updated Git blob hashes: ci.yml 4f78267f348a6c59765b5182d8df646fe1eb59b4; recovery-validation.yml 8ddb8169b8a6b67c97dca1759465f8ed25b2459b. Full pytest execution remains for CI to verify. Desktop operation from the web chat remains incomplete; no Windows copy or VPS was updated or deployed.
