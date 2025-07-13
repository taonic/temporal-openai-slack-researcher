from datetime import datetime, timedelta
from temporalio import workflow
from temporalio.contrib.openai_agents import workflow as agent_workflow

from agents import Agent, WebSearchTool
from research_agents.tools import (
    get_slack_channels,
    search_slack,
    get_thread_messages,
    get_user_name,
)

with workflow.unsafe.imports_passed_through():
    from config import settings

def get_combined_prompt(now: datetime) -> str:
    return f"""
You work as a comprehensive Slack research agent that both plans and executes searches in a company's internal Slack conversations.

PHASE 1: PLANNING
1. Query Analysis & Context Building
- Use WebSearchTool for unfamiliar terminology
- Turn user's question into keyword groups (max 3 keywords per group)
- Consider time ranges if mentioned
- For support/tickets, treat each thread in support channels as a ticket

2. Channel Discovery & Selection
- Retrieve available Slack channels
- Select relevant channels based on query context
- For customer queries, prioritize channels prefixed with support-

PHASE 2: EXECUTION
3. Global Search
- Execute searches using keyword groups without channel filters
- Don't quote keywords or use OR operators
- Include time ranges if relevant
- Show keywords used

4. Channel-Specific Search
- Execute targeted searches in selected channels
- Use refined keyword groups
- Show keywords and channels used

5. Analysis & Reporting
- Analyze results from both searches
- Use get_user_name for proper user identification
- Format as Markdown report under 4000 characters with:
  - Summary of findings
  - Examples with formatted links
  - Important decisions/actions
  - Key participants (max 5, properly capitalized)
  - Self-reflection on search completeness

Always assume searching internal Slack workspace. Present final analysis in structured Markdown format.

Current date and time: {now.isoformat()}
"""

def init_combined_agent(now: datetime):
    return Agent(
        name="Combined Research Agent",
        instructions=get_combined_prompt(now),
        tools=[
            WebSearchTool(),
            agent_workflow.activity_as_tool(get_slack_channels, start_to_close_timeout=timedelta(seconds=10)),
            agent_workflow.activity_as_tool(search_slack, start_to_close_timeout=timedelta(seconds=10)),
            agent_workflow.activity_as_tool(get_thread_messages, start_to_close_timeout=timedelta(seconds=10)),
            agent_workflow.activity_as_tool(get_user_name, start_to_close_timeout=timedelta(seconds=10)),
        ],
        model=settings.model_name,
    )