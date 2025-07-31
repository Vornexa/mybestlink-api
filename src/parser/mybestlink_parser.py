from bs4 import BeautifulSoup
import re
from datetime import datetime

def parse_dashboard(html):
    soup = BeautifulSoup(html, "html.parser")

    name = soup.find("h5", class_="mb-1 font-weight-bold")
    name = name.text.strip() if name else None

    nim = None
    nim_tag = soup.find(string=re.compile("NIM:"))
    if nim_tag:
        nim = nim_tag.replace("NIM:", "").strip()

    email = None
    email_tag = soup.find(string=re.compile("Email :"))
    if email_tag:
        email = email_tag.replace("Email :", "").strip()

    email_kampus = None
    email_kampus_tag = soup.find(string=re.compile("@bsi.ac.id"))
    if email_kampus_tag:
        email_kampus = email_kampus_tag.strip()

    return {
        "name": name,
        "nim": nim,
        "email": email,
        "email_kampus": email_kampus
    }

def parse_jadwal_uts(html):
    """
    Parse HTML jadwal UTS dari halaman Ujian Kampus BSI
    """
    soup = BeautifulSoup(html, "html.parser")
    jadwal = []

    for card in soup.select(".pricing-plan"):
        title = card.select_one(".pricing-title")
        hari_jam = card.select_one(".pricing-save")
        details = {h5.select_one("i")["class"][-1]: h5.get_text(strip=True) for h5 in card.select(".card-body h5")}

        jadwal.append({
            "mata_kuliah": title.get_text(strip=True) if title else None,
            "hari_jam": hari_jam.get_text(strip=True) if hari_jam else None,
            "kode_dosen": details.get("icon-user", "").replace("Kode Dosen :", "").strip(),
            "kode_mtk": details.get("icon-local_library", "").replace("Kode MTK :", "").strip(),
            "sks": details.get("icon-confirmation_number", "").replace("SKS :", "").strip(),
            "ruangan": details.get("icon-address", "").replace("No Ruang :", "").strip(),
            "tanggal_ujian": details.get("icon-clock", "").replace("Tanggal Ujian :", "").strip(),
            "durasi": details.get("icon-clock", "").replace("Waktu Ujian :", "").strip(),
            "jumlah_pg": details.get("icon-assignment", "").replace("Jumlah Soal PG :", "").strip(),
            "jumlah_essay": details.get("icon-import_contacts", "").replace("Jumlah Soal Essay :", "").strip()
        })

    return jadwal
