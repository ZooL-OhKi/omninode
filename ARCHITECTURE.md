# Omninode architecture

## Operating model

An autonomous AI resident runs continuously on an Oracle node. The resident uses local compute, memory, disk, processes, files, browser sessions, and network capabilities assigned by policy. The system is designed for the AI to perform complete work loops: understand, plan, act, inspect, correct, and report.

## Components

```text
Browser client
      |
      v
MCP/Go client (omniclient)
      |
      v
Authenticated FastAPI gateway (node1-gateway)
      |
      v
MQTT broker: task request/reply
      |
      v
Resident worker on Oracle node
      |
      +-- workspace and files
      +-- approved local processes
      +-- browser runtime
      +-- controlled tools
```

## Request flow

1. A client sends an authenticated request to the gateway.
2. The gateway validates the request and selects an online node.
3. The dispatcher creates a correlation identifier and registers a pending task.
4. The request is published over MQTT.
5. The worker validates policy, executes the task, and publishes a response.
6. The gateway matches the response to the pending task.
7. The task is removed from the pending map in all completion and failure paths.
8. The HTTP/MCP client receives a structured result or error.

## Correlation and reliability

Every task needs a unique task identifier. The implementation must safely handle concurrent tasks, duplicate responses, late responses after timeout, broker reconnects, worker restarts, malformed payloads, and unavailable nodes. MQTT 5 response-topic and correlation-data properties may be used where supported, but the application-level contract must remain explicit and versioned.

## Filesystem and workspace

The resident AI should be able to work with files, but access must be scoped to configured workspaces. Path traversal, arbitrary host root access, secret directories, device files, and control sockets must be denied by policy. File changes should be auditable and recoverable where possible.

## Browser runtime

The initial browser runtime should use standard Chromium, Playwright and/or CDP, separate profiles, protected CDP endpoints, domain allowlists, and controlled artifact transfer. A custom Chromium fork is not part of the current plan. CAPTCHA and MFA flows must support pause and human handoff rather than bypass.

## Future execution services

Sandboxed code execution and system operations must run behind capability checks, resource budgets, isolation boundaries, and audit events. `run_sandbox_code` is a future feature, not a justification for unrestricted shell access.
