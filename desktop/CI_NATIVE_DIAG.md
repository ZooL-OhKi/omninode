# Native fixture CI reproducibility

At commit 78c991e26517497ca81ff12beaaad34b6ed1fe44, GitHub reported native-browser failure while extension and Windows/Linux desktop unit jobs passed. The separate Python Gateway & Scripts Pytest job also remained failed. Full remote logs were not retrievable using the available connector/fetch tools, so no root cause is claimed.

The assistant's actually verified fixture environment was Python 3.12.8, Playwright 1.51.0, Pillow 12.2.0 and Chromium 134.0.6998.35. The isolated native-browser CI job now pins the two Python dependencies to those verified versions; production desktop requirements and the user's browser are NOT downgraded. This old bundled Chromium is for synthetic tests only: never use it for live browsing, account logins or untrusted web content.

The temporary Linux fixture launcher now explicitly supplies the interpreter's configured shared-library directory and captures fixture stderr for failure diagnostics. This is a portability precaution, not proof that shared-library loading caused the original CI failure. Two actual local Chromium native messaging probes passed (direct interpreter and portable launcher). The updated full synthetic-image native browser test then passed as a separate unittest process with the pinned dependencies in the assistant environment.

A new CI run is required to verify the remote result. This patch does not repair or certify the separate legacy Python gateway job, does not test Windows native consent or real desktop input, and does not complete the chat adapter. No user's screen, account or local repository was accessed or updated by this change.
