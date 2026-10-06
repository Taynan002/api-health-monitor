import json
from pathlib import Path
import tempfile
import unittest

from healthmon.config import ConfigError, load_config


class ConfigTests(unittest.TestCase):
    def write_config(self, payload):
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            delete=False,
        )
        with handle:
            json.dump(payload, handle)
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return Path(handle.name)

    def test_loads_valid_target(self):
        path = self.write_config(
            {
                "targets": [
                    {
                        "name": "Example",
                        "url": "https://example.com/health",
                        "expected_statuses": [200, 204],
                        "timeout": 2,
                        "retries": 2,
                    }
                ]
            }
        )

        targets = load_config(path)
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0].name, "Example")
        self.assertEqual(targets[0].expected_statuses, (200, 204))
        self.assertEqual(targets[0].retries, 2)

    def test_rejects_non_http_url(self):
        path = self.write_config(
            {"targets": [{"url": "file:///tmp/health"}]}
        )
        with self.assertRaises(ConfigError):
            load_config(path)


if __name__ == "__main__":
    unittest.main()
