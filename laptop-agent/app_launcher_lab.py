import subprocess
from pathlib import Path

from application_manager import ApplicationManager


class ApplicationLauncher:

    def __init__(self, application_manager=None):

        self.application_manager = (
            application_manager or ApplicationManager()
        )

    def launch_application(self, application_name):

        # STEP 1: Resolve and discover the application.

        result = self.application_manager.resolve_and_discover(
            application_name
        )

        if result["status"] != "success":
            return result

        application = result["application"]

        # STEP 2: Retrieve discovered executable path.

        executable = application.get("path")

        if not isinstance(executable, str) or not executable.strip():
            return {
                "status": "error",
                "message": "Executable path is missing."
            }

        path = Path(executable)

        # STEP 3: Validate the executable.

        if not path.is_absolute():
            return {
                "status": "error",
                "message": "Executable path must be absolute."
            }

        if path.suffix.lower() != ".exe":
            return {
                "status": "error",
                "message": "Invalid executable type."
            }

        if not path.is_file():
            return {
                "status": "error",
                "message": "Executable does not exist."
            }

        # STEP 4: Execute without a shell.

        try:

            process = subprocess.Popen(
                [str(path)],
                shell=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        except OSError:
            return {
                "status": "error",
                "message": "Application launch failed."
            }

        # STEP 5: Return structured result.

        return {
            "status": "success",
            "message": "Application launch requested.",
            "application_id": application["id"],
            "application_name": application["name"],
            "executable": str(path),
            "pid": process.pid
        }