# API Health Monitor

A lightweight Python CLI for checking multiple HTTP endpoints concurrently and producing clear health reports for automation or human review.

The project focuses on practical reliability concerns: timeouts, retries, expected status codes, latency measurement, structured output, and meaningful process exit codes.

> Built as an independent portfolio project. No proprietary or private project code is included.

## Features

- Concurrent checks with a configurable worker limit
- Per-target timeout settings
- Per-target retry counts
- Multiple acceptable HTTP status codes
- Latency measurement
- Human-readable output
- JSON output for automation
- Exit code `0` when every target is healthy
- Exit code `1` when one or more targets fail
- JSON configuration validation
- Standard-library runtime: no third-party runtime dependencies
- Automated unit tests
- GitHub Actions CI on Python 3.10 and 3.12

## Quick start

```bash
git clone https://github.com/Taynan002/api-health-monitor.git
cd api-health-monitor
python -m pip install -e .
```

Run the included example configuration:

```bash
api-health examples/targets.json
```

Structured output:

```bash
api-health examples/targets.json --json
```

Limit concurrency:

```bash
api-health examples/targets.json --workers 2
```

## Configuration

Create a JSON file with one or more targets:

```json
{
  "targets": [
    {
      "name": "Public API",
      "url": "https://example.com/health",
      "expected_statuses": [200, 204],
      "timeout": 3,
      "retries": 2
    }
  ]
}
```

Fields:

| Field | Required | Description |
| --- | --- | --- |
| `url` | yes | HTTP or HTTPS endpoint |
| `name` | no | Human-readable target name |
| `expected_statuses` | no | Accepted HTTP statuses; defaults to `[200]` |
| `timeout` | no | Request timeout in seconds; defaults to `5` |
| `retries` | no | Retry count after the first attempt; defaults to `1` |

## Example text report

```text
API health report
=================
Healthy: 2/2 (100.0%)

[OK] Example homepage status=200 latency=84.12 ms attempts=1
[OK] HTTP 204 endpoint status=204 latency=116.40 ms attempts=1
```

## Automation-friendly behavior

The command returns a non-zero exit code when any configured target remains unhealthy after its retry budget is exhausted.

That makes it easy to use in scripts or simple scheduled checks:

```bash
api-health production-targets.json --json > health-report.json
```

## Project structure

```text
.
├── .github/workflows/tests.yml
├── examples/targets.json
├── healthmon/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   └── monitor.py
├── tests/
│   ├── test_config.py
│   └── test_monitor.py
├── LICENSE
├── README.md
└── pyproject.toml
```

## Running tests

```bash
python -m unittest discover -s tests -v
```

The unit tests do not depend on live external services. HTTP behavior is simulated with test doubles so CI remains deterministic.

## Design choices

**Small operational surface.** Runtime behavior uses the Python standard library only.

**Failure-aware.** Unexpected HTTP statuses, network errors, timeout-like failures, and retry exhaustion are represented explicitly.

**Automation-ready.** JSON output and process exit codes make the tool useful beyond interactive CLI use.

**Deterministic tests.** Network behavior is mocked rather than relying on third-party services during the test suite.

## License

MIT
