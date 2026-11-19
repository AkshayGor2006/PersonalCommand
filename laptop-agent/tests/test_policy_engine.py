import unittest

from intelligence.policy_engine import PolicyEngine


class TestPolicyEngine(unittest.TestCase):

    def setUp(self):
        self.engine = PolicyEngine()

    def test_notepad_approved(self):

        plan = {
            "status": "ok",
            "steps": [
                {
                    "step": 1,
                    "command": "OPEN_NOTEPAD",
                    "arguments": {},
                    "status": "pending"
                }
            ]
        }

        result = self.engine.evaluate(plan)

        self.assertEqual(result["status"], "approved")

    def test_https_requires_confirmation(self):

        plan = {
            "status": "ok",
            "steps": [
                {
                    "step": 1,
                    "command": "OPEN_EDGE",
                    "arguments": {
                        "url": "https://www.google.com"
                    },
                    "status": "pending"
                }
            ]
        }

        result = self.engine.evaluate(plan)

        self.assertEqual(
            result["status"],
            "approved"
        )

    def test_http_url_rejected(self):

        plan = {
            "status": "ok",
            "steps": [
                {
                    "step": 1,
                    "command": "OPEN_EDGE",
                    "arguments": {
                        "url": "http://example.com"
                    }
                }
            ]
        }

        result = self.engine.evaluate(plan)

        self.assertEqual(result["status"], "rejected")

    def test_javascript_url_rejected(self):

        plan = {
            "status": "ok",
            "steps": [
                {
                    "step": 1,
                    "command": "OPEN_EDGE",
                    "arguments": {
                        "url": "javascript:alert(1)"
                    }
                }
            ]
        }

        result = self.engine.evaluate(plan)

        self.assertEqual(result["status"], "rejected")

    def test_unknown_command_rejected(self):

        plan = {
            "status": "ok",
            "steps": [
                {
                    "step": 1,
                    "command": "DELETE_FILES",
                    "arguments": {}
                }
            ]
        }

        result = self.engine.evaluate(plan)

        self.assertEqual(result["status"], "rejected")

    def test_unexpected_argument_rejected(self):

        plan = {
            "status": "ok",
            "steps": [
                {
                    "step": 1,
                    "command": "OPEN_NOTEPAD",
                    "arguments": {
                        "shell_command": "something"
                    }
                }
            ]
        }

        result = self.engine.evaluate(plan)

        self.assertEqual(result["status"], "rejected")

    def test_missing_url_rejected(self):

        plan = {
            "status": "ok",
            "steps": [
                {
                    "step": 1,
                    "command": "OPEN_EDGE",
                    "arguments": {}
                }
            ]
        }

        result = self.engine.evaluate(plan)

        self.assertEqual(result["status"], "rejected")

    def test_invalid_plan_rejected(self):

        result = self.engine.evaluate(None)

        self.assertEqual(result["status"], "rejected")

    def test_application_approved(self):

        plan = {
            "status": "ok",
            "steps": [
                {
                    "step": 1,
                    "command": "OPEN_APPLICATION",
                    "arguments": {
                        "application": "VS Code"
                    },
                    "status": "pending"
                }
            ]
        }

        result = self.engine.evaluate(plan)

        self.assertEqual(result["status"], "approved")


    def test_application_missing_name_rejected(self):

        plan = {
            "status": "ok",
            "steps": [
                {
                    "step": 1,
                    "command": "OPEN_APPLICATION",
                    "arguments": {}
                }
            ]
        }
        

        result = self.engine.evaluate(plan)

        self.assertEqual(result["status"], "rejected")


    def test_application_invalid_type_rejected(self):

        plan = {
            "status": "ok",
            "steps": [
                {
                    "step": 1,
                    "command": "OPEN_APPLICATION",
                    "arguments": {
                        "application": 123
                    }
                }
            ]
        }
    

        result = self.engine.evaluate(plan)

        self.assertEqual(result["status"], "rejected")


    def test_application_control_characters_rejected(self):

        plan = {
            "status": "ok",
            "steps": [
                {
                    "step": 1,
                    "command": "OPEN_APPLICATION",
                    "arguments": {
                        "application": "VS Code\n"
                    }
                }
            ]
        }
    

        result = self.engine.evaluate(plan)

        self.assertEqual(result["status"], "rejected")



if __name__ == "__main__":
    unittest.main()