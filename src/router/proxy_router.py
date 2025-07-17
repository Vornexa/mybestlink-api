from aiohttp import web
from src.service.proxy_service import fetch_data

async def get_dashboard(request):
    data = await fetch_data("/dashboard")
    return web.json_response(data)

async def post_login(request):
    payload = await request.json()
    data = await fetch_data("/login", method="POST", payload=payload)
    return web.json_response(data)

def setup_proxy_routes(app):
    app.router.add_get("/dashboard", get_dashboard)
    app.router.add_post("/login", post_login)