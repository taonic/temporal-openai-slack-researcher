from __future__ import annotations as _annotations

from temporalio import workflow

from pydantic import BaseModel

from research_agents.plan_agent import init_plan_agent, PlanningResult
from research_agents.execution_agent import init_execution_agent
from research_agents.plan_eval_agent import init_plan_eval_agent
from research_agents.types import EvaluationFeedback

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

class ProcessUserMessageInput(BaseModel):
    user_input: str


@workflow.defn
class ConversationWorkflow:
    @workflow.init
    def __init__(self):
        self.run_config: RunConfig = RunConfig(
            trace_include_sensitive_data=False,
        )
        self.plan_agent: Agent = init_plan_agent(now=workflow.now())
        self.plan_eval_agent: Agent = init_plan_eval_agent(workflow.now())
        self.execution_agent: Agent = init_execution_agent(now=workflow.now())
        self.chat_history: list[str] = []
        self.chain_of_thoughts: list[str] = []
        self.trace_name: str = "Slack Research Bot"
        self.input_items = []
        self.evaluation_enabled: bool = True
        self.max_evaluation_loops: int = 2

    @workflow.run
    async def run(self):
        await workflow.wait_condition(
            lambda: workflow.info().is_continue_as_new_suggested()
            and workflow.all_handlers_finished()
        )
        workflow.continue_as_new(self.input_items)

    @workflow.query
    def get_chat_history(self, watermark: int=0) -> list[str]:
        return self.chain_of_thoughts[watermark:]

    @workflow.update
    async def process_user_message(self, input: ProcessUserMessageInput) -> str:
        self.chat_history.append(f"User: {input.user_input}")
        with trace(self.trace_name, group_id=workflow.info().workflow_id):
            self.input_items.append({"content": input.user_input, "role": "user"})
            
            result = await self._run_with_evaluation()
            
            self._build_chat_history(result)
            self.input_items = result.to_input_list()
        workflow.set_current_details("\n\n".join(self.chat_history))

        if isinstance(result.final_output, PlanningResult):
            return result.final_output.clarifying_questions
        
        return result.final_output
    
    async def _run_with_evaluation(self) -> RunResult:
        """Run with explicit evaluation flow control."""
        
        plan_result = None
        exec_result = None
        
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
                self.chain_of_thoughts.append(f"This is what I'm planning to do: \n{result.plan}")
        
            # Evaluate plan
            eval_result = await Runner.run(
                self.plan_eval_agent,
                plan_result.to_input_list(),
                run_config=self.run_config,
            )
            result: EvaluationFeedback = eval_result.final_output
            self.chain_of_thoughts.append(f'The plan has been reviewed by my team mate with the following comments: \n{result.feedback}')
            
            # Move on if passed
            if not self.evaluation_enabled or result.passed:
                break
            
            # Provide feedback
            plan_input = plan_result.to_input_list()
            plan_input.append({"content": f"Plan evaluation feedback: {result.feedback}", "role": "user"})
        
        # 2. Execution phase
        self.chain_of_thoughts.append("Ok, let me take the feedback and execute the plan. This may take a few moments.")
        exec_input = plan_result.to_input_list()
        exec_result = await Runner.run(
            self.execution_agent,
            exec_input,
            run_config=self.run_config,
        )
        
        return exec_result

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

    @process_user_message.validator
    def validate_process_user_message(self, input: ProcessUserMessageInput) -> None:
        if not input.user_input:
            raise ValueError("User input cannot be empty.")
        if len(input.user_input) > 1000:
            raise ValueError("User input is too long. Please limit to 1000 characters.")
