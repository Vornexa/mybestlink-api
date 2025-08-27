from aiohttp import web
from src.service.ujian_service import get_jadwal_ujian, post_cek_lokasi
from src.service.login import post_login
from src.service.dashboard import get_dashboard
from src.service.jadwal_service import get_jadwal_pengganti

def setup_user_routes(app):
    app.router.add_post("/login", post_login)
    app.router.add_get("/dashboard", get_dashboard)
    app.router.add_get("/jadwal/pengganti", get_jadwal_pengganti)
    app.router.add_get("/jadwal/ujian", get_jadwal_ujian)
    app.router.add_post("/cek-lokasi", post_cek_lokasi)
