from urllib.parse import urlparse


class PolicyEngine:

    """
    Evaluates whether a planned workflow is permitted.

    This component does not execute commands.
    It only makes security decisions.
    """

    MAX_ACTIONS = 10

    COMMAND_POLICIES = {
        "OPEN_EDGE": {
            "allowed_arguments": {"url"},
            "required_arguments": {"url"},
            "requires_confirmation": False
        },

        "OPEN_NOTEPAD": {
            "allowed_arguments": set(),
            "required_arguments": set(),
            "requires_confirmation": False
        },

        "OPEN_APPLICATION": {
            "allowed_arguments": {"application"},
            "required_arguments": {"application"},
            "requires_confirmation": False
        }
    }

    def evaluate(self, execution_plan):

        # 1. Validate execution plan.

        if not isinstance(execution_plan, dict):
            return self._reject("Invalid execution plan.")

        if execution_plan.get("status") != "ok":
            return self._reject("Execution plan is not valid.")

        steps = execution_plan.get("steps")

        if not isinstance(steps, list) or not steps:
            return self._reject("No workflow steps provided.")

        if len(steps) > self.MAX_ACTIONS:
            return self._reject("Workflow exceeds maximum step limit.")

        approved_steps = []
        confirmation_required = False

        # 2. Evaluate every step.

        for step in steps:

            if not isinstance(step, dict):
                return self._reject("Invalid workflow step.")

            command = step.get("command")
            arguments = step.get("arguments", {})

            # 3. Check whether command is permitted.

            policy = self.COMMAND_POLICIES.get(command)

            if policy is None:
                return self._reject(
                    f"Command is not permitted: {command}"
                )

            # 4. Validate arguments.

            if not isinstance(arguments, dict):
                return self._reject(
                    f"Invalid arguments for {command}."
                )

            allowed = policy["allowed_arguments"]
            required = policy["required_arguments"]

            provided = set(arguments.keys())

            if not provided.issubset(allowed):
                return self._reject(
                    f"Unexpected arguments for {command}."
                )

            if not required.issubset(provided):
                return self._reject(
                    f"Missing required arguments for {command}."
                )

            # 5. Apply command-specific security checks.

            if command == "OPEN_EDGE":

                url = arguments.get("url")

                if not self._is_safe_url(url):
                    return self._reject(
                        "Only valid HTTPS URLs are permitted."
                    )

            if command == "OPEN_APPLICATION":

                application = arguments.get("application")

                if (
                    not isinstance(application, str)
                    or not application.strip()
                    or len(application) > 100
                    or not application.isprintable()
                ):
                    return self._reject("Invalid application name.")

            # 6. Check confirmation requirements.

            if policy["requires_confirmation"]:
                confirmation_required = True

            approved_steps.append(step)

        # 7. Return policy decision.

        if confirmation_required:
            return {
                "status": "requires_confirmation",
                "message": "User confirmation is required.",
                "approved_steps": approved_steps,
                "total_steps": len(approved_steps)
            }

        return {
            "status": "approved",
            "message": "Workflow passed security policy.",
            "approved_steps": approved_steps,
            "total_steps": len(approved_steps)
        }

    @staticmethod
    def _is_safe_url(url):

        if not isinstance(url, str):
            return False

        if not url or len(url) > 2048:
            return False

        try:
            parsed = urlparse(url)

            return (
                parsed.scheme == "https"
                and bool(parsed.hostname)
                and parsed.username is None
                and parsed.password is None
            )

        except ValueError:
            return False

    @staticmethod
    def _reject(message):

        return {
            "status": "rejected",
            "message": message,
            "approved_steps": [],
            "total_steps": 0
        }