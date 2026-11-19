import socket
import json
import hmac
import hashlib
import os


HOST = "127.0.0.1"
PORT = 8765


# -----------------------------
# ENVIRONMENT CONFIGURATION
# -----------------------------

secret = os.environ.get("CONTROL_SECRET")

if not secret:
    raise RuntimeError(
        "CONTROL_SECRET is not set. Set it in PowerShell before running."
    )

SHARED_SECRET = secret.encode()


# -----------------------------
# MESSAGE FRAMING
# -----------------------------

def receive_message(connection, buffer):
    while b"\n" not in buffer:
        chunk = connection.recv(1024)

        if not chunk:
            return None, buffer

        buffer += chunk

    message, buffer = buffer.split(b"\n", 1)

    return message.decode(), buffer


def send_message(connection, message):
    data = json.dumps(message) + "\n"
    connection.sendall(data.encode())


# -----------------------------
# COMMAND HELPER
# -----------------------------

def send_command(
    connection,
    command,
    session_token,
    buffer,
    arguments=None,
):
    request = {
        "type": "command",
        "command": command,
        "session_token": session_token,
        "arguments": arguments if arguments is not None else {},
    }

    send_message(connection, request)

    response, buffer = receive_message(connection, buffer)

    if response is None:
        print(f"{command}: server disconnected")
        return None, buffer

    try:
        result = json.loads(response)

    except json.JSONDecodeError:
        print(f"{command}: invalid JSON response")
        return None, buffer

    print(f"{command} response:", result)

    return result, buffer


# -----------------------------
# TEST ASSERTION HELPER
# -----------------------------

def check_result(
    test_name,
    result,
    expected_status,
    expected_message=None,
):
    passed = (
        isinstance(result, dict)
        and result.get("status") == expected_status
    )

    if expected_message is not None:
        passed = (
            passed
            and result.get("message") == expected_message
        )

    print(f"[{'PASS' if passed else 'FAIL'}] {test_name}")

    if not passed:
        print("    Expected status:", expected_status)
        print("    Expected message:", expected_message)
        print("    Actual response:", result)

    return passed


# -----------------------------
# MAIN TEST RUNNER
# -----------------------------

