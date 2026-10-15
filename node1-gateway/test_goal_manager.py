import pytest
import os
from goal_manager import GoalManager, GoalCheckpoint

@pytest.fixture
def temp_goal_mgr(tmp_path):
    db = str(tmp_path / "goals_test.db")
    return GoalManager(db_path=db)

def test_goal_checkpoint_persistence(temp_goal_mgr):
    cp = GoalCheckpoint(goal_id="g-1", status="running", target_file="main.py")
    temp_goal_mgr.save_checkpoint(cp)

    loaded = temp_goal_mgr.load_checkpoint("g-1")
    assert loaded is not None
    assert loaded.goal_id == "g-1"
    assert loaded.status == "running"
    assert loaded.target_file == "main.py"
    assert loaded.rollback_available is True