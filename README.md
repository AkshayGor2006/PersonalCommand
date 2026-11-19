# PersonalCommand

### Security-first Android-to-Windows command system

PersonalCommand is a project that allows an Android phone to send controlled instructions to a Windows laptop over a local network.

The goal is to build a secure, permission-based command system where users can control approved laptop applications directly from their phones.

## Architecture

The project consists of two main components:

**1. Android Client**
- Android application built with Java.
- Provides a user interface for connecting to the laptop.
- Sends instructions to the laptop agent.
- Displays connection status and execution results.

**2. Windows Laptop Agent**
- Python-based TCP server.
- Receives and processes client requests.
- Authenticates connections using HMAC-SHA256 challenge-response.
- Manages authenticated sessions.
- Validates commands and permissions.
- Executes approved application-launching operations.

## Current Features

- Android-to-Windows communication over a local network.
- TCP socket communication.
- JSON-based message exchange.
- HMAC-SHA256 challenge-response authentication.
- Session-based authentication with expiration.
- Application discovery and resolution.
- Application launching through an allowlist.
- Command parsing and workflow planning.
- Permission-based command execution.
- Error handling and automated tests.

### Currently supported applications

- Google Chrome
- Microsoft Edge
- Visual Studio Code
- Windows Notepad

Additional applications will be supported as development continues.

## Security Design

Security is a core design consideration.

Current security mechanisms include:

- Shared-secret authentication.
- HMAC-SHA256 challenge-response.
- Session expiration.
- Server-side command validation.
- Application allowlisting.
- Capability-based authorization.
- Restricted command execution.

**Security note:** The current TCP transport does not provide encryption. Use this implementation only on a trusted local network while developing. TLS and additional production security controls are planned.

Never commit shared secrets, passwords, private keys, or environment files.

## Project Structure

```text
PersonalCommand/
│
├── android-app/
│   └── PersonalCommand/
│       └── app/
│
├── laptop-agent/
│   ├── intelligence/
│   ├── tests/
│   ├── server.py
│   ├── application_manager.py
│   ├── app_launcher_lab.py
│   ├── workflow_service.py
│   └── client_test.py
│
├── .gitignore
└── README.md
```

## Development Status

| Component | Status |
|---|---|
| Android application UI | Completed |
| TCP communication | Implemented |
| Authentication | Implemented |
| Session management | Implemented |
| Application discovery | Implemented |
| Application resolution | Implemented |
| Application launching | Implemented |
| Command parsing | Implemented |
| Workflow planning | Implemented |
| Policy validation | Implemented |
| Automated laptop-agent tests | 50 passing |
| Additional application support | In progress |
| Transport encryption | Planned |

## Development Goals

Future development will focus on:

- Supporting more Windows applications.
- Improving natural-language command understanding.
- Strengthening network security.
- Adding encrypted communication.
- Improving Android connection management.
- Expanding automated integration testing.

## Disclaimer

PersonalCommand is an experimental personal development project. It is not currently intended for production or deployment on untrusted networks.

## Author

Developed by [Akshay Gor](https://github.com/AkshayGor2006).

GitHub: https://github.com/AkshayGor2006