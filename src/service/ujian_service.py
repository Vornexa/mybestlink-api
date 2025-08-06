import ssl, re
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from datetime import datetime
from aiohttp import web
import urllib
from src.utils.session_manager import get_session, save_cookies

BASE_URL = "https://elearning.bsi.ac.id"
UJIAN_BASE = "https://ujiankampusa.bsi.ac.id"
ssl_context = ssl._create_unverified_context()

async def fetch_ujian_dashboard():
    session = await get_session()
    ssl_context = ssl._create_unverified_context()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Referer": f"{BASE_URL}/halaman-ujian"
    }

    async with session.get(f"{BASE_URL}/halaman-ujian", headers=headers, ssl=ssl_context, allow_redirects=False) as resp:
        await save_cookies()
        if resp.status == 302:
            redirect_url = resp.headers.get('Location')
        else:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            meta_refresh = soup.find("meta", {"http-equiv": "refresh"})
            if not meta_refresh:
                raise Exception("Tidak menemukan redirect dari halaman ujian")
            match = re.search(r'url=(.+)', meta_refresh.get("content", ""), re.IGNORECASE)
            if not match:
                raise Exception("Tidak menemukan URL redirect di meta refresh")
            redirect_url = match.group(1)

    if not redirect_url or "ujiankampusa.bsi.ac.id" not in redirect_url:
        raise Exception(f"Redirect URL tidak valid: {redirect_url}")

    async with session.get(redirect_url, headers=headers, ssl=ssl_context, allow_redirects=False) as resp:
        await save_cookies()
        if resp.status in (301, 302):
            dashboard_url = resp.headers.get('Location')
        else:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            meta_refresh = soup.find("meta", {"http-equiv": "refresh"})
            if not meta_refresh:
                raise Exception("Tidak menemukan redirect setelah autentikasi")
            match = re.search(r'url=(.+)', meta_refresh.get("content", ""), re.IGNORECASE)
            if not match:
                raise Exception("Tidak menemukan URL dashboard di meta refresh")
            dashboard_url = match.group(1)

    async with session.get(dashboard_url, headers=headers, ssl=ssl_context) as resp:
        await save_cookies()
        html = await resp.text()
        if resp.status != 200:
            raise Exception(f"Gagal akses dashboard ujian: {resp.status}, body: {html[:200]}")
        return html
    
# async def cek_lokasi(latitude, longitude):
#     session = await get_session()
#     ssl_context = ssl._create_unverified_context()

#     async def refresh_session():
#         async with session.get("https://ujiankampusa.bsi.ac.id/dashboard",
#                                ssl=ssl_context, allow_redirects=True):
#             await save_cookies()

#     async def post_location():
#         cookies = {c.key: c.value for c in session.cookie_jar}
#         xsrf_cookie = cookies.get("XSRF-TOKEN")
#         if not xsrf_cookie:
#             raise Exception("XSRF-TOKEN tidak ditemukan di cookie")

#         xsrf_token = urllib.parse.unquote(xsrf_cookie)
#         headers = {
#             "Content-Type": "application/json",
#             "Referer": "https://ujiankampusa.bsi.ac.id/dashboard",
#             "Origin": "https://ujiankampusa.bsi.ac.id",
#             "X-XSRF-TOKEN": xsrf_token
#         }

#         payload = {"latitude": latitude, "longitude": longitude}

#         async with session.post(
#             "https://ujiankampusa.bsi.ac.id/api/save-location",
#             json=payload,
#             headers=headers,
#             ssl=ssl_context
#         ) as resp:
#             return resp.status, await resp.text()

#     await refresh_session()
#     status, body = await post_location()

#     if status == 419:
#         # Refresh lagi kalau token expired
#         await refresh_session()
#         status, body = await post_location()

#     if status != 200:
#         raise Exception(f"Gagal validasi lokasi: {status}, body: {body[:200]}")

#     await save_cookies()
#     return True


