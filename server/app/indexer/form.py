import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.catalog.tags import ESTIMATOR_FORMATS, ESTIMATOR_MAX_SECONDS, ONE_SHOT_MAX_SECONDS

DEFAULT_ESTIMATOR_COMMAND = "armarium-loop-tempo"
_ESTIMATOR_TIMEOUT_SECONDS = 15.0


@dataclass(frozen=True, slots=True)
class FormEstimate:
    is_loop: bool | None
    bpm: float | None


def should_estimate_form(format_name: str, duration_seconds: float | None) -> bool:
    if format_name not in ESTIMATOR_FORMATS:
        return False
    if duration_seconds is None:
        return False
    return ONE_SHOT_MAX_SECONDS <= duration_seconds <= ESTIMATOR_MAX_SECONDS


def estimate_form(
    path: Path,
    command: str = DEFAULT_ESTIMATOR_COMMAND,
) -> FormEstimate:
    try:
        completed = subprocess.run(
            [command, str(path)],
            capture_output=True,
            text=True,
            timeout=_ESTIMATOR_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return FormEstimate(None, None)
    if completed.returncode != 0:
        return FormEstimate(None, None)
    return _parse_estimate(completed.stdout)


def estimator_for(command: str) -> Callable[[Path], FormEstimate]:
    def run(path: Path) -> FormEstimate:
        return estimate_form(path, command)

    return run


def _parse_estimate(raw: str) -> FormEstimate:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return FormEstimate(None, None)
    if not isinstance(payload, dict):
        return FormEstimate(None, None)
    is_loop = payload.get("loop")
    if not isinstance(is_loop, bool):
        return FormEstimate(None, None)
    bpm = payload.get("bpm")
    if bpm is None:
        return FormEstimate(is_loop, None)
    if not isinstance(bpm, (int, float)) or isinstance(bpm, bool):
        return FormEstimate(is_loop, None)
    return FormEstimate(is_loop, float(bpm))
