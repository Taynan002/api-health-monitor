from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
import time
from typing import Iterable
from urllib import error, request


@dataclass(frozen=True)
class Target:
    name: str
    url: str
    expected_statuses: tuple[int, ...] = (200,)
    timeout: float = 5.0
    retries: int = 1


@dataclass(frozen=True)
class CheckResult:
    name: str
    url: str
    ok: bool
    status_code: int | None
    latency_ms: float | None
    attempts: int
    error: str | None = None


def check_target(target: Target, opener=None) -> CheckResult:
    """Probe one target and retry transient failures or unexpected statuses."""
    if opener is None:
        opener = request.urlopen

    last_error: str | None = None
    last_status: int | None = None
    last_latency: float | None = None

    for attempt in range(1, target.retries + 2):
        req = request.Request(
            target.url,
            method="GET",
            headers={"User-Agent": "api-health-monitor/0.1"},
        )
        started = time.perf_counter()

        try:
            with opener(req, timeout=target.timeout) as response:
                status = getattr(response, "status", None)
                if status is None:
                    status = response.getcode()

            latency = round((time.perf_counter() - started) * 1000, 2)
            last_status = int(status)
            last_latency = latency

            if last_status in target.expected_statuses:
                return CheckResult(
                    name=target.name,
                    url=target.url,
                    ok=True,
                    status_code=last_status,
                    latency_ms=latency,
                    attempts=attempt,
                )

            last_error = (
                f"Unexpected HTTP status {last_status}; "
                f"expected {list(target.expected_statuses)}"
            )

        except error.HTTPError as exc:
            latency = round((time.perf_counter() - started) * 1000, 2)
            last_status = exc.code
            last_latency = latency

            if exc.code in target.expected_statuses:
                return CheckResult(
                    name=target.name,
                    url=target.url,
                    ok=True,
                    status_code=exc.code,
                    latency_ms=latency,
                    attempts=attempt,
                )

            last_error = f"HTTP error {exc.code}"

        except (error.URLError, TimeoutError, OSError) as exc:
            last_latency = round((time.perf_counter() - started) * 1000, 2)
            reason = getattr(exc, "reason", exc)
            last_error = f"{type(exc).__name__}: {reason}"

    return CheckResult(
        name=target.name,
        url=target.url,
        ok=False,
        status_code=last_status,
        latency_ms=last_latency,
        attempts=target.retries + 1,
        error=last_error or "Unknown failure",
    )


def run_checks(targets: Iterable[Target], max_workers: int = 4) -> list[CheckResult]:
    target_list = list(targets)
    if max_workers < 1:
        raise ValueError("max_workers must be >= 1")
    if not target_list:
        return []

    worker_count = min(max_workers, len(target_list))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        return list(executor.map(check_target, target_list))


def build_report(results: Iterable[CheckResult]) -> dict:
    result_list = list(results)
    healthy = sum(1 for item in result_list if item.ok)
    total = len(result_list)

    return {
        "summary": {
            "total": total,
            "healthy": healthy,
            "unhealthy": total - healthy,
            "healthy_percent": round((healthy / total) * 100, 2) if total else 0.0,
        },
        "results": [asdict(item) for item in result_list],
    }


def render_text(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "API health report",
        "=================",
        (
            f"Healthy: {summary['healthy']}/{summary['total']} "
            f"({summary['healthy_percent']}%)"
        ),
        "",
    ]

    for item in report["results"]:
        state = "OK" if item["ok"] else "FAIL"
        status = item["status_code"] if item["status_code"] is not None else "-"
        latency = (
            f"{item['latency_ms']:.2f} ms"
            if item["latency_ms"] is not None
            else "-"
        )
        lines.append(
            f"[{state}] {item['name']} status={status} "
            f"latency={latency} attempts={item['attempts']}"
        )
        if item["error"]:
            lines.append(f"       {item['error']}")

    return "\n".join(lines)
