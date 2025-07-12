from pydantic import BaseModel

class EvaluationFeedback(BaseModel):
    scores: str
    total_score: int
    passed: bool
    feedback: str

class PlanningResult(BaseModel):
    plan: str
    human_input_required: bool
