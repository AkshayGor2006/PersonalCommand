import unittest
import socket
import json
import hmac
import hashlib
import os
import sys
import time
import subprocess

from pathlib import Path


HOST = "127.0.0.1"
PORT = 8765

TEST_SECRET = "a-test-only-secret-for-tcp-integration"


class TestTCPWorkflow(unittest.TestCase):

    def setUp(self):

        # Locate the laptop-agent project directory.
        self.project_dir = Path(__file__).resolve().parents[1]

        # Give the test server its own test secret.
        environment = os.environ.copy()
        environment["CONTROL_SECRET"] = TEST_SECRET

        # Start the real Python server in a separate process.
        self.server_process = subprocess.Popen(
            [sys.executable, "-u", "server.py"],
            cwd=self.project_dir,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        self.connection = None
        self.reader = None
        self.writer = None

        try:

            # Wait until the server is listening.
            deadline = time.monotonic() + 8

            while time.monotonic() < deadline:

                if self.server_process.poll() is not None:
                    raise RuntimeError(
                        "Server process stopped before accepting connections."
                    )

                try:

                    self.connection = socket.create_connection(
                        (HOST, PORT),
                        timeout=2
                    )

                    break

                except OSError:
                    time.sleep(0.1)

            else:
                raise RuntimeError(
                    "Could not connect to the test server."
                )

            self.connection.settimeout(5)

            self.reader = self.connection.makefile(
                "r",
                encoding="utf-8"
            )

            self.writer = self.connection.makefile(
                "w",
                encoding="utf-8"
            )

            # Complete HMAC authentication.
            self.authenticate()

        except Exception:
            self.tearDown()
            raise


    def authenticate(self):

        # 1. Receive authentication challenge.
        challenge_line = self.reader.readline()

        if not challenge_line:
            raise RuntimeError("No authentication challenge received.")

        challenge = json.loads(challenge_line)

        if challenge.get("type") != "auth_challenge":
            raise RuntimeError("Invalid authentication challenge.")

        nonce = challenge["nonce"]

        # 2. Calculate HMAC-SHA256 proof.
        proof = hmac.new(
            TEST_SECRET.encode("utf-8"),
            nonce.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        # 3. Send authentication response.
        self.send_message({
            "type": "auth_response",
            "proof": proof
        })

        # 4. Receive authentication result.
        result_line = self.reader.readline()

        if not result_line:
            raise RuntimeError("No authentication result received.")

        result = json.loads(result_line)

        if result.get("status") != "success":
            raise RuntimeError("Authentication failed.")

        self.session_token = result["session_token"]


    def send_message(self, message):

        self.writer.write(json.dumps(message) + "\n")
        self.writer.flush()


    def send_workflow(self, user_input):

        request = {
            "type": "workflow",
            "session_token": self.session_token,
            "user_input": user_input,
            "confirmation_granted": False
        }

        self.send_message(request)

        response_line = self.reader.readline()

        if not response_line:
            raise RuntimeError("Server did not return a response.")

        return json.loads(response_line)


    def test_open_notepad_over_tcp(self):

        response = self.send_workflow("Open Notepad")

        self.assertEqual(
            response["status"],
            "success"
        )

        self.assertIn(
            "results",
            response
        )

        self.assertGreater(
            response.get("successful_steps", 0),
            0
        )


    def test_browser_search_executes_without_confirmation(self):

        response = self.send_workflow(
            "Search for Python security"
        )

        self.assertEqual(
            response["status"],
            "success"
        )

        self.assertEqual(
            response.get("successful_steps", 0),
            1
        )


    def tearDown(self):

        if self.reader:
            self.reader.close()

        if self.writer:
            self.writer.close()

        if self.connection:
            self.connection.close()

        if self.server_process:

            self.server_process.terminate()

            try:
                self.server_process.wait(timeout=3)

            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.server_process.wait()


if __name__ == "__main__":
    unittest.main()