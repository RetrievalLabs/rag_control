"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from rag_control.exceptions import ControlPlaneConfigValidationError
from rag_control.models.config import ControlPlaneConfig

import yaml

def load_control_plane_config(path: str | Path) -> ControlPlaneConfig:
    config_path = Path(path)

    if not config_path.exists():
        raise ControlPlaneConfigValidationError(
            f"control plane config file does not exist: '{config_path}'"
        )
    if not config_path.is_file():
        raise ControlPlaneConfigValidationError(
            f"control plane config path is not a file: '{config_path}'"
        )

    try:
        raw_content = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ControlPlaneConfigValidationError(
            f"unable to read control plane config file: '{config_path}'"
        ) from exc

    try:
        parsed: Any = yaml.safe_load(raw_content)
    except yaml.YAMLError as exc:
        raise ControlPlaneConfigValidationError(
            f"invalid YAML in control plane config: '{config_path}'"
        ) from exc

    if parsed is None:
        parsed = {}
    if not isinstance(parsed, dict):
        raise ControlPlaneConfigValidationError(
            "control plane config root must be a mapping/object"
        )

    try:
        return ControlPlaneConfig.model_validate(parsed)
    except ValidationError as exc:
        raise ControlPlaneConfigValidationError(
            f"invalid control plane config: {exc}"
        ) from exc
