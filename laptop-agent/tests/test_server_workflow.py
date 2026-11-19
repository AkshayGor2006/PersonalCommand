import unittest

from workflow_service import WorkflowService


class TestWorkflowAuthorization(unittest.TestCase):

    def setUp(self):

        self.executed = []

        def open_edge(arguments):

            self.executed.append("OPEN_EDGE")

            return {
                "status": "success",
                "message": "Edge opened"
            }

        def open_application(arguments):

            self.executed.append("OPEN_APPLICATION")

            return {
                "status": "success",
                "message": "Application opened"
            }

        self.service = WorkflowService({
            "OPEN_EDGE": open_edge,
            "OPEN_APPLICATION": open_application
        })

    def test_authorized_notepad(self):

        def authorization_check(plan):

            return all(
                step["command"] == "OPEN_APPLICATION"
                for step in plan["steps"]
            )

        result = self.service.process(
            "Open Notepad",
            authorization_check=authorization_check
        )

        self.assertEqual(result["status"], "success")

        self.assertEqual(
            self.executed,
            ["OPEN_APPLICATION"]
        )

    def test_unauthorized_browser(self):

        def authorization_check(plan):

            return all(
                step["command"] == "OPEN_APPLICATION"
                for step in plan["steps"]
            )

        result = self.service.process(
            "Search for Python security",
            authorization_check=authorization_check
        )

        self.assertEqual(result["status"], "rejected")

        self.assertEqual(self.executed, [])


if __name__ == "__main__":
    unittest.main()