def main():
    client_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    buffer = b""

    try:
        # -----------------------------
        # CONNECT TO SERVER
        # -----------------------------

        client_socket.connect((HOST, PORT))

        print("Connected to server.")

        # -----------------------------
        # AUTHENTICATION
        # -----------------------------

        message, buffer = receive_message(
            client_socket,
            buffer,
        )

        if message is None:
            raise ConnectionError(
                "Server disconnected before authentication."
            )

        challenge = json.loads(message)

        if challenge.get("type") != "auth_challenge":
            raise ValueError(
                "Unexpected authentication challenge."
            )

        nonce = challenge.get("nonce")

        if not isinstance(nonce, str):
            raise ValueError("Invalid authentication nonce.")

        print("Authentication challenge received.")

        # Calculate the HMAC-SHA256 proof.
        proof = hmac.new(
            SHARED_SECRET,
            nonce.encode(),
            hashlib.sha256,
        ).hexdigest()

        # Send authentication proof.
        send_message(
            client_socket,
            {
                "type": "auth_response",
                "proof": proof,
            },
        )

        # Receive authentication result.
        auth_message, buffer = receive_message(
            client_socket,
            buffer,
        )

        if auth_message is None:
            raise ConnectionError(
                "Server disconnected during authentication."
            )

        auth_response = json.loads(auth_message)

        print("Authentication response:", auth_response)

        if auth_response.get("status") != "success":
            raise PermissionError("Authentication failed.")

        session_token = auth_response.get("session_token")

        if not isinstance(session_token, str):
            raise ValueError(
                "Server did not provide a valid session token."
            )

        print("Authentication successful. Session established.")

        # -----------------------------
        # LAYER 7 TEST SUITE
        # -----------------------------

        print("\n========== LAYER 7 TEST SUITE ==========\n")

        test_results = []

        def record_test(
            name,
            result,
            expected_status,
            expected_message=None,
        ):
            passed = check_result(
                name,
                result,
                expected_status,
                expected_message,
            )

            test_results.append((name, passed))

        # TEST 1: DEFAULT BROWSER LAUNCH

        print("\nTEST 1: Default browser launch")

        result, buffer = send_command(
            client_socket,
            "OPEN_EDGE",
            session_token,
            buffer,
        )

        record_test(
            "Default browser launch",
            result,
            "success",
        )

        # TEST 2: VALID HTTPS URL

        print("\nTEST 2: Valid HTTPS URL")

        result, buffer = send_command(
            client_socket,
            "OPEN_EDGE",
            session_token,
            buffer,
            arguments={
                "url": "https://example.com",
            },
        )

        record_test(
            "Accept valid HTTPS URL",
            result,
            "success",
        )

        # TEST 3: REJECT HTTP URL

        print("\nTEST 3: Reject HTTP URL")

        result, buffer = send_command(
            client_socket,
            "OPEN_EDGE",
            session_token,
            buffer,
            arguments={
                "url": "http://example.com",
            },
        )

        record_test(
            "Reject HTTP URL",
            result,
            "error",
            "Only HTTPS URLs are allowed",
        )

        # TEST 4: REJECT JAVASCRIPT URL

        print("\nTEST 4: Reject javascript URL")

        result, buffer = send_command(
            client_socket,
            "OPEN_EDGE",
            session_token,
            buffer,
            arguments={
                "url": "javascript:alert(1)",
            },
        )

        record_test(
            "Reject javascript URL",
            result,
            "error",
        )

        # TEST 5: REJECT EMPTY URL

        print("\nTEST 5: Reject empty URL")

        result, buffer = send_command(
            client_socket,
            "OPEN_EDGE",
            session_token,
            buffer,
            arguments={
                "url": "",
            },
        )

        record_test(
            "Reject empty URL",
            result,
            "error",
            "URL is required",
        )

        # TEST 6: REJECT EMBEDDED CREDENTIALS

        print("\nTEST 6: Reject embedded credentials")

        result, buffer = send_command(
            client_socket,
            "OPEN_EDGE",
            session_token,
            buffer,
            arguments={
                "url": "https://user:password@example.com",
            },
        )

        record_test(
            "Reject URL containing credentials",
            result,
            "error",
            "Embedded credentials are not allowed",
        )

        # TEST 7: REJECT OVERSIZED URL

        print("\nTEST 7: Reject oversized URL")

        result, buffer = send_command(
            client_socket,
            "OPEN_EDGE",
            session_token,
            buffer,
            arguments={
                "url": "https://" + ("a" * 2050) + ".com",
            },
        )

        record_test(
            "Reject oversized URL",
            result,
            "error",
            "URL is too long",
        )

        # TEST 8: LAUNCH NOTEPAD

        print("\nTEST 8: Launch Notepad")

        result, buffer = send_command(
            client_socket,
            "OPEN_NOTEPAD",
            session_token,
            buffer,
        )

        notepad_passed = (
            isinstance(result, dict)
            and result.get("status") == "success"
            and result.get("application") == "NOTEPAD"
            and isinstance(result.get("pid"), int)
        )

        print(
            f"[{'PASS' if notepad_passed else 'FAIL'}] "
            "Launch Notepad"
        )

        if not notepad_passed:
            print("    Actual response:", result)

        test_results.append(
            ("Launch Notepad", notepad_passed)
        )

        # TEST 9: AUTHORIZED TEST COMMAND

        print("\nTEST 9: Authorized test command")

        result, buffer = send_command(
            client_socket,
            "TEST_MESSAGE",
            session_token,
            buffer,
        )

        record_test(
            "Execute authorized test command",
            result,
            "success",
            "Authorized test command executed",
        )

        # TEST 10: UNKNOWN COMMAND

        print("\nTEST 10: Unknown command")

        result, buffer = send_command(
            client_socket,
            "DELETE_EVERYTHING",
            session_token,
            buffer,
        )

        record_test(
            "Reject unknown command",
            result,
            "error",
            "Command not allowed",
        )

        # TEST 11: INVALID SESSION TOKEN

        print("\nTEST 11: Invalid session token")

        result, buffer = send_command(
            client_socket,
            "OPEN_EDGE",
            "fake-invalid-token",
            buffer,
        )

        record_test(
            "Reject invalid session token",
            result,
            "error",
            "Invalid or expired session",
        )

        # TEST 12: MISSING SESSION TOKEN

        print("\nTEST 12: Missing session token")

        send_message(
            client_socket,
            {
                "type": "command",
                "command": "OPEN_EDGE",
            },
        )

        response, buffer = receive_message(
            client_socket,
            buffer,
        )

        try:
            result = json.loads(response) if response else None
        except json.JSONDecodeError:
            result = None

        record_test(
            "Reject missing session token",
            result,
            "error",
            "Session token required",
        )

        # TEST 13: INVALID REQUEST TYPE

        print("\nTEST 13: Invalid request type")

        send_message(
            client_socket,
            {
                "type": "not_a_command",
                "command": "OPEN_EDGE",
                "session_token": session_token,
            },
        )

        response, buffer = receive_message(
            client_socket,
            buffer,
        )

        try:
            result = json.loads(response) if response else None
        except json.JSONDecodeError:
            result = None

        record_test(
            "Reject invalid request type",
            result,
            "error",
            "Invalid request type",
        )

        # TEST 14: MISSING COMMAND

        print("\nTEST 14: Missing command")

        send_message(
            client_socket,
            {
                "type": "command",
                "session_token": session_token,
            },
        )

        response, buffer = receive_message(
            client_socket,
            buffer,
        )

        try:
            result = json.loads(response) if response else None
        except json.JSONDecodeError:
            result = None

        record_test(
            "Reject missing command",
            result,
            "error",
            "Invalid command",
        )

        # TEST 15: INVALID ARGUMENTS TYPE

        print("\nTEST 15: Invalid arguments type")

        send_message(
            client_socket,
            {
                "type": "command",
                "command": "OPEN_EDGE",
                "session_token": session_token,
                "arguments": "not-an-object",
            },
        )

        response, buffer = receive_message(
            client_socket,
            buffer,
        )

        try:
            result = json.loads(response) if response else None
        except json.JSONDecodeError:
            result = None

        record_test(
            "Reject invalid arguments type",
            result,
            "error",
            "Arguments must be a JSON object",
        )

        # -----------------------------
        # TEST SUMMARY
        # -----------------------------

        print("\n========== TEST SUMMARY ==========")

        passed_count = sum(
            1 for _, passed in test_results if passed
        )

        failed_count = len(test_results) - passed_count

        for name, passed in test_results:
            print(
                f"[{'PASS' if passed else 'FAIL'}] {name}"
            )

        print(f"\nTotal tests: {len(test_results)}")
        print(f"Passed:      {passed_count}")
        print(f"Failed:      {failed_count}")

    except (
        OSError,
        ValueError,
        PermissionError,
        ConnectionError,
        json.JSONDecodeError,
    ) as error:
        print("Client error:", error)

    finally:
        client_socket.close()
        print("Client connection closed.")


if __name__ == "__main__":
    main()