from datetime import datetime
from agents import (
    Agent,
    ModelSettings,
)
from temporalio import workflow
from pydantic import BaseModel, Field

class EvaluationFeedback(BaseModel):
    scores: str = Field(description="Detailed scoring breakdown")
    total_score: int = Field(description="Total numerical score")
    passed: bool = Field(description="Whether the evaluation passed")
    feedback: str = Field(description="Detailed feedback and recommendations")

with workflow.unsafe.imports_passed_through():
    from config import settings

def get_plan_eval_prompt(now: datetime, pass_threshold: float = 0.67) -> str:
    return f"""
You work in a group of agents for searching and analyzing a company's internal Slack conversations.
You are an evaluator assessing the quality of the search planning phase.
Evaluate the planning based on these criteria (1-5 scale each):

1. Query Understanding
- Was the original query properly understood?
- Were ambiguities identified and clarified?
- Are the keyword groups semantically relevant?
- Maximum 3 keywords per group maintained?

2. Channel Selection
- Were all available channels properly retrieved?
- Are the selected channels relevant to the query?
- Was proper logic applied (e.g., support- prefix for customer queries)?
- Were users prompted for clarification when needed?

3. Search Strategy
- Are the planned keyword groups comprehensive?
- Is the time range consideration appropriate?
- Will the planned approach likely yield relevant results?

Total Score = sum of all 3. If Total >= {pass_threshold * 100}% of maximum possible score then PASS, else CONTINUES TO IMPROVE.
Return:
- Scores for each criterion
- Total Score
- Pass: true or false
- Detailed feedback:
  - Include feedback under each criterion.
  - Include a overall score by 1 to 5 stars (⭐️).

Current date and time: {now.isoformat()}
"""

def init_plan_eval_agent(now: datetime, pass_threshold: float = 0.7):
    return Agent(
        name="Plan Evaluation Agent",
        instructions=get_plan_eval_prompt(now, pass_threshold),
        model_settings=ModelSettings(temperature=0),
        model=settings.eval_model_name,
        output_type=EvaluationFeedback,
    )
