class WorkflowExecutor:
    """
    Executes workflows that have passed the Policy Engine.

    Responsibilities:
    1. Verify policy approval.
    2. Check whether confirmation is required.
    3. Validate each approved action.
    4. Execute actions through registered handlers.
    5. Track individual execution results.
    6. Stop execution when an action fails.

    This component never executes arbitrary shell commands.
    """

    MAX_ACTIONS = 10

    # Only explicitly registered commands can execute.
    COMMAND_ARGUMENTS = {
        "OPEN_EDGE": {"url"},
        "OPEN_APPLICATION": {"application"}
    }

    REQUIRED_ARGUMENTS = {
        "OPEN_EDGE": {"url"},
        "OPEN_APPLICATION": {"application"}
    }

    def __init__(self, command_handlers):
        """
        command_handlers maps permitted command names to functions.

        Example:
        {
            "OPEN_EDGE": open_edge_handler,
            "OPEN_APPLICATION": open_application_handler
        }
        """

        if not isinstance(command_handlers, dict):
            raise TypeError("Command handlers must be a dictionary.")

        self.command_handlers = command_handlers

    def execute(
        self,
        policy_decision,
        confirmation_granted=False
    ):
        """
        Execute a workflow using the Policy Engine's decision.

        A workflow requiring confirmation will not execute
        unless explicit confirmation is supplied.
        """

        # 1. Validate policy decision structure.

        if not isinstance(policy_decision, dict):
            return self._reject("Invalid policy decision.")

        policy_status = policy_decision.get("status")

        # 2. Check policy approval.

        if policy_status == "rejected":
            return self._reject(
                "Workflow was rejected by the Policy Engine."
            )

        if policy_status == "requires_confirmation":

            if confirmation_granted is not True:
                return {
                    "status": "requires_confirmation",
                    "message": "Explicit user confirmation is required.",
                    "results": [],
                    "total_steps": 0,
                    "successful_steps": 0,
                    "failed_steps": 0
                }

        elif policy_status != "approved":

            return self._reject(
                "Workflow has not received policy approval."
            )

        # 3. Retrieve policy-approved actions.

        approved_steps = policy_decision.get("approved_steps")

        if not isinstance(approved_steps, list):
            return self._reject("Invalid approved workflow.")

        if not approved_steps:
            return self._reject("No approved actions to execute.")

        if len(approved_steps) > self.MAX_ACTIONS:
            return self._reject(
                "Workflow exceeds maximum execution limit."
            )

        # 4. Execute each approved action sequentially.

        results = []

        for index, step in enumerate(approved_steps, start=1):

            # Validate step structure.

            if not isinstance(step, dict):
                return self._execution_failure(
                    "Invalid workflow step.",
                    results
                )

            command = step.get("command")
            arguments = step.get("arguments", {})

            # Validate command registration.

            if command not in self.COMMAND_ARGUMENTS:
                return self._execution_failure(
                    f"Command is not permitted: {command}",
                    results
                )

            handler = self.command_handlers.get(command)

            if not callable(handler):
                return self._execution_failure(
                    f"No execution handler registered for {command}.",
                    results
                )

            # Validate arguments.

            if not isinstance(arguments, dict):
                return self._execution_failure(
                    f"Invalid arguments for {command}.",
                    results
                )

            allowed = self.COMMAND_ARGUMENTS[command]
            required = self.REQUIRED_ARGUMENTS[command]

            provided = set(arguments.keys())

            if not provided.issubset(allowed):
                return self._execution_failure(
                    f"Unexpected arguments for {command}.",
                    results
                )

            if not required.issubset(provided):
                return self._execution_failure(
                    f"Missing required arguments for {command}.",
                    results
                )

            # 5. Execute the registered handler.

            try:

                handler_result = handler(arguments)

                if not isinstance(handler_result, dict):
                    raise ValueError("Invalid handler response.")

                execution_status = handler_result.get("status")

                if execution_status not in {"success", "error"}:
                    raise ValueError("Invalid execution status.")

                step_result = {
                    "step": step.get("step", index),
                    "command": command,
                    "status": execution_status,
                    "message": handler_result.get(
                        "message",
                        "No execution message."
                    )
                }

                results.append(step_result)

                # Stop if an action fails.

                if execution_status == "error":

                    return self._execution_failure(
                        f"Execution failed at step {index}.",
                        results
                    )

            except Exception:

                return self._execution_failure(
                    f"Unexpected execution error at step {index}.",
                    results
                )

        # 6. Return completed workflow results.

        return {
            "status": "success",
            "message": "Workflow executed successfully.",
            "results": results,
            "total_steps": len(results),
            "successful_steps": len(results),
            "failed_steps": 0
        }

    @staticmethod
    def _reject(message):

        return {
            "status": "rejected",
            "message": message,
            "results": [],
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0
        }

    @staticmethod
    def _execution_failure(message, results):

        successful = sum(
            1 for result in results
            if result["status"] == "success"
        )

        failed = sum(
            1 for result in results
            if result["status"] == "error"
        )

        return {
            "status": "failed",
            "message": message,
            "results": results,
            "total_steps": len(results),
            "successful_steps": successful,
            "failed_steps": failed
        }