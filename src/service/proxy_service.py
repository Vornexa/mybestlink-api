import aiohttp

BASE_URL = "https://elearning.bsi.ac.id/login"

async def fetch_data(endpoint, method="GET", payload=None, headers=None):
    async with aiohttp.ClientSession() as session:
        url = f"{BASE_URL}{endpoint}"
        async with session.request(method, url, json=payload, headers=headers) as resp:
            return await resp.json()