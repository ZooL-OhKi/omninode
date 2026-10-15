#!/usr/bin/env bash
# OmniNode Healthcheck Script
curl -sf http://localhost:8000/api/v1/fleet/health || exit 1