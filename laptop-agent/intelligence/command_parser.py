import re
from urllib.parse import urlencode, urlsplit


class CommandParser:

    """
    Converts natural-language instructions
    into structured, predefined actions.

    This parser does not execute commands.
    """

    def parse(self, user_input):

        if not isinstance(user_input, str):
            return self._error("Command must be text.")

        text = user_input.strip()

        if not text:
            return self._error("Command cannot be empty.")

        if len(text) > 500:
            return self._error("Command is too long.")

        normalized = text.lower()

        # --------------------------------
        # INTENT 1: YOUTUBE SEARCH
        # --------------------------------

        youtube_match = re.search(
            r"\bsearch\s+youtube\s+for\s+(.+)",
            text,
            re.IGNORECASE
        )

        if youtube_match:

            query = youtube_match.group(1).strip().rstrip("?.! ")

            if not query:
                return self._error("Search query is missing.")

            url = (
                "https://www.youtube.com/results?"
                + urlencode({"search_query": query})
            )

            return self._browser_action(
                "youtube_search",
                url
            )

        # --------------------------------
        # INTENT 2: GOOGLE SEARCH
        # --------------------------------

        google_match = re.search(
            r"\bsearch(?:\s+for)?\s+(.+)",
            text,
            re.IGNORECASE
        )

        if google_match:

            query = google_match.group(1).strip()

            query = re.sub(
                r"\s+on\s+google\s*$",
                "",
                query,
                flags=re.IGNORECASE
            )

            query = query.rstrip("?.! ")

            if not query:
                return self._error("Search query is missing.")

            url = (
                "https://www.google.com/search?"
                + urlencode({"q": query})
            )

            return self._browser_action(
                "google_search",
                url
            )

        # --------------------------------
# INTENT 3: OPEN APPLICATION
# --------------------------------

        application_aliases = [
            (r"visual\s+studio\s+code|vs\s*code", "VS Code"),
            (r"google\s+chrome|chrome", "Chrome"),
            (r"android\s+studio", "Android Studio"),
            (r"intellij(?:\s+idea)?", "IntelliJ IDEA"),
            (r"notepad", "Notepad"),
        ]

        for pattern, application_name in application_aliases:

            match = re.search(
                rf"\b(?:open|launch|start)\s+(?:the\s+)?(?:{pattern})\b",
                normalized
            )

            if match:
                return {
                    "status": "ok",
                    "intent": "open_application",
                    "actions": [
                        {
                            "command": "OPEN_APPLICATION",
                            "arguments": {
                                "application": application_name
                            }
                        }
                    ],
                    "requires_confirmation": False
                }

        # --------------------------------
        # INTENT 4: OPEN KNOWN WEBSITES
        # --------------------------------

        websites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "github": "https://github.com",
            "stackoverflow": "https://stackoverflow.com",
            "reddit": "https://www.reddit.com",
            "linkedin": "https://www.linkedin.com"
        }

        for name, url in websites.items():

            if re.search(
                rf"\bopen\s+{re.escape(name)}\b",
                normalized
            ):

                return self._browser_action(
                    f"open_{name}",
                    url
                )

        # --------------------------------
        # INTENT 5: OPEN EDGE
        # --------------------------------

        if re.search(
            r"\b(open|launch)\s+(microsoft\s+)?edge\b",
            normalized
        ):

            return self._browser_action(
                "open_browser",
                "https://www.google.com"
            )

        return self._error(
            "I could not understand this command yet."
        )

    @staticmethod
    def _browser_action(intent, url):

        parsed = urlsplit(url)

        if parsed.scheme != "https" or not parsed.hostname:
            return CommandParser._error("Invalid website URL.")

        return {
            "status": "ok",
            "intent": intent,
            "actions": [
                {
                    "command": "OPEN_EDGE",
                    "arguments": {
                        "url": url
                    }
                }
            ],
            "requires_confirmation": False
        }

    @staticmethod
    def _error(message):

        return {
            "status": "error",
            "message": message,
            "actions": []
        }