import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app_launcher_lab import ApplicationLauncher


class TestApplicationLauncher(unittest.TestCase):

    def setUp(self):

        self.temp_dir = tempfile.TemporaryDirectory()

        self.fake_executable = (
            Path(self.temp_dir.name) / "notepad.exe"
        )

        self.fake_executable.touch()

        self.manager = Mock()

        self.launcher = ApplicationLauncher(
            application_manager=self.manager
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_successful_launch(self):

        self.manager.resolve_and_discover.return_value = {
            "status": "success",
            "application": {
                "id": "NOTEPAD",
                "name": "Notepad",
                "path": str(self.fake_executable)
            }
        }

        with patch(
            "app_launcher_lab.subprocess.Popen"
        ) as mock_popen:

            mock_popen.return_value.pid = 1234

            result = self.launcher.launch_application(
                "Notepad"
            )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["application_id"], "NOTEPAD")
        mock_popen.assert_called_once()

    def test_unknown_application_rejected(self):

        self.manager.resolve_and_discover.return_value = {
            "status": "error",
            "message": "Application not recognized"
        }

        with patch(
            "app_launcher_lab.subprocess.Popen"
        ) as mock_popen:

            result = self.launcher.launch_application(
                "Unknown App"
            )

        self.assertEqual(result["status"], "error")
        mock_popen.assert_not_called()

    def test_missing_executable_rejected(self):

        self.manager.resolve_and_discover.return_value = {
            "status": "success",
            "application": {
                "id": "NOTEPAD",
                "name": "Notepad",
                "path": str(
                    Path(self.temp_dir.name) / "missing.exe"
                )
            }
        }

        with patch(
            "app_launcher_lab.subprocess.Popen"
        ) as mock_popen:

            result = self.launcher.launch_application(
                "Notepad"
            )

        self.assertEqual(result["status"], "error")
        mock_popen.assert_not_called()

    def test_relative_path_rejected(self):

        self.manager.resolve_and_discover.return_value = {
            "status": "success",
            "application": {
                "id": "NOTEPAD",
                "name": "Notepad",
                "path": "notepad.exe"
            }
        }

        with patch(
            "app_launcher_lab.subprocess.Popen"
        ) as mock_popen:

            result = self.launcher.launch_application(
                "Notepad"
            )

        self.assertEqual(result["status"], "error")
        mock_popen.assert_not_called()

    def test_invalid_application_record_rejected(self):

        self.manager.resolve_and_discover.return_value = {
            "status": "success",
            "application": {}
        }

        with patch(
            "app_launcher_lab.subprocess.Popen"
        ) as mock_popen:

            result = self.launcher.launch_application(
                "Notepad"
            )

        self.assertEqual(result["status"], "error")
        mock_popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()