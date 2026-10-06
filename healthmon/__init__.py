"""Concurrent HTTP health checks for small services and APIs."""

from .monitor import CheckResult, Target, run_checks

__all__ = ["CheckResult", "Target", "run_checks"]
__version__ = "0.1.0"
