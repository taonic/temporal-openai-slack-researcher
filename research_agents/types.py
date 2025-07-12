from pydantic import BaseModel, Field

class EvaluationFeedback(BaseModel):
    scores: str = Field(description="Detailed scoring breakdown")
    total_score: int = Field(description="Total numerical score")
    passed: bool = Field(description="Whether the evaluation passed")
    feedback: str = Field(description="Detailed feedback and recommendations")

class PlanningResult(BaseModel):
    clarifying_questions: str = Field(description="Either clarifying questions if input unclear, or detailed search plan if clear")
    human_input_required: bool = Field(description="True if clarifying questions needed, False if plan is ready")
    plan: str = Field(description="Detailed search plan if clarifying questions not needed")
