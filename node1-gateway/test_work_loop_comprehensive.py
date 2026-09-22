import unittest
from audit import AuditEventEngine
from policy_engine import PolicyEngine
from workspace_manager import WorkspaceManager
from test_executor import CommandExecutor

class TestAutonomousWorkLoopComprehensive(unittest.TestCase):
    def setUp(self):
        self.audit = AuditEventEngine()
        self.policy = PolicyEngine(self.audit)
        self.ws_dir = "./test_ws_sandbox_comprehensive"
        self.agent_id = "agent-01"
        self.goal_id = "goal-999"
        self.wm = WorkspaceManager(self.ws_dir, self.policy, self.agent_id, self.goal_id)
        self.executor = CommandExecutor(self.policy, self.agent_id, self.goal_id, self.ws_dir)

    def test_default_deny(self):
        allowed, _ = self.policy.authorize(self.agent_id, self.goal_id, "workspace.write", "any", "write")
        self.assertFalse(allowed)

    def test_path_traversal_denial(self):
        with self.assertRaises(ValueError):
            self.wm.write("../outside.txt", "evil")

    def test_unallowed_command(self):
        with self.assertRaises(ValueError):
            self.executor.run(["rm", "-rf", "/"])

if __name__ == "__main__":
    unittest.main()
