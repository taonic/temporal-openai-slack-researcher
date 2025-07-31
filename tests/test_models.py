from agents import (
    ModelResponse,
    Usage
)
from temporalio.contrib.openai_agents import (
    TestModel,
)
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
)
from research_agents.plan_agent import PlanningResult
from research_agents.plan_eval_agent import EvaluationFeedback


class StaticTestModel(TestModel):
    __test__ = False
    responses: list[ModelResponse] = []

    def response(self):
        global response_index
        response = self.responses[response_index]
        response_index += 1
        return response

    def __init__(
        self,
    ) -> None:
        global response_index
        response_index = 0
        super().__init__(self.response)

class CombinedAgentTestModel(StaticTestModel):
    responses = [
        ModelResponse(
            output=[
                ResponseFunctionToolCall(
                    type="function_call",
                    name="get_slack_channels",
                    arguments='{"request": {"include_archived": false}}',
                    call_id="call",
                    id="id",
                    status="completed",
                )
            ],
            usage=Usage(),
            response_id=None,
        ),
        ModelResponse(
            output=[
                ResponseOutputMessage(
                    id="",
                    content=[
                        ResponseOutputText(
                            text="final result",
                            annotations=[],
                            type="output_text",
                        )
                    ],
                    role="assistant",
                    status="completed",
                    type="message",
                )
            ],
            usage=Usage(),
            response_id=None,
        ),
    ]

class MultiAgentTestModel(StaticTestModel):
    responses = [
        ModelResponse(
            output=[
                ResponseFunctionToolCall(
                    type="function_call",
                    name="get_slack_channels",
                    arguments='{"request": {"include_archived": false}}',
                    call_id="call",
                    id="id",
                    status="completed",
                )
            ],
            usage=Usage(),
            response_id=None,
        ),
        ModelResponse(
            output=[
                ResponseOutputMessage(
                    id="",
                    content=[
                        ResponseOutputText(
                            text=PlanningResult(
                                clarifying_questions="",
                                human_input_required=False,
                                plan="search a,b,c"
                            ).model_dump_json(),
                            annotations=[],
                            type="output_text",
                        )
                    ],
                    role="assistant",
                    status="completed",
                    type="message",
                )
            ],
            usage=Usage(),
            response_id=None,
        ),
        ModelResponse(
            output=[
                ResponseOutputMessage(
                    id="",
                    content=[
                        ResponseOutputText(
                            text=EvaluationFeedback(
                                scores="5",
                                total_score=20,
                                passed=True,
                                feedback="very good plan"
                            ).model_dump_json(),
                            annotations=[],
                            type="output_text",
                        )
                    ],
                    role="assistant",
                    status="completed",
                    type="message",
                )
            ],
            usage=Usage(),
            response_id=None,
        ),
        ModelResponse(
            output=[
                ResponseOutputMessage(
                    id="",
                    content=[
                        ResponseOutputText(
                            text="my summary is blah",
                            annotations=[],
                            type="output_text",
                        )
                    ],
                    role="assistant",
                    status="completed",
                    type="message",
                )
            ],
            usage=Usage(),
            response_id=None,
        ),        
    ]
