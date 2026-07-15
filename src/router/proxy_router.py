"""Public API route definitions."""

from aiohttp import web

from view.controller import (
    STATIC_DIR,
    get_configuration_page,
    get_connectors_page,
    get_control_config,
    get_control_panel,
    get_data_console,
    get_endpoints_page,
    post_connector_test,
    put_control_config,
)
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
            web.get("/", get_control_panel),
            web.get("/cp", get_control_panel),
            web.get("/cp/connectors", get_connectors_page),
            web.get("/cp/configuration", get_configuration_page),
            web.get("/cp/endpoints", get_endpoints_page),
            web.get("/cp/data", get_data_console),
            web.get("/cp/api/config", get_control_config),
            web.put("/cp/api/config", put_control_config),
            web.post("/cp/api/connectors/test", post_connector_test),
            web.post("/login", post_login),
            web.get("/dashboard", get_dashboard),
            web.get("/jadwal/kuliah", get_jadwal_kuliah),
            web.get("/jadwal/pengganti", get_jadwal_pengganti),
            web.get("/jadwal/ujian", get_jadwal_ujian),
            web.post("/cek-lokasi", post_cek_lokasi),
        ]
    )
    app.router.add_static("/view/", path=STATIC_DIR, name="view")
