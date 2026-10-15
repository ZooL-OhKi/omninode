import pytest
from diagnostics import TelemetryEvent, AnomalyDetector

def test_telemetry_event_creation():
    ev = TelemetryEvent(node_id="node-1", metric="task_latency_seconds", value=15.5)
    assert ev.schema_version == 1
    assert ev.status == "ok"
    assert ev.value == 15.5

def test_detector_latency_anomaly():
    detector = AnomalyDetector()
    ev = TelemetryEvent(node_id="node-1", metric="task_latency_seconds", value=75.0, goal_id="g-1")
    report = detector.evaluate_telemetry(ev)
    assert report is not None
    assert report.severity == "warning"
    assert report.recommended_action == "degrade"
    assert report.auto_remediation_allowed is True

def test_detector_consecutive_failures():
    detector = AnomalyDetector()
    ev = TelemetryEvent(node_id="node-1", metric="consecutive_failures", value=3.0)
    report = detector.evaluate_telemetry(ev)
    assert report is not None
    assert report.severity == "critical"
    assert report.recommended_action == "quarantine"