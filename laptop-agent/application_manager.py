import os
import shutil
import winreg

from pathlib import Path


class ApplicationManager:

    """
    Discovers approved applications installed on Windows.

    Responsibilities:
    1. Maintain known application identities.
    2. Search Windows Registry App Paths.
    3. Search executable PATH entries.
    4. Resolve application names to executable paths.

    This component does not launch applications.
    """

    # Applications Aegis knows how to identify.
    APPLICATIONS = {
        "NOTEPAD": {
            "name": "Notepad",
            "executable": "notepad.exe",
            "aliases": ["notepad", "text editor"]
        },

        "EDGE": {
            "name": "Microsoft Edge",
            "executable": "msedge.exe",
            "aliases": ["edge", "microsoft edge"]
        },

        "CHROME": {
            "name": "Google Chrome",
            "executable": "chrome.exe",
            "aliases": ["chrome", "google chrome"]
        },

        "VSCODE": {
            "name": "Visual Studio Code",
            "executable": "code.exe",
            "aliases": ["vscode", "vs code", "visual studio code"]
        },

        "ANDROID_STUDIO": {
            "name": "Android Studio",
            "executable": "studio64.exe",
            "aliases": ["android studio"]
        },

        "INTELLIJ": {
            "name": "IntelliJ IDEA",
            "executable": "idea64.exe",
            "aliases": ["intellij", "intellij idea"]
        }
    }

    REGISTRY_PATH = (
        r"Software\Microsoft\Windows\CurrentVersion\App Paths"
    )

    def __init__(self):

        self.discovered_applications = {}

    # ---------------------------------
    # STEP 1: SEARCH WINDOWS REGISTRY
    # ---------------------------------

    def _find_in_registry(self, executable):

        registry_roots = [
            winreg.HKEY_CURRENT_USER,
            winreg.HKEY_LOCAL_MACHINE
        ]

        for root in registry_roots:

            key_path = (
                f"{self.REGISTRY_PATH}\\{executable}"
            )

            try:

                with winreg.OpenKey(
                    root,
                    key_path
                ) as key:

                    executable_path, _ = winreg.QueryValueEx(
                        key,
                        None
                    )

                    executable_path = os.path.expandvars(
                        executable_path.strip('"')
                    )

                    path = Path(executable_path)

                    if path.is_file():
                        return str(path)

            except (FileNotFoundError, OSError):
                continue

        return None

    # ---------------------------------
    # STEP 2: SEARCH SYSTEM PATH
    # ---------------------------------

    def _find_in_path(self, executable):

        executable_path = shutil.which(executable)

        if executable_path:

            path = Path(executable_path)

            if path.is_file():
                return str(path)

        return None

    # ---------------------------------
    # STEP 3: DISCOVER ONE APPLICATION
    # ---------------------------------

    def discover_application(self, application_id):

        application = self.APPLICATIONS.get(
            application_id
        )

        if application is None:
            return None

        executable = application["executable"]

        # Search Windows Registry first.
        path = self._find_in_registry(executable)

        source = "registry"

        # If not found, search PATH.
        if path is None:

            path = self._find_in_path(executable)

            source = "path"

        if path is None:
            return None

        result = {
            "id": application_id,
            "name": application["name"],
            "executable": executable,
            "path": path,
            "source": source
        }

        self.discovered_applications[
            application_id
        ] = result

        return result

    # ---------------------------------
    # STEP 4: DISCOVER ALL KNOWN APPS
    # ---------------------------------

    def discover_all(self):

        discovered = {}

        for application_id in self.APPLICATIONS:

            result = self.discover_application(
                application_id
            )

            if result is not None:

                discovered[application_id] = result

        return discovered

        # ---------------------------------
    # STEP 5: NORMALIZE APPLICATION NAME
    # ---------------------------------

    def normalize_application_name(self, user_input):

        if not isinstance(user_input, str):
            return None

        normalized = user_input.strip().casefold()

        if not normalized:
            return None

        return normalized

    # ---------------------------------
    # STEP 6: RESOLVE APPLICATION IDENTITY
    # ---------------------------------

    def resolve_application(self, user_input):

        normalized = self.normalize_application_name(
            user_input
        )

        if normalized is None:
            return {
                "status": "error",
                "message": "Invalid application name"
            }

        for application_id, application in self.APPLICATIONS.items():

            possible_names = [
                application_id,
                application["name"],
                application["executable"],
                *application["aliases"]
            ]

            normalized_names = [
                name.casefold()
                for name in possible_names
            ]

            if normalized in normalized_names:

                return {
                    "status": "success",
                    "application_id": application_id,
                    "name": application["name"],
                    "executable": application["executable"]
                }

        return {
            "status": "error",
            "message": "Application not recognized"
        }

        # ---------------------------------
    # STEP 7: RESOLVE AND DISCOVER
    # ---------------------------------

    def resolve_and_discover(self, user_input):

        # Step 1: Resolve application identity.
        resolution = self.resolve_application(user_input)

        if resolution["status"] != "success":
            return resolution

        application_id = resolution["application_id"]

        # Step 2: Discover the actual executable.
        discovered = self.discover_application(application_id)

        if discovered is None:
            return {
                "status": "error",
                "message": "Application is recognized but not installed or discoverable.",
                "application_id": application_id,
                "name": resolution["name"]
            }

        # Step 3: Return the complete application record.
        return {
            "status": "success",
            "application": discovered
        }