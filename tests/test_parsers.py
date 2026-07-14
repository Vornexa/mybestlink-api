import unittest

from src.parser.mybestlink_parser import (
    parse_class_schedule,
    parse_dashboard,
    parse_exam_schedule,
    parse_replacement_schedule,
)

SCHEDULE_HTML = """
<div class="pricing-plan">
  <div class="pricing-title">Algoritma</div>
  <div class="pricing-save">senin - 08:00-09:40</div>
  <div>Kode MTK: ALG101</div>
  <div>Kode Dosen: DSN01</div>
  <div>No Ruang: 301</div>
  <div>SKS: 3</div>
  <div>Kode Gabung: KG01</div>
  <div>Tanggal: 01-09-2026</div>
  <div>Kel Praktek: A</div>
</div>
"""

EXAM_TABLE_HTML = """
<table><tbody><tr>
  <td>Algoritma</td><td>ALG101</td><td>DSN01</td><td>301</td>
  <td>14-07-2026</td><td>Selasa</td><td>08:00</td><td>09:30</td><td>12.1A</td>
</tr></tbody></table>
"""


class DashboardParserTest(unittest.TestCase):
    def test_parse_dashboard_preserves_public_fields(self):
        html = """
        <h5 class="mb-1 font-weight-bold">Ariqa</h5>
        <span>NIM: 12345678</span>
        <span>Email : student@example.com</span>
        <span>12345678@bsi.ac.id</span>
        """

        self.assertEqual(
            parse_dashboard(html),
            {
                "name": "Ariqa",
                "nim": "12345678",
                "email": "student@example.com",
                "email_kampus": "12345678@bsi.ac.id",
            },
        )


class ScheduleParserTest(unittest.TestCase):
    def test_parse_class_schedule(self):
        self.assertEqual(
            parse_class_schedule(SCHEDULE_HTML),
            [
                {
                    "matakuliah": "Algoritma",
                    "kode_mtk": "ALG101",
                    "dosen": "DSN01",
                    "ruang": "301",
                    "sks": "3",
                    "kode_gabung": "KG01",
                    "waktu": {
                        "hari": "Senin",
                        "jam_mulai": "08:00",
                        "jam_selesai": "09:40",
                    },
                }
            ],
        )

    def test_parse_replacement_schedule_preserves_public_fields(self):
        result = parse_replacement_schedule(SCHEDULE_HTML)

        self.assertEqual(result[0]["mata_kuliah"], "Algoritma")
        self.assertEqual(result[0]["kode_dosen"], "DSN01")
        self.assertEqual(result[0]["tanggal"], "01-09-2026")
        self.assertEqual(result[0]["kel_praktek"], "A")

    def test_parse_exam_table_normalizes_valid_date(self):
        result = parse_exam_schedule(EXAM_TABLE_HTML)

        self.assertEqual(result[0]["waktu"]["tanggal"], "2026-07-14")
        self.assertEqual(result[0]["kelas"], "12.1A")


if __name__ == "__main__":
    unittest.main()
