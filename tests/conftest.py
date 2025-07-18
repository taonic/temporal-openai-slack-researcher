import pytest_asyncio
from typing import AsyncGenerator

from temporalio.testing import WorkflowEnvironment
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

def pytest_addoption(parser):
    parser.addoption(
        "--workflow-environment",
        default="local",
        help="Which workflow environment to use ('local', 'time-skipping', or target to existing server)",
    )

@pytest_asyncio.fixture
async def client(env: WorkflowEnvironment) -> Client:
    new_config = env.client.config()
    new_config["data_converter"] = pydantic_data_converter
    return Client(**new_config)

@pytest_asyncio.fixture(scope="session")
async def env(request) -> AsyncGenerator[WorkflowEnvironment, None]:
    env_type = request.config.getoption("--workflow-environment")
    if env_type == "local":
        env = await WorkflowEnvironment.start_local(
            dev_server_extra_args=[
                "--dynamic-config-value",
                "frontend.enableExecuteMultiOperation=true",
            ]
        )
    elif env_type == "time-skipping":
        env = await WorkflowEnvironment.start_time_skipping()
    else:
        env = WorkflowEnvironment.from_client(await Client.connect(env_type))
    yield env
    await env.shutdown()
