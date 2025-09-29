import re
import ssl

from aiohttp import web
from bs4 import BeautifulSoup

from src.utils.session_manager import get_session, save_cookies

BASE_URL = "https://elearning.bsi.ac.id"


async def get_login_page():
    session = await get_session()
    session.cookie_jar.clear()
    ssl_context = ssl._create_unverified_context()
    async with session.get(f"{BASE_URL}/login", ssl=ssl_context) as resp:
        html = await resp.text()
        soup = BeautifulSoup(html, "html.parser")
        token = soup.find("input", {"name": "_token"})["value"]

        # Cari pertanyaan captcha
        captcha_text = soup.find(id="captcha_question").text.strip()
        captcha_answer = solve_captcha(captcha_text)
        return token, captcha_answer


def solve_captcha(text):
    """Contoh sederhana: hanya menangani operasi + dan -."""
    match = re.findall(r"(\d+)\s*([+\-])\s*(\d+)", text)
    if not match:
        return None
    a, op, b = match[0]
    a, b = int(a), int(b)
    return a + b if op == "+" else a - b


async def login(username, password):
    session = await get_session()
    token, captcha_answer = await get_login_page()
    payload = {
        "username": username,
        "password": password,
        "_token": token,
        "captcha_answer": captcha_answer
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    ssl_context = ssl._create_unverified_context()
    async with session.post(f"{BASE_URL}/login", data=payload, headers=headers, ssl=ssl_context) as resp:
        html = await resp.text()
        from src.utils.session_manager import save_cookies
        await save_cookies()
        return html


async def post_login(request):
    """"
    This post_login method is updated to 3 supported Content-Type.
    Need more flexibility in the future.
    """
    content_type = request.headers.get("Content-Type", '').lower()
    username = None
    password = None

    if 'application/json' in content_type:
        body = await request.json()
        username = body.get("username")
        password = body.get("password")

    elif 'multipart/form-data' in content_type or 'application/x-www-form-urlencoded' in content_type:
        post_data = await request.post()
        username = post_data.get("username")
        password = post_data.get("password")

    else :
        return web.json_response({
            'error': 'bad request unsupported content_type',
        }, status=415)

    if not username or not password:
        return web.json_response({
            'status': 'error failed',
            'message': 'bad username or password (missing)',
        }, status=400)

    html = await login(username, password)
    await save_cookies()

    if "dashboard" in html.lower():
        return web.json_response({"status": "success", "message": "Logged in"})
    else:
        return web.json_response({"status": "failed", "message": "Invalid credentials"})
