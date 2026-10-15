import pytest
import sqlite3
from goal_dag import GoalDAG
from goal_queue import OperationalGoalQueue, GoalItem, TaskItem
from workloop_driver import WorkloopDriver

def test_dag_cycle_detection():
    tasks_no_cycle = [{"task_id": "t1", "dependencies": []}, {"task_id": "t2", "dependencies": ["t1"]}]
    dag1 = GoalDAG(tasks_no_cycle)
    assert dag1.has_cycle() is False

    tasks_with_cycle = [{"task_id": "t1", "dependencies": ["t2"]}, {"task_id": "t2", "dependencies": ["t1"]}]
    dag2 = GoalDAG(tasks_with_cycle)
    assert dag2.has_cycle() is True

def test_protected_patterns():
    dag = GoalDAG([])
    assert dag.is_path_protected("policy/security.conf") is True
    assert dag.is_path_protected(".env") is True
    assert dag.is_path_protected("node1-gateway/main.py") is False

def test_operational_queue_transitions(tmp_path):
    db_file = tmp_path / "op_queue.db"
    q = OperationalGoalQueue(db_path=str(db_file))
    conn = sqlite3.connect(str(db_file))
    conn.execute("INSERT INTO op_tasks VALUES ('t1', 'g1', 'ready', '', 1)")
    conn.commit()
    conn.close()

    assert q.claim_ready_task("t1", "exec-123") is True
    q.complete_task("t1")

def test_workloop_end_to_end():
    driver = WorkloopDriver()
    tasks = [{"task_id": "t1", "dependencies": []}]
    res = driver.execute_goal_pipeline("g-e2e-1", tasks, risk_tier=1)
    assert res["success"] is True
    assert res["status"] == "pull_request_opened"