import socket
import json
import secrets
import hmac
import hashlib
import os
import time
import subprocess
import webbrowser

from pathlib import Path
from urllib.parse import urlsplit

from workflow_service import WorkflowService
from app_launcher_lab import ApplicationLauncher


HOST = "0.0.0.0"
PORT = 8765

SESSION_TTL = 15 * 60

session = None

SHARED_SECRET = os.environ["CONTROL_SECRET"].encode()

# -----------------------------
# EXECUTION ENGINE CONFIG
# -----------------------------

MAX_URL_LENGTH = 2048

# Only applications explicitly registered here may be launched.
ALLOWED_APPLICATIONS = {
    "NOTEPAD": {
        "executable": "notepad.exe",
        "capability": "control.application",
    }
}

# Tracks processes launched directly by this server.
# The server does not trust client-supplied PIDs.
launched_processes = {}

def open_edge(url="https://www.google.com"):
    valid, result = validate_url(url)

    if not valid:
        return {
            "status": "error",
            "message": result,
        }

    try:
        opened = webbrowser.open(
            f"microsoft-edge:{result}"
        )

    except Exception:
        return {
            "status": "error",
            "message": "Browser launch failed",
        }

    if not opened:
        return {
            "status": "error",
            "message": "Browser could not be opened",
        }

    return {
        "status": "success",
        "message": "Browser launch requested",
        "url": result,
    }

def show_test_message():
    return {
        "status": "success",
        "message": "Authorized test command executed"
    }

def validate_url(url):
    if not isinstance(url, str):
        return False, "URL must be a string"

    url = url.strip()

    if not url:
        return False, "URL is required"

    if len(url) > MAX_URL_LENGTH:
        return False, "URL is too long"

    if any(ord(character) < 32 for character in url):
        return False, "URL contains invalid control characters"

    try:
        parsed = urlsplit(url)

        # Accessing port can raise ValueError for malformed ports.
        _ = parsed.port

    except ValueError:
        return False, "Malformed URL"

    if parsed.scheme.lower() != "https":
        return False, "Only HTTPS URLs are allowed"

    if not parsed.hostname:
        return False, "URL hostname is required"

    if parsed.username is not None or parsed.password is not None:
        return False, "Embedded credentials are not allowed"

    return True, url

