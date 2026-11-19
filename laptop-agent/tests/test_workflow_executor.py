import unittest

from intelligence.workflow_executor import WorkflowExecutor


class TestWorkflowExecutor(unittest.TestCase):

    def setUp(self):

        # Fake handlers prevent tests from launching real applications.

        self.executed_commands = []

        def open_edge(arguments):

            self.executed_commands.append("OPEN_EDGE")

            return {
                "status": "success",
                "message": "Edge launch requested."
            }

        def open_application(arguments):

            self.executed_commands.append("OPEN_APPLICATION")

            return {
                "status": "success",
                "message": "Application launch requested."
            }

        self.executor = WorkflowExecutor({
            "OPEN_EDGE": open_edge,
            "OPEN_APPLICATION": open_application
        })

    def create_policy_decision(self, steps):

        return {
            "status": "approved",
            "approved_steps": steps
        }

    def test_single_action_execution(self):

        decision = self.create_policy_decision([
            {
                "step": 1,
                "command": "OPEN_APPLICATION",
                "arguments": {"application": "Notepad"}
            }
        ])

        result = self.executor.execute(decision)

        self.assertEqual(result["status"], "success")

        self.assertEqual(
            self.executed_commands,
            ["OPEN_APPLICATION"]
        )

    def test_multiple_action_execution(self):

        decision = self.create_policy_decision([
            {
                "step": 1,
                "command": "OPEN_APPLICATION",
                "arguments": {"application": "Notepad"}
            },
            {
                "step": 2,
                "command": "OPEN_EDGE",
                "arguments": {
                    "url": "https://www.google.com"
                }
            }
        ])

        result = self.executor.execute(decision)

        self.assertEqual(result["status"], "success")

        self.assertEqual(
            self.executed_commands,
            ["OPEN_APPLICATION", "OPEN_EDGE"]
        )

        self.assertEqual(result["total_steps"], 2)

    def test_rejected_workflow(self):

        decision = {
            "status": "rejected",
            "approved_steps": []
        }

        result = self.executor.execute(decision)

        self.assertEqual(result["status"], "rejected")

        self.assertEqual(self.executed_commands, [])

    def test_confirmation_required(self):

        decision = {
            "status": "requires_confirmation",
            "approved_steps": [
                {
                    "step": 1,
                    "command": "OPEN_EDGE",
                    "arguments": {
                        "url": "https://www.google.com"
                    }
                }
            ]
        }

        result = self.executor.execute(decision)

        self.assertEqual(
            result["status"],
            "requires_confirmation"
        )

        self.assertEqual(self.executed_commands, [])

    def test_confirmation_granted(self):

        decision = {
            "status": "requires_confirmation",
            "approved_steps": [
                {
                    "step": 1,
                    "command": "OPEN_EDGE",
                    "arguments": {
                        "url": "https://www.google.com"
                    }
                }
            ]
        }

        result = self.executor.execute(
            decision,
            confirmation_granted=True
        )

        self.assertEqual(result["status"], "success")

        self.assertEqual(
            self.executed_commands,
            ["OPEN_EDGE"]
        )

    def test_unknown_command_rejected(self):

        decision = self.create_policy_decision([
            {
                "step": 1,
                "command": "DELETE_FILES",
                "arguments": {}
            }
        ])

        result = self.executor.execute(decision)

        self.assertEqual(result["status"], "failed")

        self.assertEqual(self.executed_commands, [])

    def test_unexpected_arguments_rejected(self):

        decision = self.create_policy_decision([
            {
                "step": 1,
                "command": "OPEN_APPLICATION",
                "arguments": {
                    "application": "Notepad",
                    "filename": "secret.txt"
                }
            }
        ])

        result = self.executor.execute(decision)

        self.assertEqual(result["status"], "failed")

        self.assertEqual(self.executed_commands, [])

    def test_missing_required_arguments_rejected(self):

        decision = self.create_policy_decision([
            {
                "step": 1,
                "command": "OPEN_EDGE",
                "arguments": {}
            }
        ])

        result = self.executor.execute(decision)

        self.assertEqual(result["status"], "failed")

        self.assertEqual(self.executed_commands, [])

    def test_empty_workflow_rejected(self):

        decision = self.create_policy_decision([])

        result = self.executor.execute(decision)

        self.assertEqual(result["status"], "rejected")

    def test_maximum_action_limit(self):

        decision = self.create_policy_decision([
            {
                "step": index,
                "command": "OPEN_APPLICATION",
                "arguments": {"application": "Notepad"}
            }
            for index in range(11)
        ])

        result = self.executor.execute(decision)

        self.assertEqual(result["status"], "rejected")

        self.assertEqual(self.executed_commands, [])


if __name__ == "__main__":
    unittest.main()