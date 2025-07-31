import aiohttp
import pickle
import os

COOKIES_FILE = "cookies.pkl"
_session = None

async def get_session():
    global _session

    if _session is None or _session.closed:
        jar = aiohttp.CookieJar()

        # Load cookies jika file ada
        if os.path.exists(COOKIES_FILE):
            try:
                with open(COOKIES_FILE, "rb") as f:
                    cookies = pickle.load(f)
                    jar.update_cookies(cookies)
            except Exception:
                pass

        _session = aiohttp.ClientSession(cookie_jar=jar)

    return _session

async def save_cookies():
    global _session
    if _session and not _session.closed:
        cookies = {cookie.key: cookie.value for cookie in _session.cookie_jar}
        with open(COOKIES_FILE, "wb") as f:
            pickle.dump(cookies, f)
