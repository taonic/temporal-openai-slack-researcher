import dataclasses

import temporalio.converter
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource  # type: ignore
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from temporalio.client import Client
from temporalio.converter import DataConverter
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.runtime import OpenTelemetryConfig, Runtime, TelemetryConfig

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

    if settings.temporal_codec_key:
        print("- Encrypting payloads")
        dataConverter = dataclasses.replace(
            temporalio.converter.default(), payload_codec=EncryptionCodec(settings.temporal_codec_key)
        )
        connect_args.update({
            "data_converter": dataConverter,
        })
        
    if settings.temporal_enable_telemetry:
        print("- Enabling telemetry")
        connect_args.update({
            "runtime": init_runtime_with_telemetry(),
        })

    return await Client.connect(**connect_args)


def init_runtime_with_telemetry() -> Runtime:
    # Setup global tracer for workflow traces
    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: settings.otel_service_name}))
    exporter = OTLPSpanExporter(endpoint=settings.otel_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Setup SDK metrics to OTel endpoint
    return Runtime(
        telemetry=TelemetryConfig(
            metrics=OpenTelemetryConfig(url=settings.otel_endpoint)
        )
    )
