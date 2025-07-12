from datetime import datetime
from agents import Agent
from .types import EvaluationFeedback

def get_execution_eval_prompt(now: datetime, pass_threshold: float = 0.75) -> str:
    return f"""
Evaluate the Slack research report formatting (1-5 scale each):

1. Markdown Structure
	• Proper headers, lists, and emphasis
	• Clean section organization

2. Link Formatting
	• Permalinks not raw URLs
	• Proper markdown link syntax

3. Length & Readability
	• Under 4000 characters
	• Clear, scannable format

4. Name Resolution
	• User names resolved from Slack IDs
	• Proper capitalization

Total Score = sum of all 4. Pass if >= {pass_threshold * 100}% of 20.
Return scores, total, pass status, and feedback.

Current time: {now.isoformat()}
"""

def init_execution_eval_agent(now: datetime, pass_threshold: float = 0.7):
    return Agent(
        name="Execution Evaluation Agent",
        instructions=get_execution_eval_prompt(now, pass_threshold),
        output_type=EvaluationFeedback,
    )
