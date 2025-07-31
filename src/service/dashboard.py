# Endpoint dashboard
from parser.mybestlink_parser import parse_dashboard
from src.service.proxy_service import fetch_data
from utils.session_manager import save_cookies
from aiohttp import web


async def get_dashboard(request):
    html = await fetch_data("/dashboard")
    await save_cookies()  # simpan cookies setelah akses dashboard
    parsed = parse_dashboard(html)
    return web.json_response(parsed)