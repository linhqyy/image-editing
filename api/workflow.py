import copy
import json
from pathlib import Path

_HERE = Path(__file__).parent
_FILENAME = "image_flux2_klein_image_edit_4b_distilled.json"

# Search order: worker-comfyui/ (local/CI), project root (container), absolute /
_CANDIDATES = [
    _HERE.parent / "worker-comfyui" / _FILENAME,
    _HERE.parent / _FILENAME,
    Path("/") / _FILENAME,
]
_WORKFLOW_PATH = next((p for p in _CANDIDATES if p.exists()), _CANDIDATES[0])

with open(_WORKFLOW_PATH, "r") as _f:
    _WORKFLOW_TEMPLATE: dict = json.load(_f)

UPLOAD_IMAGE_NAME = "input.png"


def build_workflow() -> dict:
    wf = copy.deepcopy(_WORKFLOW_TEMPLATE)

    if "76" in wf:
        wf["76"]["inputs"]["image"] = UPLOAD_IMAGE_NAME

    if "75:73" in wf:
        wf["75:73"]["inputs"]["control_after_generate"] = "fixed"

    return wf
