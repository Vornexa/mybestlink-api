from bs4 import BeautifulSoup
import ssl
import re
from src.utils.session_manager import get_session, save_cookies
from aiohttp import web


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
    payload = await request.json()
    username = payload.get("username")
    password = payload.get("password")
    html = await login(username, password)
    await save_cookies()  # simpan cookies setelah login

    if "dashboard" in html.lower():
        return web.json_response({"status": "success", "message": "Logged in"})
    else:
        return web.json_response({"status": "failed", "message": "Invalid credentials"})