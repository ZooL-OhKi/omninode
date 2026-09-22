import time
from workspace_manager import WorkspaceManager
from test_executor import CommandExecutor

class AutonomousWorkLoop:
    def __init__(self, workspace_manager: WorkspaceManager, test_executor: CommandExecutor):
        self.wm = workspace_manager
        self.executor = test_executor
        self.audit_ids = []

    def execute_goal(self, goal_data: dict) -> dict:
        commands = goal_data.get("commands", [["python", "-m", "pytest", "-q"]])
        max_iterations = goal_data.get("max_iterations", 3)
        max_duration = goal_data.get("max_duration_seconds", 900)

        start_time = time.time()
        goal_id = self.wm.goal_id

        test_results = []
        status = "failed"
        iteration = 0

        while iteration < max_iterations:
            if (time.time() - start_time) > max_duration:
                status = "failed"
                break

            iteration += 1
            all_passed = True

            for cmd in commands:
                res = self.executor.run(cmd)
                test_results.append(res)
                if res.get("status") == "blocked":
                    return {
                        "goal_id": goal_id,
                        "status": "blocked",
                        "changed_files": [],
                        "tests": test_results,
                        "artifacts": [],
                        "audit_ids": [res.get("audit_id")],
                        "next_action": "needs_capability_grant"
                    }
                if res.get("exit_code", 1) != 0:
                    all_passed = False

            if all_passed:
                status = "completed"
                break

        changed_files = [p.relative_to(self.wm.base_dir).as_posix() for p in self.wm.base_dir.rglob("*") if p.is_file()]

        return {
            "goal_id": goal_id,
            "status": status,
            "changed_files": changed_files,
            "tests": test_results,
            "artifacts": [],
            "audit_ids": self.audit_ids,
            "next_action": None if status == "completed" else "review_errors"
        }
