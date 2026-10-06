from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from .monitor import Target


class ConfigError(ValueError):
    pass


def _validated_url(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("Each target must define a non-empty 'url'.")

    url = value.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigError(f"Unsupported target URL: {url!r}")

    return url


def load_config(path: Path) -> list[Target]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"Could not read config: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON config: {exc}") from exc

    raw_targets = payload.get("targets") if isinstance(payload, dict) else None
    if not isinstance(raw_targets, list) or not raw_targets:
        raise ConfigError("Config must contain a non-empty 'targets' list.")

    targets: list[Target] = []
    for index, item in enumerate(raw_targets, start=1):
        if not isinstance(item, dict):
            raise ConfigError(f"Target #{index} must be an object.")

        url = _validated_url(item.get("url"))
        name = item.get("name") or url
        if not isinstance(name, str):
            raise ConfigError(f"Target #{index} has an invalid name.")

        expected = item.get("expected_statuses", [200])
        if (
            not isinstance(expected, list)
            or not expected
            or any(not isinstance(code, int) for code in expected)
        ):
            raise ConfigError(
                f"Target #{index} expected_statuses must be a non-empty integer list."
            )

        timeout = item.get("timeout", 5.0)
        retries = item.get("retries", 1)

        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ConfigError(f"Target #{index} timeout must be > 0.")
        if not isinstance(retries, int) or retries < 0:
            raise ConfigError(f"Target #{index} retries must be >= 0.")

        targets.append(
            Target(
                name=name.strip() or url,
                url=url,
                expected_statuses=tuple(expected),
                timeout=float(timeout),
                retries=retries,
            )
        )

    return targets
