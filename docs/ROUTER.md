# Dokumentasi Endpoint

Base URL lokal: `http://127.0.0.1:8000`

Endpoint selain `/health` dan `/login` memakai sesi upstream yang dibuat oleh login terakhir pada proses API. Content type respons adalah `application/json`.

## Ringkasan

| Method | Path | Keterangan |
|---|---|---|
| `GET` | `/health` | Health check proses. |
| `POST` | `/login` | Login ke portal elearning BSI. |
| `GET` | `/dashboard` | Profil mahasiswa. |
| `GET` | `/jadwal/kuliah` | Jadwal kuliah reguler. |
| `GET` | `/jadwal/pengganti` | Jadwal kuliah pengganti. |
| `GET` | `/jadwal/ujian?type=uts|uas` | Jadwal UTS atau UAS. |
| `POST` | `/cek-lokasi` | Validasi lokasi ke portal ujian. |

## Error umum

Error yang ditangani middleware memiliki format:

```json
{
  "status": "error",
  "message": "deskripsi error"
}
```

| Status | Arti |
|---:|---|
| `400` | Body, field, koordinat, atau query tidak valid. |
| `404` | Route tidak ditemukan. |
| `415` | Content type request tidak didukung. |
| `502` | Portal BSI timeout, tidak dapat dihubungi, format berubah, atau memberi status tak terduga. |
| `500` | Error internal tak terduga. Detail tidak dikirim ke client. |

---

## `GET /health`

Tidak membutuhkan sesi.

```bash
curl http://127.0.0.1:8000/health
```

Respons `200`:

```json
{"status":"ok"}
```

---

## `POST /login`

Content type yang didukung:

- `application/json`
- `application/x-www-form-urlencoded`
- `multipart/form-data`

Field:

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `username` | string | ya | Username portal BSI. |
| `password` | string | ya | Password portal BSI. |

JSON request:

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"USERNAME","password":"PASSWORD"}'
```

Form request:

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'username=USERNAME' \
  --data-urlencode 'password=PASSWORD'
```

Berhasil, `200`:

```json
{"status":"success","message":"Logged in"}
```

Kredensial ditolak, `200` (dipertahankan untuk kompatibilitas client lama):

```json
{"status":"failed","message":"Invalid credentials"}
```

Field kosong menghasilkan `400`; content type lain menghasilkan `415`.

Login baru membersihkan cookie login yang sedang aktif pada proses API.

---

## `GET /dashboard`

Membutuhkan login.

```bash
curl http://127.0.0.1:8000/dashboard
```

Respons `200`:

```json
{
  "name": "Nama Mahasiswa",
  "nim": "12345678",
  "email": "student@example.com",
  "email_kampus": "12345678@bsi.ac.id"
}
```

Seluruh field dapat bernilai `null` jika field tidak tersedia pada halaman upstream.

---

## `GET /jadwal/kuliah`

Membutuhkan login.

```bash
curl http://127.0.0.1:8000/jadwal/kuliah
```

Respons `200`:

```json
{
  "status": "success",
  "data": {
    "jadwal": [
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
          "jam_selesai": "09:40"
        }
      }
    ]
  },
  "meta": {
    "total": 1,
    "timestamp": "2026-07-14T04:00:00Z"
  }
}
```

Nilai item jadwal dapat `null` ketika elemen tidak tersedia pada HTML upstream.

---

## `GET /jadwal/pengganti`

Membutuhkan login.

```bash
curl http://127.0.0.1:8000/jadwal/pengganti
```

Respons `200` menggunakan envelope yang sama dengan jadwal kuliah. Bentuk tiap item:

```json
{
  "mata_kuliah": "Algoritma",
  "waktu": {
    "hari": "Selasa",
    "jam_mulai": "10:00",
    "jam_selesai": "11:40"
  },
  "kode_dosen": "DSN01",
  "kode_mtk": "ALG101",
  "sks": "3",
  "no_ruang": "302",
  "tanggal": "20-07-2026",
  "kel_praktek": "A",
  "kode_gabung": "KG01"
}
```

Nama field dipertahankan dari kontrak API lama meskipun berbeda dari `/jadwal/kuliah`.

---

## `GET /jadwal/ujian`

Membutuhkan login. Query `type` opsional dan default-nya `uts`.

| Query | Nilai | Default |
|---|---|---|
| `type` | `uts` atau `uas` (case-insensitive) | `uts` |

```bash
curl 'http://127.0.0.1:8000/jadwal/ujian?type=uas'
```

Respons `200`:

```json
{
  "status": "success",
  "data": {
    "jadwal": []
  },
  "meta": {
    "total": 0,
    "type": "UAS",
    "timestamp": "2026-07-14T04:00:00Z"
  }
}
```

Portal ujian pernah memakai dua layout HTML, sehingga bentuk item mengikuti layout sumber.

Layout kartu:

```json
{
  "mata_kuliah": "Algoritma",
  "hari_jam": "Senin - 08:00",
  "kode_dosen": "DSN01",
  "kode_mtk": "ALG101",
  "sks": "3",
  "ruangan": "301",
  "tanggal": "20-07-2026",
  "durasi_menit": "90",
  "jumlah_pg": "40",
  "jumlah_essay": "5"
}
```

Layout tabel:

```json
{
  "matakuliah": "Algoritma",
  "kode": "ALG101",
  "dosen": "DSN01",
  "ruang": "301",
  "waktu": {
    "hari": "Senin",
    "tanggal": "2026-07-20",
    "jam_mulai": "08:00",
    "jam_selesai": "09:30"
  },
  "kelas": "12.1A"
}
```

`type` selain `uts`/`uas` menghasilkan `400`.

---

## `POST /cek-lokasi`

Membutuhkan login dan `Content-Type: application/json`.

| Field | Tipe | Range | Wajib |
|---|---|---:|---|
| `latitude` | number/string numerik | `-90` sampai `90` | ya |
| `longitude` | number/string numerik | `-180` sampai `180` | ya |

```bash
curl -X POST http://127.0.0.1:8000/cek-lokasi \
  -H 'Content-Type: application/json' \
  -d '{"latitude":-6.2,"longitude":106.8}'
```

Berhasil, `200`:

```json
{"success":true,"message":"Lokasi berhasil divalidasi"}
```

Ditolak portal ujian, `200` untuk kompatibilitas client lama:

```json
{"success":false,"error":"Gagal validasi lokasi: upstream HTTP 422"}
```

Body malformed, field hilang, nilai boolean, non-numerik, atau di luar range menghasilkan `400`.
