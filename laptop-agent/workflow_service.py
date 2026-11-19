from intelligence.command_parser import CommandParser
from intelligence.task_planner import TaskPlanner
from intelligence.policy_engine import PolicyEngine
from intelligence.workflow_executor import WorkflowExecutor
from intelligence.result_collector import ResultCollector


class WorkflowService:

    """
    Coordinates the complete natural-language workflow.

    Pipeline:

    User Input
        |
        v
    Command Parser
        |
        v
    Task Planner
        |
        v
    Policy Engine
        |
        v
    Workflow Executor
        |
        v
    Result Collector
        |
        v
    Final Response

    This class coordinates components.
    It does not implement their internal logic.
    """

    def __init__(self, command_handlers):

        """
        Initialize all workflow components.

        command_handlers:
            A dictionary containing registered command
            handlers used by the WorkflowExecutor.
        """

        # 1. Understand natural-language instructions.
        self.parser = CommandParser()

        # 2. Convert parsed actions into an execution plan.
        self.planner = TaskPlanner()

        # 3. Check whether the execution plan is permitted.
        self.policy_engine = PolicyEngine()

        # 4. Execute only approved registered actions.
        self.executor = WorkflowExecutor(command_handlers)

        # 5. Convert execution results into a readable report.
        self.result_collector = ResultCollector()


    def process(
        self,
        user_input,
        confirmation_granted=False,
        authorization_check=None
    ):

        """
        Process one natural-language instruction.

        confirmation_granted:
            False = Do not execute actions requiring confirmation.
            True  = Explicit confirmation has been supplied.

        Returns:
            A structured workflow result.
        """

        # -----------------------------------------
        # STEP 1: PARSE USER INPUT
        # -----------------------------------------

        parsed_command = self.parser.parse(user_input)

        if parsed_command.get("status") != "ok":

            return {
                "status": "error",
                "message": parsed_command.get(
                    "message",
                    "Could not understand the instruction."
                ),
                "results": []
            }


        # -----------------------------------------
        # STEP 2: CREATE EXECUTION PLAN
        # -----------------------------------------

        execution_plan = self.planner.create_plan(
            parsed_command
        )

        if execution_plan.get("status") != "ok":

            return {
                "status": "error",
                "message": execution_plan.get(
                    "message",
                    "Could not create execution plan."
                ),
                "results": []
            }

        # -----------------------------------------
        # SECURITY: AUTHORIZE EVERY WORKFLOW ACTION
        # -----------------------------------------

        if authorization_check is not None:

            if not callable(authorization_check):
                return {
                    "status": "error",
                    "message": "Invalid authorization checker.",
                    "results": []
                }

            if not authorization_check(execution_plan):
                return {
                    "status": "rejected",
                    "message": "Workflow permission denied.",
                    "results": []
                }


        # -----------------------------------------
        # STEP 3: EVALUATE SECURITY POLICY
        # -----------------------------------------

        policy_decision = self.policy_engine.evaluate(
            execution_plan
        )


        # -----------------------------------------
        # STEP 4: EXECUTE APPROVED WORKFLOW
        # -----------------------------------------

        execution_result = self.executor.execute(
            policy_decision,
            confirmation_granted=confirmation_granted
        )


        # -----------------------------------------
        # STEP 5: COLLECT EXECUTION RESULTS
        # -----------------------------------------

        final_report = self.result_collector.collect(
            execution_result
        )


        # -----------------------------------------
        # STEP 6: ADD WORKFLOW METADATA
        # -----------------------------------------

        if final_report.get("status") == "error":
            return final_report

        final_report["intent"] = execution_plan.get(
            "intent",
            "unknown"
        )

        final_report["requires_confirmation"] = (
            final_report["status"] == "requires_confirmation"
        )

        return final_report