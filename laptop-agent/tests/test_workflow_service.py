import unittest

from workflow_service import WorkflowService


class TestWorkflowService(unittest.TestCase):

    def setUp(self):

        # Fake handlers prevent tests from opening
        # real applications or browsers.

        self.executed_commands = []

        def open_edge_handler(arguments):

            self.executed_commands.append("OPEN_EDGE")

            return {
                "status": "success",
                "message": "Browser opened successfully."
            }

        def open_application_handler(arguments):

            self.executed_commands.append("OPEN_APPLICATION")

            return {
                "status": "success",
                "message": "Application opened successfully."
            }

        handlers = {
            "OPEN_EDGE": open_edge_handler,
            "OPEN_APPLICATION": open_application_handler
        }

        self.service = WorkflowService(handlers)


    def test_open_notepad(self):

        result = self.service.process(
            "Open Notepad"
        )

        self.assertEqual(result["status"], "success")

        self.assertEqual(
            self.executed_commands,
            ["OPEN_APPLICATION"]
        )


    def test_search_executes_without_confirmation(self):

        result = self.service.process(
            "Open Google and search who is Elon Musk"
        )

        self.assertEqual(
            result["status"],
            "success"
        )

        self.assertEqual(
            self.executed_commands,
            ["OPEN_EDGE"]
        )


    def test_search_after_confirmation(self):

        result = self.service.process(
            "Open Google and search who is Elon Musk",
            confirmation_granted=True
        )

        self.assertEqual(result["status"], "success")

        self.assertEqual(
            self.executed_commands,
            ["OPEN_EDGE"]
        )


    def test_unknown_command_rejected(self):

        result = self.service.process(
            "Delete all my files"
        )

        self.assertEqual(result["status"], "error")

        self.assertEqual(
            self.executed_commands,
            []
        )


if __name__ == "__main__":
    unittest.main()