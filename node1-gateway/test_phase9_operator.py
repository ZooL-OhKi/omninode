import pytest
from goal_queue import GoalItem, TaskItem, GoalQueueDB
from workloop_driver import WorkloopDriver

def test_goal_queue_persistence(tmp_path):
    db_file = tmp_path / "test_goals.db"
    queue = GoalQueueDB(db_path=str(db_file))

    goal = GoalItem(goal_id="g-1", priority=10)
    task = TaskItem(task_id="t-1", goal_id="g-1", status="queued")

    queue.add_goal(goal, [task])
    
    fetched_goal = queue.get_goal("g-1")
    assert fetched_goal is not None
    assert fetched_goal.priority == 10

    tasks = queue.get_tasks_for_goal("g-1")
    assert len(tasks) == 1
    assert tasks[0].task_id == "t-1"

    queue.update_task_status("t-1", "completed")
    updated_tasks = queue.get_tasks_for_goal("g-1")
    assert updated_tasks[0].status == "completed"

def test_dag_dependency_resolution():
    driver = WorkloopDriver()
    t1 = TaskItem(task_id="t-1", goal_id="g-1", status="completed")
    t2 = TaskItem(task_id="t-2", goal_id="g-1", depends_on=["t-1"], status="queued")
    t3 = TaskItem(task_id="t-3", goal_id="g-1", depends_on=["t-2"], status="queued")

    resolved = driver.resolve_dag_dependencies([t1, t2, t3])
    
    # t2 dipende da t1 (completato) -> deve diventare ready
    assert next(t for t in resolved if t.task_id == "t-2").status == "ready"
    # t3 dipende da t2 (non ancora completato) -> resta queued
    assert next(t for t in resolved if t.task_id == "t-3").status == "queued"

def test_patch_safety_validation():
    driver = WorkloopDriver()
    
    # Modifica sicura Tier 0
    res_safe = driver.validate_patch_safety(["node1-gateway/some_feature.py"], risk_tier=0)
    assert res_safe["allowed"] is True

    # Modifica protetta bloccata
    res_prot = driver.validate_patch_safety(["config/acl.conf"], risk_tier=0)
    assert res_prot["allowed"] is False

    # Tier alto bloccato
    res_tier = driver.validate_patch_safety(["node1-gateway/some_feature.py"], risk_tier=2)
    assert res_tier["allowed"] is False