# async def fetch_jadwal_uts():
#     session = await get_session()
#     ssl_context = ssl._create_unverified_context()
#     dashboard_html = await fetch_ujian_dashboard()

#     soup = BeautifulSoup(dashboard_html, "html.parser")
#     uts_link = None
#     for a in soup.find_all("a", href=True):
#         if "jadwal" in a.get_text(strip=True).lower() and "uts" in a.get_text(strip=True).lower():
#             uts_link = a["href"]
#             break

#     if not uts_link:
#         raise Exception("Tidak menemukan link Jadwal UTS di dashboard")

#     if uts_link.startswith("/"):
#         uts_link = "https://ujiankampusa.bsi.ac.id" + uts_link

#     headers = {
#         "User-Agent": "Mozilla/5.0",
#         "Referer": "https://ujiankampusa.bsi.ac.id/dashboard",
#         "Accept": "text/html,application/xhtml+xml"
#     }

#     async with session.get(uts_link, headers=headers, ssl=ssl_context, allow_redirects=True) as resp:
#         await save_cookies()
#         html = await resp.text()
#         if resp.status != 200:
#             raise Exception(f"Gagal akses jadwal UTS: {resp.status}")
#         return html

def parse_jadwal_uts(html):
    soup = BeautifulSoup(html, "html.parser")
    jadwal = []
    cards = soup.select("div.pricing-plan")
    if cards:
        for card in cards:
            title = card.select_one(".pricing-title")
            waktu_hari_jam = card.select_one(".pricing-save")
            detail = {}
            for h5 in card.select(".card-body h5.styled"):
                text = h5.get_text(strip=True)
                if "Kode Dosen" in text:
                    detail["kode_dosen"] = text.split(":")[-1].strip()
                elif "Kode MTK" in text:
                    detail["kode_mtk"] = text.split(":")[-1].strip()
                elif "SKS" in text:
                    detail["sks"] = text.split(":")[-1].strip()
                elif "No Ruang" in text:
                    detail["ruangan"] = text.split(":")[-1].strip()
                elif "Tanggal Ujian" in text:
                    detail["tanggal"] = text.split(":")[-1].strip()
                elif "Waktu Ujian" in text:
                    detail["durasi_menit"] = text.split(":")[-1].strip()
                elif "Jumlah Soal PG" in text:
                    detail["jumlah_pg"] = text.split(":")[-1].strip()
                elif "Jumlah Soal Essay" in text:
                    detail["jumlah_essay"] = text.split(":")[-1].strip()

            jadwal.append({
                "mata_kuliah": title.get_text(strip=True) if title else None,
                "hari_jam": waktu_hari_jam.get_text(strip=True) if waktu_hari_jam else None,
                **detail
            })
        return jadwal

    table = soup.find("table")
    if table:
        for row in table.select("tbody tr"):
            cols = [col.get_text(strip=True) for col in row.find_all("td")]
            if len(cols) >= 6:
                try:
                    tanggal = datetime.strptime(cols[4], "%d-%m-%Y").date().isoformat()
                except ValueError:
                    tanggal = cols[4]

                jadwal.append({
                    "matakuliah": cols[0],
                    "kode": cols[1],
                    "dosen": cols[2],
                    "ruang": cols[3],
                    "waktu": {
                        "hari": cols[5],
                        "tanggal": tanggal,
                        "jam_mulai": cols[6] if len(cols) > 6 else None,
                        "jam_selesai": cols[7] if len(cols) > 7 else None
                    },
                    "kelas": cols[8] if len(cols) > 8 else None
                })
    return jadwal

# async def get_jadwal_uts():
#     html = await fetch_jadwal_uts()
#     parsed = parse_jadwal_uts(html)
#     return web.json_response(parsed)

