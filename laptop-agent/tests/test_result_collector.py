import unittest

from intelligence.result_collector import ResultCollector


class TestResultCollector(unittest.TestCase):

    def setUp(self):
        self.collector = ResultCollector()

    def test_successful_workflow(self):

        execution_result = {
            "status": "success",
            "results": [
                {
                    "step": 1,
                    "command": "OPEN_NOTEPAD",
                    "status": "success",
                    "message": "Notepad opened."
                },
                {
                    "step": 2,
                    "command": "OPEN_EDGE",
                    "status": "success",
                    "message": "Edge opened."
                }
            ]
        }

        result = self.collector.collect(execution_result)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_steps"], 2)
        self.assertEqual(result["successful_steps"], 2)
        self.assertEqual(result["failed_steps"], 0)

    def test_failed_workflow(self):

        execution_result = {
            "status": "failed",
            "results": [
                {
                    "step": 1,
                    "command": "OPEN_NOTEPAD",
                    "status": "success",
                    "message": "Notepad opened."
                },
                {
                    "step": 2,
                    "command": "OPEN_EDGE",
                    "status": "error",
                    "message": "Edge failed."
                }
            ]
        }

        result = self.collector.collect(execution_result)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["successful_steps"], 1)
        self.assertEqual(result["failed_steps"], 1)

    def test_rejected_workflow(self):

        execution_result = {
            "status": "rejected",
            "results": []
        }

        result = self.collector.collect(execution_result)

        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["total_steps"], 0)

    def test_confirmation_required(self):

        execution_result = {
            "status": "requires_confirmation",
            "results": []
        }

        result = self.collector.collect(execution_result)

        self.assertEqual(
            result["status"],
            "requires_confirmation"
        )

    def test_empty_successful_workflow(self):

        execution_result = {
            "status": "success",
            "results": []
        }

        result = self.collector.collect(execution_result)

        self.assertEqual(result["total_steps"], 0)
        self.assertEqual(result["successful_steps"], 0)

    def test_invalid_execution_result(self):

        result = self.collector.collect("invalid data")

        self.assertEqual(result["status"], "error")

    def test_unknown_status(self):

        execution_result = {
            "status": "unknown",
            "results": []
        }

        result = self.collector.collect(execution_result)

        self.assertEqual(result["status"], "error")

    def test_invalid_step_data(self):

        execution_result = {
            "status": "success",
            "results": [
                {
                    "step": 0,
                    "command": "OPEN_EDGE",
                    "status": "success",
                    "message": "Edge opened."
                }
            ]
        }

        result = self.collector.collect(execution_result)

        self.assertEqual(result["status"], "error")

    def test_missing_command(self):

        execution_result = {
            "status": "success",
            "results": [
                {
                    "step": 1,
                    "status": "success",
                    "message": "Completed."
                }
            ]
        }

        result = self.collector.collect(execution_result)

        self.assertEqual(result["status"], "error")

    def test_timestamp_generated(self):

        execution_result = {
            "status": "success",
            "results": []
        }

        result = self.collector.collect(execution_result)

        self.assertIn("completed_at", result)

        self.assertTrue(result["completed_at"])


if __name__ == "__main__":
    unittest.main()