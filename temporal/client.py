from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from config import settings


async def connect() -> Client:
    connect_args = {
        "target_host": settings.temporal_host_port,
        "data_converter": pydantic_data_converter,
        "namespace": settings.temporal_namespace,
    }

    if settings.temporal_api_key:
        connect_args.update({
            "api_key": settings.temporal_api_key,
            "tls": True,
        })

    return await Client.connect(**connect_args)
