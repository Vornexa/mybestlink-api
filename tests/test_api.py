import json
import unittest

from aiohttp.test_utils import TestClient, TestServer

from main import create_app
from src.config import Settings
from src.service.login import solve_captcha
from src.validation import validate_coordinates


class ValidationTest(unittest.TestCase):
    def test_coordinates_are_converted_to_floats(self):
        self.assertEqual(validate_coordinates("-6.2", 106.8), (-6.2, 106.8))

    def test_coordinates_outside_world_bounds_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "latitude"):
            validate_coordinates(91, 100)
        with self.assertRaisesRegex(ValueError, "longitude"):
            validate_coordinates(1, 181)

    def test_boolean_is_not_a_valid_coordinate(self):
        with self.assertRaisesRegex(ValueError, "latitude"):
            validate_coordinates(True, 100)

    def test_captcha_solver_handles_addition_and_subtraction(self):
        self.assertEqual(solve_captcha("Berapa 12 + 7?"), 19)
        self.assertEqual(solve_captcha("Berapa 12 - 7?"), 5)
        self.assertIsNone(solve_captcha("tidak ada operasi"))


class ApplicationTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        settings = Settings(
            cookie_file=self._cookie_path(),
            control_config_file=self._config_path(),
        )
        self.client = TestClient(TestServer(create_app(settings)))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()
        cookie_file = self._cookie_path()
        if cookie_file.exists():
            cookie_file.unlink()
        config_file = self._config_path()
        if config_file.exists():
            config_file.unlink()

    @staticmethod
    def _cookie_path():
        from pathlib import Path
        from tempfile import gettempdir

        return Path(gettempdir()) / "mybestlink-api-test-cookies.json"

    @staticmethod
    def _config_path():
        from pathlib import Path
        from tempfile import gettempdir

        return Path(gettempdir()) / "mybestlink-api-test-control.json"

    async def test_control_panel_page_is_served(self):
        response = await self.client.get("/cp")

        self.assertEqual(response.status, 200)
        self.assertEqual(response.content_type, "text/html")
        self.assertIn("MyBestLink Control", await response.text())

    async def test_control_panel_pages_share_viewport_reveal_motion(self):
        dashboard_response = await self.client.get("/cp")
        console_response = await self.client.get("/cp/data")
        motion_response = await self.client.get("/view/motion.js")

        dashboard = await dashboard_response.text()
        console = await console_response.text()

        self.assertEqual(motion_response.status, 200)
        self.assertIn('src="/view/motion.js"', dashboard)
        self.assertIn('src="/view/motion.js"', console)
        self.assertIn("data-reveal", dashboard)
        self.assertIn("data-reveal", console)
        self.assertNotIn("is-ready", dashboard)
        self.assertNotIn("is-ready", console)

    async def test_control_config_reports_connectors_without_cookie_values(self):
        response = await self.client.get("/cp/api/config")

        self.assertEqual(response.status, 200)
        body = await response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(
            [connector["id"] for connector in body["connectors"]],
            ["elearning", "exam"],
        )
        self.assertNotIn("cookies", body)

    async def test_control_config_update_is_applied_and_persisted(self):
        payload = {
            "elearning_base_url": "http://127.0.0.1:9010/",
            "exam_base_url": "https://exam.example.test/",
            "request_timeout_seconds": 12.5,
            "verify_ssl": False,
        }
        response = await self.client.put("/cp/api/config", json=payload)

        self.assertEqual(response.status, 200)
        body = await response.json()
        self.assertEqual(
            body["config"]["elearning_base_url"], "http://127.0.0.1:9010"
        )
        self.assertEqual(body["config"]["request_timeout_seconds"], 12.5)
        saved = json.loads(self._config_path().read_text(encoding="utf-8"))
        self.assertEqual(saved["exam_base_url"], "https://exam.example.test")
        self.assertFalse(saved["verify_ssl"])

    async def test_control_config_rejects_invalid_connector_url(self):
        response = await self.client.put(
            "/cp/api/config",
            json={
                "elearning_base_url": "file:///etc/passwd",
                "exam_base_url": "https://ujiankampusa.bsi.ac.id",
                "request_timeout_seconds": 30,
                "verify_ssl": True,
            },
        )

        self.assertEqual(response.status, 400)
        body = await response.json()
        self.assertIn("http", body["message"])

    async def test_connector_test_checks_the_configured_url(self):
        base_url = str(self.client.make_url("/")).rstrip("/")
        update_response = await self.client.put(
            "/cp/api/config",
            json={
                "elearning_base_url": base_url,
                "exam_base_url": "https://ujiankampusa.bsi.ac.id",
                "request_timeout_seconds": 5,
                "verify_ssl": True,
            },
        )
        self.assertEqual(update_response.status, 200)

        response = await self.client.post(
            "/cp/api/connectors/test", json={"connector": "elearning"}
        )

        self.assertEqual(response.status, 200)
        body = await response.json()
        self.assertTrue(body["reachable"])
        self.assertEqual(body["http_status"], 200)

    async def test_health_endpoint(self):
        response = await self.client.get("/health")

        self.assertEqual(response.status, 200)
        self.assertEqual(await response.json(), {"status": "ok"})

    async def test_location_rejects_malformed_json(self):
        response = await self.client.post(
            "/cek-lokasi",
            data="{",
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(response.status, 400)
        body = json.loads(await response.text())
        self.assertEqual(body["status"], "error")

    async def test_location_rejects_out_of_range_coordinates(self):
        response = await self.client.post(
            "/cek-lokasi", json={"latitude": 91, "longitude": 106.8}
        )

        self.assertEqual(response.status, 400)
        body = await response.json()
        self.assertIn("latitude", body["message"])

    async def test_login_rejects_missing_password_before_upstream_call(self):
        response = await self.client.post(
            "/login", json={"username": "student"}
        )

        self.assertEqual(response.status, 400)
        body = await response.json()
        self.assertEqual(body["message"], "password is required")

    async def test_login_rejects_unsupported_content_type(self):
        response = await self.client.post(
            "/login",
            data="username=student",
            headers={"Content-Type": "text/plain"},
        )

        self.assertEqual(response.status, 415)

    async def test_exam_type_is_validated_before_upstream_call(self):
        response = await self.client.get("/jadwal/ujian?type=quiz")

        self.assertEqual(response.status, 400)
        body = await response.json()
        self.assertIn("uts", body["message"])

    async def test_unknown_route_keeps_404_status(self):
        response = await self.client.get("/does-not-exist")

        self.assertEqual(response.status, 404)
        body = await response.json()
        self.assertEqual(body["status"], "error")


if __name__ == "__main__":
    unittest.main()
