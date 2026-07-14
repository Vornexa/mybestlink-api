import os
import unittest
from unittest.mock import patch

from src.config import Settings


class SettingsTest(unittest.TestCase):
    def test_defaults_are_secure_and_development_friendly(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings.from_env()

        self.assertEqual(settings.host, "0.0.0.0")
        self.assertEqual(settings.port, 8000)
        self.assertTrue(settings.verify_ssl)
        self.assertEqual(settings.request_timeout_seconds, 30.0)

    def test_environment_overrides_are_parsed(self):
        environment = {
            "MYBESTLINK_HOST": "127.0.0.1",
            "MYBESTLINK_PORT": "9000",
            "MYBESTLINK_VERIFY_SSL": "false",
            "MYBESTLINK_REQUEST_TIMEOUT": "12.5",
            "MYBESTLINK_COOKIE_FILE": "var/test-cookies.json",
        }

        with patch.dict(os.environ, environment, clear=True):
            settings = Settings.from_env()

        self.assertEqual(settings.host, "127.0.0.1")
        self.assertEqual(settings.port, 9000)
        self.assertFalse(settings.verify_ssl)
        self.assertEqual(settings.request_timeout_seconds, 12.5)
        self.assertEqual(str(settings.cookie_file), "var\\test-cookies.json")

    def test_invalid_boolean_is_rejected(self):
        with patch.dict(
            os.environ,
            {"MYBESTLINK_VERIFY_SSL": "sometimes"},
            clear=True,
        ), self.assertRaisesRegex(ValueError, "MYBESTLINK_VERIFY_SSL"):
            Settings.from_env()

    def test_invalid_port_and_timeout_are_rejected(self):
        with patch.dict(
            os.environ, {"MYBESTLINK_PORT": "70000"}, clear=True
        ), self.assertRaisesRegex(ValueError, "MYBESTLINK_PORT"):
            Settings.from_env()

        with patch.dict(
            os.environ,
            {"MYBESTLINK_REQUEST_TIMEOUT": "0"},
            clear=True,
        ), self.assertRaisesRegex(ValueError, "MYBESTLINK_REQUEST_TIMEOUT"):
            Settings.from_env()


if __name__ == "__main__":
    unittest.main()
