import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response

load_dotenv(Path(__file__).parent.parent / ".env")

from runpod_client import call_runsync
from workflow import UPLOAD_IMAGE_NAME, build_workflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource

_OTEL_ENABLED = os.getenv("OTEL_ENABLED", "false").lower() == "true"
_JAEGER_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "comfyui-api")

if _OTEL_ENABLED:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    resource = Resource.create({"service.name": _SERVICE_NAME})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=_JAEGER_ENDPOINT, insecure=True))
    )
    trace.set_tracer_provider(provider)
    logger.info("OpenTelemetry tracing enabled → %s", _JAEGER_ENDPOINT)
else:
    logger.info("OpenTelemetry tracing disabled (set OTEL_ENABLED=true to enable)")

tracer = trace.get_tracer(__name__)

app = FastAPI(
    title="ComfyUI Image Edit API",
    description="Edit images using Flux.2 Klein 4B Distilled via RunPod serverless.",
    version="1.0.0",
)

if _OTEL_ENABLED:
    FastAPIInstrumentor.instrument_app(app)


@app.get("/health", tags=["Utility"])
async def health():
    """Liveness check."""
    return {"status": "ok"}


@app.get("/debug-workflow", tags=["Utility"])
async def debug_workflow():
    """Return the built workflow JSON so you can verify patches are applied."""
    wf = build_workflow()
    return JSONResponse({
        "UPLOAD_IMAGE_NAME": UPLOAD_IMAGE_NAME,
        "node_76_image_input": wf.get("76", {}).get("inputs", {}).get("image", "NOT FOUND"),
        "node_75_73_seed_control": wf.get("75:73", {}).get("inputs", {}).get("control_after_generate", "NOT FOUND"),
    })


@app.post(
    "/edit-image",
    response_class=Response,
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "The edited image as PNG.",
        }
    },
    tags=["Image Edit"],
)
async def edit_image(
    image: UploadFile = File(..., description="Source image to edit"),
):
    with tracer.start_as_current_span("edit_image") as span:
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded image is empty.")

        span.set_attribute("image.filename", image.filename or "unknown")
        span.set_attribute("image.size_bytes", len(image_bytes))
        logger.info("Received request | file=%s size=%d bytes", image.filename, len(image_bytes))

        workflow = build_workflow()

        try:
            with tracer.start_as_current_span("runpod_call"):
                output_bytes = await call_runsync(
                    workflow=workflow,
                    image_bytes=image_bytes,
                    image_name=UPLOAD_IMAGE_NAME,
                )
        except RuntimeError as exc:
            logger.error("RunPod job error: %s", exc)
            span.record_exception(exc)
            raise HTTPException(status_code=502, detail=str(exc))
        except Exception as exc:
            logger.exception("Unexpected error calling RunPod")
            span.record_exception(exc)
            raise HTTPException(status_code=500, detail=str(exc))

        span.set_attribute("output.size_bytes", len(output_bytes))
        logger.info("Returning output image (%d bytes)", len(output_bytes))
        return Response(content=output_bytes, media_type="image/png")
