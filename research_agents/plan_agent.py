from datetime import datetime, timedelta
from temporalio.contrib.openai_agents import workflow
from pydantic import BaseModel, Field

from agents import Agent, WebSearchTool
from research_agents.tools import get_slack_channels, search_slack

class PlanningResult(BaseModel):
    clarifying_questions: str = Field(description="Either clarifying questions if input unclear, or detailed search plan if clear")
    human_input_required: bool = Field(description="True if clarifying questions needed, False if plan is ready")
    plan: str = Field(description="Detailed search plan if clarifying questions not needed")

def get_plan_prompt(now: datetime) -> str:
    """Returns the planning phase prompt"""
    return f"""
You work in a group of agents for searching and analyzing a company's internal Slack conversations.
Your job is to plan the search based on the following steps.

1. Clarify and Expand the Search Query
	• Use WebSearchTool for terminology you don't understand.
	• Think hard to turn user's question into multiple groups of related keywords based on the semantics
	• Do a basic slack search to build some context.
	• Maximum 3 keywords per group.
	• Consider time ranges if temporal aspects are mentioned.
	• When searching for tickets or support requests, treat each thread in the customer's support channel as a ticket.
	• Prompt for additional details if the query is still ambiguous.
	• Don't ask which channel to search.

2. Retrieve Available Slack Channels
	• Use the tool available to obtain the list of channels.
	• Review channel names and descriptions to understand their purposes.

3. Select Relevant Channels for Searching
	• Based on the query and channel descriptions, identify the most relevant channels.
	• If the query is ambiguous regarding which channels to search, prompt the user for clarification via PromptUser.
	• For general queries, suggest searching in channels that seem most relevant.
	• When channels cannot be determined from the query, ask the user which channels they want to search by using PromptUser.
	• If the question is about customers, select channel names prefixed with support-.

4. Articulate the Search Plan
	• Clearly state the key words and keyword groups that will be used for searching.
	• List the specific channels that will be searched.
	• Explain the rationale for the selected keywords and channels.
	• Include any time ranges or filters that will be applied.
	• End with a confidence level: 🔴 (low), 🟡 (medium), or 🟢 (high) based on how well the available channels and keywords match the user's query.

IMPORTANT: If the user's question is not clear enough or lacks sufficient detail to create an effective search plan, return clarifying questions in the clarifying_questions field and set human_input_required to true. Otherwise, return the detailed search plan in clarifying_questions field and set human_input_required to false.

Current date and time: {now.isoformat()}
"""

def init_plan_agent(now: datetime):
    return Agent(
        name="Planning Agent",
        instructions=get_plan_prompt(now),
        tools=[
            WebSearchTool(),
            workflow.activity_as_tool(get_slack_channels, start_to_close_timeout=timedelta(seconds=10)),
            workflow.activity_as_tool(search_slack, start_to_close_timeout=timedelta(seconds=10)),
        ],
        output_type=PlanningResult,
    )
