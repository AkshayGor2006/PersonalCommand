class TaskPlanner:

    """
    Converts parsed actions into an ordered execution plan.

    This component does not execute commands.
    It only organizes and validates the plan structure.
    """

    # Commands currently supported by our laptop server.
    ALLOWED_COMMANDS = {
        "OPEN_EDGE",
        "OPEN_NOTEPAD",
        "OPEN_APPLICATION"
    }

    # Define which arguments each command accepts.
    COMMAND_ARGUMENTS = {
        "OPEN_EDGE": {"url"},
        "OPEN_NOTEPAD": set(),
        "OPEN_APPLICATION": {"application"}
    }

    MAX_ACTIONS = 10

    def create_plan(self, parsed_command):

        # 1. Validate parser output.

        if not isinstance(parsed_command, dict):
            return self._error("Invalid parser output.")

        if parsed_command.get("status") != "ok":
            return self._error("Cannot plan an invalid command.")

        actions = parsed_command.get("actions")

        if not isinstance(actions, list) or not actions:
            return self._error("No actions were provided.")

        if len(actions) > self.MAX_ACTIONS:
            return self._error("Workflow contains too many actions.")

        # 2. Build the execution plan.

        steps = []

        for index, action in enumerate(actions, start=1):

            # Validate action structure.

            if not isinstance(action, dict):
                return self._error("Invalid action structure.")

            command = action.get("command")
            arguments = action.get("arguments", {})

            # Validate command.

            if command not in self.ALLOWED_COMMANDS:
                return self._error(
                    f"Unsupported command: {command}"
                )

            # Validate arguments.

            if not isinstance(arguments, dict):
                return self._error(
                    f"Invalid arguments for {command}."
                )

            allowed_arguments = self.COMMAND_ARGUMENTS[command]

            if not set(arguments.keys()).issubset(allowed_arguments):
                return self._error(
                    f"Unexpected arguments for {command}."
                )

            if command == "OPEN_EDGE":
                url = arguments.get("url")

                if url is not None and not isinstance(url, str):
                    return self._error("Invalid browser URL.")

            if command == "OPEN_APPLICATION":
                application = arguments.get("application")

                if not isinstance(application, str) or not application.strip():
                    return self._error("Invalid application name.")

            # 3. Create an ordered workflow step.

            step = {
                "step": index,
                "command": command,
                "arguments": arguments,
                "status": "pending"
            }

            steps.append(step)

        # 4. Return the completed plan.

        return {
            "status": "ok",
            "intent": parsed_command.get("intent", "unknown"),
            "total_steps": len(steps),
            "steps": steps,
            "requires_confirmation": parsed_command.get(
                "requires_confirmation",
                True
            )
        }

    @staticmethod
    def _error(message):

        return {
            "status": "error",
            "message": message,
            "steps": []
        }