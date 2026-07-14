"""Public API route definitions."""

from aiohttp import web

from src.service.dashboard import get_dashboard
from src.service.jadwal_service import get_jadwal_kuliah, get_jadwal_pengganti
from src.service.login import post_login
from src.service.ujian_service import get_jadwal_ujian, post_cek_lokasi


async def health(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


def setup_user_routes(app: web.Application) -> None:
    app.add_routes(
        [
            web.get("/health", health),
            web.post("/login", post_login),
            web.get("/dashboard", get_dashboard),
            web.get("/jadwal/kuliah", get_jadwal_kuliah),
            web.get("/jadwal/pengganti", get_jadwal_pengganti),
            web.get("/jadwal/ujian", get_jadwal_ujian),
            web.post("/cek-lokasi", post_cek_lokasi),
        ]
    )