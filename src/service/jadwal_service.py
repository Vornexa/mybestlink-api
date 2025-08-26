from bs4 import BeautifulSoup
from src.utils.session_manager import get_session
from src.utils.session_manager import save_cookies
import ssl, re
from datetime import datetime
from aiohttp import web

BASE_URL = "https://elearning.bsi.ac.id"

async def get_jadwal_pengganti(request):
    session = await get_session()
    ssl_context = ssl._create_unverified_context()

    async with session.get(f"{BASE_URL}/kuliah-pengganti", ssl=ssl_context) as resp:
        html = await resp.text()
        await save_cookies()

    soup = BeautifulSoup(html, "html.parser")
    jadwals = []

    cards = soup.select(".pricing-plan")
    for card in cards:
        try:
            matakuliah = card.select_one(".pricing-title")
            waktu_info = card.select_one(".pricing-save")

            hari, jam_mulai, jam_selesai = None, None, None
            if waktu_info:
                try:
                    hari_jam = waktu_info.text.strip()
                    hari, jam_range = hari_jam.split(" - ")
                    jam_mulai, jam_selesai = jam_range.split("-")
                except:
                    pass

            def get_info(label):
                el = card.find(string=lambda t: t and label in t)
                if el and ":" in el:
                    return el.split(":", 1)[1].strip()
                return None

            jadwals.append({
                "mata_kuliah": matakuliah.text.strip() if matakuliah else None,
                "waktu": {
                    "hari": hari.capitalize() if hari else None,
                    "jam_mulai": jam_mulai.strip() if jam_mulai else None,
                    "jam_selesai": jam_selesai.strip() if jam_selesai else None
                },
                "kode_dosen": get_info("Kode Dosen"),
                "kode_mtk": get_info("Kode MTK"),
                "sks": get_info("SKS"),
                "no_ruang": get_info("No Ruang"),
                "tanggal": get_info("Tanggal"),
                "kel_praktek": get_info("Kel Praktek"),
                "kode_gabung": get_info("Kode Gabung")
            })

        except Exception as e:
            print("Error parsing replacement:", e)
            continue

    response = {
        "status": "success",
        "data": {"jadwal": jadwals},
        "meta": {
            "total": len(jadwals),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }

    return web.json_response(response)