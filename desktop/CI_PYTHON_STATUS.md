# Prerequisiti dei test gateway

[Stato corrente](../docs/CURRENT_STATUS.md). La correzione e pubblicata in f8e7500fd52863b998b187285a832b17c2b129f2; b669ec4 ha lo stesso messaggio e non e una nuova funzionalita. Alla baseline entrambi i job Python erano success.

Il workflow storico installava requirements.txt senza Playwright/Chromium e plugin asyncio richiesti dai test. Ora ci.yml e recovery-validation.yml condividono node1-gateway/requirements-test.txt e installano Chromium. requirements.txt di runtime non e stato modificato; gli intervalli test non costituiscono un lock completo.

I blob modificati verificati erano ci.yml 4f78267f348a6c59765b5182d8df646fe1eb59b4 e recovery-validation.yml 8ddb8169b8a6b67c97dca1759465f8ed25b2459b. Job Go e security scan erano invariati. Success di pytest non dimostra una chat web o un deploy, e non installa nulla sul PC dell'utente.
