from __future__ import annotations as _annotations

from temporalio import workflow

from pydantic import BaseModel

from research_agents.plan_agent import init_plan_agent, PlanningResult
from research_agents.execution_agent import init_execution_agent
from research_agents.plan_eval_agent import init_plan_eval_agent, EvaluationFeedback
from research_agents.combined_agent import init_combined_agent
from temporal.activities import post_to_slack, PostToSlackInput

with workflow.unsafe.imports_passed_through():
    from agents import (
        Agent,
        HandoffOutputItem,
        ItemHelpers,
        MessageOutputItem,
        RunConfig,
        Runner,
        RunResult,
        ToolCallItem,
        ToolCallOutputItem,
        trace,
    )
    from config import settings

class ProcessUserMessageInput(BaseModel):
    user_input: str
    thread_ts: str = None
    channel_id: str = None


@workflow.defn
class ConversationWorkflow:
    @workflow.init
    def __init__(self, research_mode: str = ""):
        self.research_mode = research_mode
        self.run_config: RunConfig = RunConfig(
            trace_include_sensitive_data=False,
        )
        self.plan_agent: Agent = init_plan_agent(now=workflow.now())
        self.plan_eval_agent: Agent = init_plan_eval_agent(workflow.now())
        self.execution_agent: Agent = init_execution_agent(now=workflow.now())
        self.combined_agent: Agent = init_combined_agent(now=workflow.now())
        self.chat_history: list[str] = []
        self.trace_name: str = "Slack Research Bot"
        self.input_items = []
        self.evaluation_enabled: bool = True
        self.max_evaluation_loops: int = 2
        self.thread_ts: str = None
        self.channel_id: str = None

    @workflow.run
    async def run(self, research_mode: str = ""):
        await workflow.wait_condition(
            lambda: workflow.info().is_continue_as_new_suggested()
            and workflow.all_handlers_finished()
        )
        workflow.continue_as_new(self.input_items)

    @workflow.signal
    async def process_user_message(self, input: ProcessUserMessageInput) -> None:
        self.thread_ts = input.thread_ts
        self.channel_id = input.channel_id

        if len(self.chat_history) == 0:
            await self._post_to_slack(f"[view workflow]({settings.temporal_ui_url}/namespaces/{settings.temporal_namespace}/workflows/{workflow.info().workflow_id})")

        self.chat_history.append(f"User: {input.user_input}")
        with trace(self.trace_name, group_id=workflow.info().workflow_id):
            self.input_items.append({"content": input.user_input, "role": "user"})
            
            if self.research_mode == "with_judge":
                result = await self._run_with_judge()
            else:
                result = await self._run_without_judge()
            
            self._build_chat_history(result)
            self.input_items = result.to_input_list()

        if isinstance(result.final_output, PlanningResult):
            await self._post_to_slack(result.final_output.clarifying_questions)
        elif isinstance(result.final_output, MessageOutputItem):
            await self._post_to_slack(ItemHelpers.text_message_output(result.final_output))
        else:
            await self._post_to_slack(str(result.final_output))
            
        workflow.set_current_details("\n\n".join(self.chat_history))

    async def _run_with_judge(self) -> RunResult:
        """Run with explicit evaluation flow control."""

        plan_result = None
        exec_result = None
        plan = ""

        # 1. Planning phase with LLM-as-a-judge
        for _ in range(self.max_evaluation_loops):
            # Run plan agent
            plan_input = self.input_items
            plan_result = await Runner.run(
                self.plan_agent,
                plan_input,
                run_config=self.run_config,
            )
            result: PlanningResult = plan_result.final_output
            if result.human_input_required:
                return plan_result
            else:
                message = f"This is what I'm planning to do: \n{result.plan}"
                plan = result.plan
                await self._post_to_slack(message)

            # Evaluate plan
            eval_result = await Runner.run(
                self.plan_eval_agent,
                plan_result.to_input_list(),
                run_config=self.run_config,
            )
            result: EvaluationFeedback = eval_result.final_output
            message = f'The plan has been reviewed by my team mate with the following comments: \n{result.feedback}'
            await self._post_to_slack(message)
            
            # Move on if passed
            if not self.evaluation_enabled or result.passed:
                break
            
            # Provide feedback
            plan_input = plan_result.to_input_list()
            plan_input.append({"content": f"Plan evaluation feedback: {result.feedback}", "role": "user"})

        # 2. Execution phase
        message = "Ok, let me take the feedback and execute the plan. This may take a few moments."
        await self._post_to_slack(message)
        exec_input = plan_result.to_input_list()
        exec_input.append({"content": f'Final plan to execute: {plan}', "role": "user"})
        exec_result = await Runner.run(
            self.execution_agent,
            exec_input,
            run_config=self.run_config,
            max_turns=30,
        )
        
        return exec_result

    async def _run_without_judge(self) -> RunResult:
        """Run with combined agent (no evaluation)."""
        return await Runner.run(
            self.combined_agent,
            self.input_items,
            run_config=self.run_config,
        )

    async def _post_to_slack(self, message: str) -> None:
        await workflow.execute_activity(
            post_to_slack,
            PostToSlackInput(
                message=message,
                channel_id=self.channel_id,
                thread_ts=self.thread_ts
            ),
            start_to_close_timeout=workflow.timedelta(seconds=30)
        )

    def _build_chat_history(self, result: RunResult) -> None:
        for new_item in result.new_items:
                agent_name = new_item.agent.name
                if isinstance(new_item, MessageOutputItem):
                    self.chat_history.append(
                        f"{agent_name}: {ItemHelpers.text_message_output(new_item)}"
                    )
                elif isinstance(new_item, HandoffOutputItem):
                    self.chat_history.append(
                        f"Handed off from {new_item.source_agent.name} to {new_item.target_agent.name}"
                    )
                elif isinstance(new_item, ToolCallItem):
                    self.chat_history.append(f"{agent_name}: Calling a tool")
                elif isinstance(new_item, ToolCallOutputItem):
                    self.chat_history.append(
                        f"{agent_name}: Tool call output: {new_item.output}"
                    )
                else:
                    self.chat_history.append(
                        f"{agent_name}: Skipping item: {new_item.__class__.__name__}"
                    )
