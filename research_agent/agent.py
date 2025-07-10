from datetime import datetime, timedelta
from research_agent.tools import get_slack_channels, search_slack, get_thread_messages, get_user_name
from temporalio.contrib.openai_agents.temporal_tools import activity_as_tool
from research_agent.sys_prompt import get_system_prompt

from agents import Agent

def init_agent(now: datetime):
    return Agent(
        name="Slack Research Agent",
        instructions=get_system_prompt(now),
        tools=[
            activity_as_tool(get_slack_channels, start_to_close_timeout=timedelta(seconds=10)),
            activity_as_tool(get_slack_channels, start_to_close_timeout=timedelta(seconds=10)),
            activity_as_tool(search_slack, start_to_close_timeout=timedelta(seconds=10)),
            activity_as_tool(get_thread_messages, start_to_close_timeout=timedelta(seconds=10)),
            activity_as_tool(get_user_name, start_to_close_timeout=timedelta(seconds=10)),
        ],
    )
