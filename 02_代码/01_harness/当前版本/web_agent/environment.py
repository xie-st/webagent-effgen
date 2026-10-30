"""Startup checks for the pinned EffGen runtime.

The harness deliberately refuses to start on an unpinned or missing framework.
The version and public symbols are read from the installed distribution; the
official SDK is checked separately by ``run.py``.
"""
from __future__ import annotations

from importlib import metadata
from pathlib import Path
import sys
from typing import Any

REQUIRED_PYTHON = (3, 11)
REQUIRED_EFFGEN = "1.3.0"


class EnvironmentError(RuntimeError):
    """The runtime does not satisfy the pinned M1a environment."""


def _lock_versions(lock_path: Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    for line in lock_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            raise EnvironmentError(
                f"Unpinned requirement in {lock_path.name}: {line}"
            )
        name, version = line.split("==", 1)
        versions[name.strip()] = version.strip()
    return versions


def report(lock_path: str | Path | None = None) -> dict[str, Any]:
    if sys.version_info < REQUIRED_PYTHON:
        raise EnvironmentError(
            "EffGen 1.3.0 requires Python 3.11+; current interpreter is "
            + sys.version.split()[0]
        )
    try:
        import effgen
        from effgen import Agent, AgentConfig, BaseModel  # noqa: F401
        from effgen.core.agent import AgentMode  # noqa: F401
    except ImportError as exc:
        raise EnvironmentError(
            "EffGen is not installed. Create the pinned environment with "
            "'python -m pip install -r requirements.lock'."
        ) from exc
    version = getattr(effgen, "__version__", None)
    distribution_version = metadata.version("effgen")
    if version != REQUIRED_EFFGEN or distribution_version != REQUIRED_EFFGEN:
        raise EnvironmentError(
            f"EffGen must be exactly {REQUIRED_EFFGEN}; import reports "
            f"{version!r}, installed distribution reports {distribution_version!r}"
        )
    if not callable(Agent) or not callable(AgentConfig):
        raise EnvironmentError("EffGen public Agent/AgentConfig surface is incomplete")
    if not isinstance(BaseModel, type):
        raise EnvironmentError("EffGen public BaseModel surface is incomplete")

    lock = Path(lock_path) if lock_path is not None else (
        Path(__file__).resolve().parents[1] / "requirements.lock"
    )
    if not lock.is_file():
        raise EnvironmentError(f"Pinned dependency lock is missing: {lock}")
    mismatches = []
    for name, expected in _lock_versions(lock).items():
        try:
            actual = metadata.version(name)
        except metadata.PackageNotFoundError:
            mismatches.append(f"{name}: missing (expected {expected})")
            continue
        if actual != expected:
            mismatches.append(f"{name}: {actual} (expected {expected})")
    if mismatches:
        raise EnvironmentError(
            "Installed dependencies differ from requirements.lock: "
            + "; ".join(mismatches[:8])
            + (" ..." if len(mismatches) > 8 else "")
        )
    return {
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "effgen": version,
        "effgen_path": str(Path(effgen.__file__).resolve().parent),
        "agent_mode": AgentMode.SINGLE.value,
        "lock": lock.name,
        "locked_packages": len(_lock_versions(lock)),
    }


def check() -> dict[str, Any]:
    value = report()
    print(
        "PASS: environment python={python} effgen={effgen} path={effgen_path}".format(
            **value
        )
    )
    return value


__all__ = [
    "EnvironmentError",
    "REQUIRED_EFFGEN",
    "REQUIRED_PYTHON",
    "check",
    "report",
]
