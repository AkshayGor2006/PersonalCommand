import unittest

from intelligence.task_planner import TaskPlanner


class TestTaskPlanner(unittest.TestCase):

    def setUp(self):
        self.planner = TaskPlanner()

    def test_single_action_plan(self):

        parsed_command = {
            "status": "ok",
            "intent": "open_application",
            "actions": [
                {
                    "command": "OPEN_NOTEPAD",
                    "arguments": {}
                }
            ]
        }

        result = self.planner.create_plan(parsed_command)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["total_steps"], 1)

        self.assertEqual(
            result["steps"][0]["command"],
            "OPEN_NOTEPAD"
        )

    def test_multiple_action_plan(self):

        parsed_command = {
            "status": "ok",
            "intent": "multiple_actions",
            "actions": [
                {
                    "command": "OPEN_EDGE",
                    "arguments": {
                        "url": "https://www.google.com"
                    }
                },
                {
                    "command": "OPEN_NOTEPAD",
                    "arguments": {}
                }
            ]
        }

        result = self.planner.create_plan(parsed_command)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["total_steps"], 2)

        self.assertEqual(
            result["steps"][0]["step"],
            1
        )

        self.assertEqual(
            result["steps"][1]["step"],
            2
        )

    def test_unknown_command_rejected(self):

        parsed_command = {
            "status": "ok",
            "actions": [
                {
                    "command": "DELETE_FILES",
                    "arguments": {}
                }
            ]
        }

        result = self.planner.create_plan(parsed_command)

        self.assertEqual(result["status"], "error")

    def test_invalid_arguments_rejected(self):

        parsed_command = {
            "status": "ok",
            "actions": [
                {
                    "command": "OPEN_NOTEPAD",
                    "arguments": {
                        "shell_command": "something"
                    }
                }
            ]
        }

        result = self.planner.create_plan(parsed_command)

        self.assertEqual(result["status"], "error")

    def test_empty_actions_rejected(self):

        parsed_command = {
            "status": "ok",
            "actions": []
        }

        result = self.planner.create_plan(parsed_command)

        self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main()