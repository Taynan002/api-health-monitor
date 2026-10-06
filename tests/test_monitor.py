import unittest
from urllib import error

from healthmon.monitor import Target, build_report, check_target


class FakeResponse:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class SequenceOpener:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def __call__(self, request, timeout):
        outcome = self.outcomes[self.calls]
        self.calls += 1
        if isinstance(outcome, Exception):
            raise outcome
        return FakeResponse(outcome)


class MonitorTests(unittest.TestCase):
    def test_success_on_first_attempt(self):
        target = Target(name="API", url="https://example.com")
        opener = SequenceOpener([200])

        result = check_target(target, opener=opener)

        self.assertTrue(result.ok)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.attempts, 1)

    def test_retries_until_success(self):
        target = Target(
            name="API",
            url="https://example.com",
            retries=2,
        )
        opener = SequenceOpener(
            [error.URLError("temporary"), 503, 200]
        )

        result = check_target(target, opener=opener)

        self.assertTrue(result.ok)
        self.assertEqual(result.attempts, 3)
        self.assertEqual(opener.calls, 3)

    def test_reports_failure_after_retries(self):
        target = Target(
            name="API",
            url="https://example.com",
            retries=1,
        )
        opener = SequenceOpener([500, 503])

        result = check_target(target, opener=opener)

        self.assertFalse(result.ok)
        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.attempts, 2)

    def test_build_report(self):
        ok = check_target(
            Target(name="A", url="https://a.example"),
            opener=SequenceOpener([200]),
        )
        failed = check_target(
            Target(name="B", url="https://b.example", retries=0),
            opener=SequenceOpener([500]),
        )

        report = build_report([ok, failed])

        self.assertEqual(report["summary"]["total"], 2)
        self.assertEqual(report["summary"]["healthy"], 1)
        self.assertEqual(report["summary"]["unhealthy"], 1)
        self.assertEqual(report["summary"]["healthy_percent"], 50.0)


if __name__ == "__main__":
    unittest.main()
