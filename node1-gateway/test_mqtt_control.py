import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from mqtt_control import ControlCommandEnvelope, validate_command_for_state

def test_control_envelope_valid():
    future = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    env = ControlCommandEnvelope(
        expires_at=future,
        node_id="node-01",
        goal_id="goal-123",
        command="pause"
    )
    assert env.schema_version == 1
    assert env.command == "pause"
    assert env.is_expired() is False
    assert env.verify_identity("gateway") is True

def test_control_envelope_expired():
    past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    env = ControlCommandEnvelope(
        expires_at=past,
        node_id="node-01",
        goal_id="goal-123",
        command="pause"
    )
    assert env.is_expired() is True

def test_state_transition_matrix():
    assert validate_command_for_state("running", "pause") is True
    assert validate_command_for_state("running", "resume") is False
    assert validate_command_for_state("paused", "resume") is True
    assert validate_command_for_state("completed", "stop") is False