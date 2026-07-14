import json
import tempfile
import unittest
from pathlib import Path

from yarl import URL

from src.config import Settings
from src.service.upstream_client import SessionManager


class SessionManagerTest(unittest.IsolatedAsyncioTestCase):
    async def test_cookies_are_persisted_as_json_and_reloaded(self):
        with tempfile.TemporaryDirectory() as directory:
            cookie_file = Path(directory) / "cookies.json"
            first_manager = SessionManager(Settings(cookie_file=cookie_file))
            first_session = await first_manager.get()
            first_session.cookie_jar.update_cookies(
                {"session": "abc123"},
                URL("https://elearning.bsi.ac.id/login"),
            )

            await first_manager.save()
            payload = json.loads(cookie_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["version"], 1)
            self.assertEqual(payload["cookies"][0]["name"], "session")
            self.assertEqual(payload["cookies"][0]["value"], "abc123")
            await first_manager.close()

            second_manager = SessionManager(Settings(cookie_file=cookie_file))
            await second_manager.get()
            self.assertEqual(
                second_manager.cookies_for("https://elearning.bsi.ac.id")[
                    "session"
                ],
                "abc123",
            )
            await second_manager.close()

    async def test_same_cookie_name_remains_isolated_per_upstream_host(self):
        with tempfile.TemporaryDirectory() as directory:
            cookie_file = Path(directory) / "cookies.json"
            first_manager = SessionManager(Settings(cookie_file=cookie_file))
            first_session = await first_manager.get()
            first_session.cookie_jar.update_cookies(
                {"session": "elearning"},
                URL("https://elearning.bsi.ac.id/login"),
            )
            first_session.cookie_jar.update_cookies(
                {"session": "exam"},
                URL("https://ujiankampusa.bsi.ac.id/dashboard"),
            )
            await first_manager.close()

            second_manager = SessionManager(Settings(cookie_file=cookie_file))
            second_session = await second_manager.get()

            elearning_cookies = second_session.cookie_jar.filter_cookies(
                URL("https://elearning.bsi.ac.id/dashboard")
            )
            exam_cookies = second_session.cookie_jar.filter_cookies(
                URL("https://ujiankampusa.bsi.ac.id/dashboard")
            )
            self.assertEqual(elearning_cookies["session"].value, "elearning")
            self.assertEqual(exam_cookies["session"].value, "exam")
            await second_manager.close()

    async def test_corrupt_cookie_file_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            cookie_file = Path(directory) / "cookies.json"
            cookie_file.write_text("not-json", encoding="utf-8")
            manager = SessionManager(Settings(cookie_file=cookie_file))

            with self.assertLogs(
                "src.service.upstream_client", level="WARNING"
            ):
                await manager.get()

            self.assertEqual(manager.cookies(), {})
            await manager.close()


if __name__ == "__main__":
    unittest.main()