def open_application(application_name):
    if not isinstance(application_name, str):
        return {
            "status": "error",
            "message": "Invalid application name",
        }

    application_name = application_name.upper()

    application = ALLOWED_APPLICATIONS.get(application_name)

    if application is None:
        return {
            "status": "error",
            "message": "Application is not allowed",
        }

    executable = application["executable"]

    try:
        process = subprocess.Popen(
            [executable],
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    except FileNotFoundError:
        return {
            "status": "error",
            "message": "Application executable was not found",
        }

    except OSError:
        return {
            "status": "error",
            "message": "Operating system could not launch the application",
        }

    launched_processes[process.pid] = {
        "application": application_name,
        "started_at": time.monotonic(),
        "process": process,
    }

    return {
        "status": "success",
        "message": "Application launch requested",
        "application": application_name,
        "pid": process.pid,
    }


# -----------------------------
# COMMAND REGISTRY
# -----------------------------

# APPLICATION MANAGEMENT
application_launcher = ApplicationLauncher()

# One generic command handles applications registered by ApplicationLauncher.
COMMANDS = {
    "OPEN_EDGE": lambda arguments: open_edge(
        arguments.get("url", "https://www.google.com")
    ),

    "OPEN_APPLICATION": lambda arguments: (
        application_launcher.launch_application(
            arguments.get("application")
        )
    ),

    "TEST_MESSAGE": lambda arguments: show_test_message(),
}

# -----------------------------
# WORKFLOW SERVICE
# -----------------------------

workflow_service = WorkflowService(COMMANDS)

COMMAND_CAPABILITIES = {
    "OPEN_EDGE": "control.browser",
    "OPEN_APPLICATION": "control.application",
    "TEST_MESSAGE": "control.test",
}

def dispatch_command(command, arguments):
    handler = COMMANDS.get(command)

    if handler is None:
        return {
            "status": "error",
            "message": "Command not allowed",
        }

    if not isinstance(arguments, dict):
        return {
            "status": "error",
            "message": "Arguments must be a JSON object",
        }

    try:
        return handler(arguments)

    except Exception:
        # Avoid returning internal exception details to the client.
        print("Command execution failed:", command)

        return {
            "status": "error",
            "message": "Command execution failed",
        }


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


def authenticate(connection, buffer):
    # 1. Generate a fresh random challenge
    nonce = secrets.token_hex(32)

    # 2. Send challenge to client
    send_message(
        connection,
        {
            "type": "auth_challenge",
            "nonce": nonce
        }
    )

    # 3. Receive authentication response
    message, buffer = receive_message(connection, buffer)

    if message is None:
        return False, buffer

    try:
        response = json.loads(message)
    except json.JSONDecodeError:
        return False, buffer

    # 4. Check message structure
    if response.get("type") != "auth_response":
        return False, buffer

    proof = response.get("proof")

    if not isinstance(proof, str):
        return False, buffer

    # 5. Calculate the expected HMAC
    expected_proof = hmac.new(
        SHARED_SECRET,
        nonce.encode(),
        hashlib.sha256
    ).hexdigest()

    # 6. Safely compare the two proofs
    if not hmac.compare_digest(proof, expected_proof):
        return False, buffer

    return True, buffer

def create_session(capabilities):
    token = secrets.token_urlsafe(32)

    return {
        "token": token,
        "expires_at": time.monotonic() + SESSION_TTL,
        "capabilities": set(capabilities)
    }

def validate_session(token):
    global session

    if session is None:
        return False

    if token != session["token"]:
        return False

    if time.monotonic() > session["expires_at"]:
        session = None
        return False

    session["expires_at"] = time.monotonic() + SESSION_TTL

    return True

def authorize_command(command, session):
    if not isinstance(session, dict):
        return False

    capabilities = session.get("capabilities")

    if not isinstance(capabilities, set):
        return False

    required_capability = COMMAND_CAPABILITIES.get(command)

    if required_capability is None:
        return False

    print(
        "Authorization:",
        command,
        "requires",
        required_capability,
        "session has",
        capabilities
    )

    if required_capability not in capabilities:
        return False

    return True

def authorize_workflow(execution_plan, active_session):

    if not isinstance(execution_plan, dict):
        return False

    steps = execution_plan.get("steps")

    if not isinstance(steps, list) or not steps:
        return False

    for step in steps:

        if not isinstance(step, dict):
            return False

        command = step.get("command")

        if not isinstance(command, str):
            return False

        if command not in COMMANDS:
            return False

        if not authorize_command(command, active_session):
            return False

    return True

def destroy_session():
    global session

    had_session = session is not None
    session = None

    print("Session destroyed:", had_session)

# -----------------------------
# WORKFLOW REQUEST HANDLER
# -----------------------------

def handle_workflow_request(request):

    # 1. Validate session token.

    token = request.get("session_token")

    if not isinstance(token, str):
        return {
            "status": "error",
            "message": "Session token required"
        }

    if not validate_session(token):
        return {
            "status": "error",
            "message": "Invalid or expired session"
        }

    # 2. Validate natural-language input.

    user_input = request.get("user_input")

    if not isinstance(user_input, str):
        return {
            "status": "error",
            "message": "User input must be text"
        }

    if not user_input.strip() or len(user_input) > 500:
        return {
            "status": "error",
            "message": "Invalid workflow input"
        }

    # 3. Validate explicit confirmation flag.

    confirmation_granted = request.get(
        "confirmation_granted",
        False
    )

    if not isinstance(confirmation_granted, bool):
        return {
            "status": "error",
            "message": "Invalid confirmation value"
        }

    # 4. Process the complete workflow.

    return workflow_service.process(
        user_input=user_input,
        confirmation_granted=confirmation_granted,
        authorization_check=lambda plan: authorize_workflow(
            plan,
            session
        )
    )

def handle_request(request):

    # 1. Validate request structure.
    if not isinstance(request, dict):
        return {
            "status": "error",
            "message": "Invalid request",
        }

    request_type = request.get("type")

    # 2. Route workflow requests.
    if request_type == "workflow":
        return handle_workflow_request(request)

    # 3. Reject unsupported request types.
    if request_type != "command":
        return {
            "status": "error",
            "message": "Invalid request type",
        }

    # 4. Retrieve session token.
    token = request.get("session_token")

    if not isinstance(token, str):
        return {
            "status": "error",
            "message": "Session token required",
        }

    # 5. Validate authenticated session.
    if not validate_session(token):
        return {
            "status": "error",
            "message": "Invalid or expired session",
        }

    # 6. Validate command.
    command = request.get("command")

    if not isinstance(command, str):
        return {
            "status": "error",
            "message": "Invalid command",
        }

    if command not in COMMANDS:
        return {
            "status": "error",
            "message": "Command not allowed",
        }

    # 7. Authorize command using session capabilities.
    if not authorize_command(command, session):
        return {
            "status": "error",
            "message": "Permission denied",
        }

    # 8. Validate arguments.
    arguments = request.get("arguments", {})

    if not isinstance(arguments, dict):
        return {
            "status": "error",
            "message": "Arguments must be a JSON object",
        }

    # 9. Dispatch approved command.
    return dispatch_command(command, arguments)


# -----------------------------
# SERVER START
# -----------------------------

server_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Server listening on port {PORT}...")


connection, address = server_socket.accept()

print(f"Connection received from {address}")

buffer = b""


# -----------------------------
# AUTHENTICATION
# -----------------------------

authenticated, buffer = authenticate(connection, buffer)

if not authenticated:
    print("Authentication failed")

    send_message(
        connection,
        {
            "status": "error",
            "message": "Authentication failed"
        }
    )

    connection.close()
    server_socket.close()

else:
    print("Authentication successful")

    session = create_session({
        "control.browser",
        "control.application",
        "control.test"
    })

    send_message(
        connection,
        {
            "status": "success",
            "message": "session created",
            "session_token": session["token"]
        }
    )

    # -----------------------------
    # COMMAND
    # -----------------------------

    while True:
        message, buffer = receive_message(connection, buffer)

        if message is None:
            print("Client disconnected")
            break

        try:
            request = json.loads(message)

        except json.JSONDecodeError:
            response = {
                "status": "error",
                "message": "Invalid JSON"
            }

            send_message(connection, response)
            continue

        print("Request received:", request.get("type"))

        response = handle_request(request)

        send_message(connection, response)

    destroy_session()

    connection.close()
    server_socket.close()

