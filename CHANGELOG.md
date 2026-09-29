# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- **Phase 1: Real local vertical slice** - Implementazione del ciclo di esecuzione autonomo locale.
  - `mqtt_service.py`: Aggiunto task handler per intercettare eventi `tasks` dal topic `omninode/nodes/node-local/tasks`.
  - `main.py`: Aggiunta logica di cablaggio e validazione per eseguire task `workspace.write` localmente tramite `LocalWorkspaceExecutor`.
  - Workspace temporaneo isolato configurato in `OMNINODE_WORKSPACE_ROOT` (default: temp directory).
  - Endpoint FastAPI `/workspace/write` aggiunto per debug diretto senza MQTT.

### Changed
- Il demone Python locale ora agisce come nodo esecutore, iscrivendosi al proprio topic MQTT `tasks` ed eseguendo in sicurezza l'operazione `workspace.write`.

### Security
- Principio del minimo privilegio: il nodo locale supporta esclusivamente `workspace.write`.
- Policy denial esplicito per capability non supportate.

## [0.0.1] - Initial Release
- Repository initialization.
- Basic MQTT service and gateway structure.
