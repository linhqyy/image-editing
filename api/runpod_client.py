import asyncio
import base64
import logging
import os

import httpx

logger = logging.getLogger(__name__)

RUNPOD_API_KEY = os.environ["RUNPOD_API_KEY"]
RUNPOD_ENDPOINT_ID = os.environ["RUNPOD_ENDPOINT_ID"]
COMFYUI_TIMEOUT = int(os.getenv("COMFYUI_TIMEOUT", "300"))

BASE_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}"
HEADERS = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json",
}
POLL_INTERVAL = 5  
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"}


async def call_runsync(
    workflow: dict,
    image_bytes: bytes,
    image_name: str = "input.png",
) -> bytes:
    payload = {
        "input": {
            "workflow": workflow,
            "images": [
                {"name": image_name, "image": base64.b64encode(image_bytes).decode()}
            ],
        }
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{BASE_URL}/run", json=payload, headers=HEADERS)
        r.raise_for_status()

        job_id = r.json()["id"]
        logger.info("Job submitted: %s", job_id)

        elapsed = 0
        while elapsed < COMFYUI_TIMEOUT:
            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

            sr = await client.get(f"{BASE_URL}/status/{job_id}", headers=HEADERS)
            sr.raise_for_status()
            result = sr.json()
            status = result.get("status")
            logger.info("Job %s — %s (%ds)", job_id, status, elapsed)

            if status not in TERMINAL:
                continue

            if status != "COMPLETED":
                raise RuntimeError(
                    f"RunPod job failed with status '{status}': "
                    f"{result.get('error', 'unknown')}. Raw: {result}"
                )

            output = result.get("output", {})

            images = output.get("images", [])
            if not images:
                raise RuntimeError(f"Job completed but returned no images. Full output: {output}")

            image_b64 = images[0].get("data", "")
            if not image_b64:
                raise RuntimeError(f"Output image data is empty. Image entry: {images[0]}")

            return base64.b64decode(image_b64)

    raise RuntimeError(f"Timeout after {COMFYUI_TIMEOUT}s — job {job_id} not done.")

