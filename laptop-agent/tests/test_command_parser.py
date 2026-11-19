import unittest

from intelligence.command_parser import CommandParser


class TestCommandParser(unittest.TestCase):

    def setUp(self):
        self.parser = CommandParser()

    def test_google_search(self):

        result = self.parser.parse(
            "Open Google and search who is Elon Musk"
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["intent"], "google_search")

        self.assertEqual(
            result["actions"][0]["command"],
            "OPEN_EDGE"
        )

        self.assertIn(
            "Elon",
            result["actions"][0]["arguments"]["url"]
        )

    def test_open_notepad(self):

        result = self.parser.parse("Open Notepad")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(
            result["actions"][0]["command"],
            "OPEN_APPLICATION"
        )
        self.assertEqual(
            result["actions"][0]["arguments"]["application"],
            "Notepad"
        )

    def test_open_edge(self):

        result = self.parser.parse("Launch Microsoft Edge")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(
            result["actions"][0]["command"],
            "OPEN_EDGE"
        )

    def test_empty_command(self):

        result = self.parser.parse("")

        self.assertEqual(result["status"], "error")

    def test_unknown_command(self):

        result = self.parser.parse(
            "Delete all files on my laptop"
        )

        self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main()