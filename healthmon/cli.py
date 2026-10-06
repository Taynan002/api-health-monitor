from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import ConfigError, load_config
from .monitor import build_report, render_text, run_checks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="api-health",
        description="Run concurrent health checks defined in a JSON config file.",
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to a JSON target configuration",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Print the report as JSON",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Maximum concurrent checks (default: 4)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.workers < 1:
        raise SystemExit("--workers must be >= 1")

    try:
        targets = load_config(args.config)
    except ConfigError as exc:
        raise SystemExit(str(exc)) from exc

    results = run_checks(targets, max_workers=args.workers)
    report = build_report(results)

    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))

    return 0 if report["summary"]["unhealthy"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