async def get_jadwal_ujian(request):
    """
    Endpoint: GET /jadwal/ujian?type=uts|uas
    """
    type_param = request.query.get("type", "uts").lower()
    if type_param not in ("uts", "uas"):
        return web.json_response(
            {"status": "error", "message": "Only 'uts' and 'uas' supported"}, status=400
        )

    try:
        dashboard_html = await fetch_ujian_dashboard()
        await save_cookies()

        soup = BeautifulSoup(dashboard_html, "html.parser")
        target_link = None
        for a in soup.find_all("a", href=True):
            txt = a.get_text(strip=True).lower()
            if type_param in txt and "jadwal" in txt:
                target_link = a["href"]
                break

        if not target_link:
            raise Exception(f"Link Jadwal {type_param.upper()} tidak ditemukan di dashboard")

        if target_link.startswith("/"):
            target_link = "https://ujiankampusa.bsi.ac.id" + target_link

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://ujiankampusa.bsi.ac.id/dashboard",
            "Accept": "text/html,application/xhtml+xml"
        }

        ssl_context = ssl._create_unverified_context()
        session = await get_session()
        async with session.get(target_link, headers=headers, ssl=ssl_context, allow_redirects=True) as resp:
            # await save_cookies()
            html = await resp.text()
            if resp.status != 200:
                raise Exception(f"Gagal akses jadwal {type_param.upper()}: {resp.status}")

        jadwal = parse_jadwal_uts(html)  # parser-nya bisa dipakai ulang

        response = {
            "status": "success",
            "data": {"jadwal": jadwal},
            "meta": {
                "total": len(jadwal),
                "type": type_param.upper(),
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        if not jadwal:
            response["debug_html_sample"] = html[:1000]

        return web.json_response(response)

    except Exception as e:
        return web.json_response(
            {
                "status": "error",
                "message": str(e),
            },
            status=500,
        )

async def post_cek_lokasi_service(latitude: float, longitude: float):
    session = await get_session()
    ssl_context = ssl._create_unverified_context()

    # 1. Panggil flow redirect elearning -> ujian (seperti fetch_ujian_dashboard)
    dashboard_html = await fetch_ujian_dashboard()  # ini sudah memastikan session valid
    await save_cookies()

    # 2. Ambil token XSRF dari cookie (ujiankampusa.bsi.ac.id)
    cookies = {c.key: c.value for c in session.cookie_jar}
    xsrf_cookie = cookies.get("XSRF-TOKEN")
    if not xsrf_cookie:
        return {"success": False, "error": "XSRF token tidak ditemukan di cookie"}

    xsrf_token = urllib.parse.unquote(xsrf_cookie)

    # 3. Kirim lokasi ke API ujian
    url = "https://ujiankampusa.bsi.ac.id/api/save-location"
    payload = {"latitude": latitude, "longitude": longitude}

    headers = {
        "Content-Type": "application/json",
        "Referer": "https://ujiankampusa.bsi.ac.id/dashboard",
        "Origin": "https://ujiankampusa.bsi.ac.id",
        "X-XSRF-TOKEN": xsrf_token,
        "User-Agent": "Mozilla/5.0"
    }

    async with session.post(url, json=payload, headers=headers, ssl=ssl_context) as resp:
        body = await resp.text()
        if resp.status == 200:
            return {"success": True, "message": "Lokasi berhasil divalidasi"}
        else:
            return {"success": False, "error": f"Gagal validasi lokasi: {resp.status}, body: {body[:300]}"}
    payload = {"latitude": latitude, "longitude": longitude}
    url = f"{UJIAN_BASE}/api/save-location"

    async with session.post(url, json=payload, headers=headers, ssl=ssl_context) as resp:
        text = await resp.text()
        if resp.status == 200:
            try:
                return await resp.json()
            except:
                return {"success": False, "error": f"Unexpected response: {text}"}
        else:
            return {"success": False, "error": f"Gagal validasi lokasi: {resp.status}, body: {text}"}


async def post_cek_lokasi(request):
    data = await request.json()
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:
        return web.json_response({"error": "latitude and longitude are required"}, status=400)

    result = await post_cek_lokasi_service(latitude, longitude)
    return web.json_response(result)
