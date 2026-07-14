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
        settings = Settings(cookie_file=self._cookie_path())
        self.client = TestClient(TestServer(create_app(settings)))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()
        cookie_file = self._cookie_path()
        if cookie_file.exists():
            cookie_file.unlink()

    @staticmethod
    def _cookie_path():
        from pathlib import Path
        from tempfile import gettempdir

        return Path(gettempdir()) / "mybestlink-api-test-cookies.json"

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
