from pydantic import BaseModel, Field

class EvaluationFeedback(BaseModel):
    scores: str = Field(description="Detailed scoring breakdown")
    total_score: int = Field(description="Total numerical score")
    passed: bool = Field(description="Whether the evaluation passed")
    feedback: str = Field(description="Detailed feedback and recommendations")
