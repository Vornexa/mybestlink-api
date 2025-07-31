from src.utils.session_manager import get_session
from bs4 import BeautifulSoup
import ssl
import re
from src.utils.session_manager import save_cookies
from urllib.parse import urlparse, parse_qs

BASE_URL = "https://elearning.bsi.ac.id"
UJIAN_BASE_URL = "https://ujiankampusa.bsi.ac.id"

async def fetch_data(endpoint, method="GET", payload=None, headers=None):
    session = await get_session()
    url = f"{BASE_URL}{endpoint}"
    ssl_context = ssl._create_unverified_context()
    async with session.request(method, url, data=payload, headers=headers, ssl=ssl_context) as resp:
        if resp.content_type == "application/json":
            data = await resp.json()
        else:
            data = await resp.text()
        await save_cookies()
        return data