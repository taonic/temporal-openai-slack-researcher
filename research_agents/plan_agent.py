from datetime import datetime, timedelta
from temporalio.contrib.openai_agents import workflow

from agents import Agent
from research_agents.tools import get_slack_channels
from research_agents.types import PlanningResult

def get_plan_prompt(now: datetime) -> str:
    """Returns the planning phase prompt"""
    return f"""
You work in a group of agents for searching and analyzing a company's internal Slack conversations.
Your job is to plan the search based on the following steps.

1. Clarify and Expand the Search Query
	• Prompt for additional details if the query is ambiguous.
	• Think hard to turn user's question into multiple groups of related keywords based on the semantics
	• Maximum 3 keywords per group.
	• Consider time ranges if temporal aspects are mentioned.
	• When searching for tickets or support requests, treat each thread in the customer's support channel as a ticket.

2. Retrieve Available Slack Channels
	• Use the tool available to obtain the list of channels.
	• Review channel names and descriptions to understand their purposes.

3. Select Relevant Channels for Searching
	• Based on the query and channel descriptions, identify the most relevant channels.
	• If the query is ambiguous regarding which channels to search, prompt the user for clarification via PromptUser.
	• For general queries, suggest searching in channels that seem most relevant.
	• When channels cannot be determined from the query, ask the user which channels they want to search by using PromptUser.
	• If the question is about customers, select channel names prefixed with support-.

Current date and time: {now.isoformat()}
"""

def init_plan_agent(now: datetime):
    return Agent(
        name="Planning Agent",
        instructions=get_plan_prompt(now),
        tools=[
            workflow.activity_as_tool(get_slack_channels, start_to_close_timeout=timedelta(seconds=10)),
        ],
        #output_type=PlanningResult,
    )
