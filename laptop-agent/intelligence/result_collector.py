from datetime import datetime, timezone


class ResultCollector:
    """
    Collects and structures workflow execution results.

    Responsibilities:
    1. Validate execution results.
    2. Extract individual step information.
    3. Calculate execution statistics.
    4. Generate a readable summary.
    5. Return a structured report.
    """

    VALID_STATUSES = {
        "success",
        "failed",
        "rejected",
        "requires_confirmation"
    }

    VALID_STEP_STATUSES = {
        "success",
        "error"
    }

    def collect(self, execution_result):

        # 1. Validate the incoming execution result.

        if not isinstance(execution_result, dict):
            return self._invalid_result()

        status = execution_result.get("status")

        if status not in self.VALID_STATUSES:
            return self._invalid_result()

        raw_results = execution_result.get("results")

        if not isinstance(raw_results, list):
            return self._invalid_result()

        # 2. Extract and validate individual step results.

        collected_results = []

        for result in raw_results:

            if not isinstance(result, dict):
                return self._invalid_result()

            step = result.get("step")
            command = result.get("command")
            step_status = result.get("status")
            message = result.get("message", "")

            if not isinstance(step, int) or isinstance(step, bool):
                return self._invalid_result()

            if step < 1:
                return self._invalid_result()

            if not isinstance(command, str) or not command:
                return self._invalid_result()

            if step_status not in self.VALID_STEP_STATUSES:
                return self._invalid_result()

            if not isinstance(message, str):
                return self._invalid_result()

            collected_results.append({
                "step": step,
                "command": command,
                "status": step_status,
                "message": message
            })

        # 3. Calculate statistics from actual results.

        total_steps = len(collected_results)

        successful_steps = sum(
            1
            for result in collected_results
            if result["status"] == "success"
        )

        failed_steps = sum(
            1
            for result in collected_results
            if result["status"] == "error"
        )

        # 4. Generate a human-readable summary.

        summary = self._generate_summary(
            status,
            total_steps,
            successful_steps,
            failed_steps
        )

        # 5. Create the final report.

        return {
            "status": status,
            "message": summary,
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "results": collected_results,
            "completed_at": datetime.now(
                timezone.utc
            ).isoformat()
        }

    @staticmethod
    def _generate_summary(
        status,
        total_steps,
        successful_steps,
        failed_steps
    ):

        if status == "success":

            return (
                f"Workflow completed successfully. "
                f"{successful_steps}/{total_steps} actions completed."
            )

        if status == "failed":

            return (
                f"Workflow stopped. "
                f"{successful_steps} actions succeeded and "
                f"{failed_steps} actions failed."
            )

        if status == "rejected":

            return "Workflow was rejected by the security policy."

        if status == "requires_confirmation":

            return "User confirmation is required before execution."

        return "Workflow result unavailable."

    @staticmethod
    def _invalid_result():

        return {
            "status": "error",
            "message": "Invalid execution result received.",
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "results": [],
            "completed_at": datetime.now(
                timezone.utc
            ).isoformat()
        }