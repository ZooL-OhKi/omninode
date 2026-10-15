import pytest
from fleet_dashboard import FleetDashboardManager
from backup_manager import BackupManager

def test_fleet_dashboard_overview():
    dash = FleetDashboardManager()
    overview = dash.get_overview()
    assert overview.nodes_online > 0
    assert overview.health_score == 1.0

    health = dash.get_health()
    assert health["status"] == "healthy"

    dash.record_alert("warning", "High latency detected")
    alerts = dash.get_alerts()
    assert len(alerts) == 1

def test_backup_and_restore(tmp_path):
    db = tmp_path / "test.db"
    backup_dir = tmp_path / "backups"
    
    manager = BackupManager(db_path=str(db), backup_dir=str(backup_dir))
    res_backup = manager.create_sqlite_backup("test_bk.db")
    assert res_backup["success"] is True

    res_restore = manager.restore_sqlite_backup("test_bk.db")
    assert res_restore["success"] is True