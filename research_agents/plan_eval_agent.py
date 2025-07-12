from datetime import datetime
from agents import Agent
from .types import EvaluationFeedback
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
	from config import settings

def get_plan_eval_prompt(now: datetime, pass_threshold: float = 0.67) -> str:
    return f"""
You work in a group of agents for searching and analyzing a company's internal Slack conversations.
You are an evaluator assessing the quality of the search planning phase.
Evaluate the planning based on these criteria (1-5 scale each):

1. Query Understanding
	• Was the original query properly understood?
	• Were ambiguities identified and clarified?
	• Are the keyword groups semantically relevant?
	• Maximum 3 keywords per group maintained?

2. Channel Selection
	• Were all available channels properly retrieved?
	• Are the selected channels relevant to the query?
	• Was proper logic applied (e.g., support- prefix for customer queries)?
	• Were users prompted for clarification when needed?

3. Search Strategy
	• Are the planned keyword groups comprehensive?
	• Is the time range consideration appropriate?
	• Will the planned approach likely yield relevant results?

Total Score = sum of all 3. If Total >= {pass_threshold * 100}% of maximum possible score then PASS, else CONTINUES TO IMPROVE.
Return:
- Scores for each criterion
- Total Score
- Pass: true or false
- Feedback under each criterion

Current date and time: {now.isoformat()}
"""

def init_plan_eval_agent(now: datetime, pass_threshold: float = 0.7):
    return Agent(
        name="Plan Evaluation Agent",
        instructions=get_plan_eval_prompt(now, pass_threshold),
        model=settings.eval_model_name,
        output_type=EvaluationFeedback,
    )
