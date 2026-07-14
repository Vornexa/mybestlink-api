"""Pure HTML parsers for MyBest/BSI upstream pages."""

from __future__ import annotations

import re
from datetime import datetime

from bs4 import BeautifulSoup, Tag


def _text(element: Tag | None) -> str | None:
    return element.get_text(strip=True) if element else None


def _extract_label(card: Tag, label: str) -> str | None:
    value = card.find(string=lambda text: bool(text and label in text))
    if not value or ":" not in value:
        return None
    return value.split(":", 1)[1].strip() or None


def _parse_time(card: Tag) -> dict[str, str | None]:
    value = _text(card.select_one(".pricing-save"))
    if not value:
        return {"hari": None, "jam_mulai": None, "jam_selesai": None}

    try:
        day, time_range = value.split(" - ", 1)
        start, end = time_range.split("-", 1)
    except ValueError:
        return {"hari": None, "jam_mulai": None, "jam_selesai": None}

    return {
        "hari": day.strip().capitalize() or None,
        "jam_mulai": start.strip() or None,
        "jam_selesai": end.strip() or None,
    }


def parse_dashboard(html: str) -> dict[str, str | None]:
    """Extract the student profile displayed on the dashboard."""

    soup = BeautifulSoup(html, "html.parser")
    name = _text(soup.find("h5", class_="mb-1 font-weight-bold"))

    nim_tag = soup.find(string=re.compile(r"NIM\s*:"))
    email_tag = soup.find(string=re.compile(r"Email\s*:"))
    campus_email_tag = soup.find(string=re.compile(r"@bsi\.ac\.id"))

    return {
        "name": name,
        "nim": re.sub(r"^.*?NIM\s*:\s*", "", nim_tag).strip()
        if nim_tag
        else None,
        "email": re.sub(r"^.*?Email\s*:\s*", "", email_tag).strip()
        if email_tag
        else None,
        "email_kampus": campus_email_tag.strip() if campus_email_tag else None,
    }


def parse_class_schedule(html: str) -> list[dict[str, object]]:
    """Parse regular lecture schedule cards."""

    soup = BeautifulSoup(html, "html.parser")
    schedule = []
    for card in soup.select(".pricing-plan"):
        schedule.append(
            {
                "matakuliah": _text(card.select_one(".pricing-title")),
                "kode_mtk": _extract_label(card, "Kode MTK"),
                "dosen": _extract_label(card, "Kode Dosen"),
                "ruang": _extract_label(card, "No Ruang"),
                "sks": _extract_label(card, "SKS"),
                "kode_gabung": _extract_label(card, "Kode Gabung"),
                "waktu": _parse_time(card),
            }
        )
    return schedule


def parse_replacement_schedule(html: str) -> list[dict[str, object]]:
    """Parse replacement lecture schedule cards."""

    soup = BeautifulSoup(html, "html.parser")
    schedule = []
    for card in soup.select(".pricing-plan"):
        schedule.append(
            {
                "mata_kuliah": _text(card.select_one(".pricing-title")),
                "waktu": _parse_time(card),
                "kode_dosen": _extract_label(card, "Kode Dosen"),
                "kode_mtk": _extract_label(card, "Kode MTK"),
                "sks": _extract_label(card, "SKS"),
                "no_ruang": _extract_label(card, "No Ruang"),
                "tanggal": _extract_label(card, "Tanggal"),
                "kel_praktek": _extract_label(card, "Kel Praktek"),
                "kode_gabung": _extract_label(card, "Kode Gabung"),
            }
        )
    return schedule


def parse_exam_schedule(html: str) -> list[dict[str, object]]:
    """Parse either card-based or table-based UTS/UAS schedules."""

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.pricing-plan")
    if cards:
        return [_parse_exam_card(card) for card in cards]

    schedule = []
    table = soup.find("table")
    if not table:
        return schedule

    for row in table.select("tbody tr"):
        columns = [column.get_text(strip=True) for column in row.find_all("td")]
        if len(columns) < 6:
            continue
        try:
            exam_date = datetime.strptime(columns[4], "%d-%m-%Y").date().isoformat()
        except ValueError:
            exam_date = columns[4]

        schedule.append(
            {
                "matakuliah": columns[0],
                "kode": columns[1],
                "dosen": columns[2],
                "ruang": columns[3],
                "waktu": {
                    "hari": columns[5],
                    "tanggal": exam_date,
                    "jam_mulai": columns[6] if len(columns) > 6 else None,
                    "jam_selesai": columns[7] if len(columns) > 7 else None,
                },
                "kelas": columns[8] if len(columns) > 8 else None,
            }
        )
    return schedule


def _parse_exam_card(card: Tag) -> dict[str, str | None]:
    details: dict[str, str] = {}
    labels = {
        "Kode Dosen": "kode_dosen",
        "Kode MTK": "kode_mtk",
        "SKS": "sks",
        "No Ruang": "ruangan",
        "Tanggal Ujian": "tanggal",
        "Waktu Ujian": "durasi_menit",
        "Jumlah Soal PG": "jumlah_pg",
        "Jumlah Soal Essay": "jumlah_essay",
    }
    for element in card.select(".card-body h5.styled"):
        text = element.get_text(strip=True)
        for label, field in labels.items():
            if label in text:
                details[field] = text.split(":", 1)[-1].strip()
                break

    return {
        "mata_kuliah": _text(card.select_one(".pricing-title")),
        "hari_jam": _text(card.select_one(".pricing-save")),
        **details,
    }


# Backward-compatible alias for callers using the old parser name.
parse_jadwal_uts = parse_exam_schedule