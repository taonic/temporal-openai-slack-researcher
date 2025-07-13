import dataclasses

import temporalio.converter
from temporalio.client import Client
from temporalio.converter import DataConverter
from temporalio.contrib.pydantic import pydantic_data_converter

from config import settings
from temporal.codec import EncryptionCodec


async def connect() -> Client:
    print("🔌 Connecting to Temporal")
    connect_args = {
        "target_host": settings.temporal_host_port,
        "data_converter": pydantic_data_converter,
        "namespace": settings.temporal_namespace,
    }

    if settings.temporal_api_key:
        print("- Using API key")
        connect_args.update({
            "api_key": settings.temporal_api_key,
            "tls": True,
        })

    dataConverter = DataConverter.default
    if settings.temporal_codec_key:
        print("- Encrypting payloads")
        dataConverter = dataclasses.replace(
            temporalio.converter.default(), payload_codec=EncryptionCodec(settings.temporal_codec_key)
        )
        connect_args.update({
            "data_converter": dataConverter,
        })

    return await Client.connect(**connect_args)
