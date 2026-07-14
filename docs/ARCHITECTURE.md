# Arsitektur

## Ringkasan

Aplikasi memakai application factory `main.create_app()` dan membagi tanggung jawab menjadi beberapa lapisan:

```text
HTTP request
    ↓
router (`src/router`)
    ↓
handler/use case (`src/service/login.py`, `dashboard.py`, ...)
    ↓                         ↘
pure parser (`src/parser`)    upstream client (`src/service/upstream_client.py`)
                                      ↓
                              portal elearning/ujian BSI
```

## Komponen

### Application factory

`main.create_app(settings)` membangun `aiohttp.web.Application`, memasang middleware, route, konfigurasi, `SessionManager`, dan `UpstreamClient`. Cleanup hook menutup outbound `ClientSession` saat server berhenti.

### Configuration

`src/config.py` memuat seluruh konfigurasi dari `MYBESTLINK_*`. Objek `Settings` immutable dan bisa diinjeksi langsung pada test sehingga test tidak perlu mengubah source code atau mengakses portal asli.

### Middleware

`src/middleware/base_middleware.py`:

- mencatat method, path, status, dan durasi;
- mempertahankan status `aiohttp.web.HTTPException` seperti 400/404/415;
- memetakan kegagalan upstream menjadi 502;
- tidak membocorkan traceback/internal exception ke client.

### Outbound HTTP dan sesi

`SessionManager` memiliki lifecycle tunggal per application:

- membuat `aiohttp.ClientSession` secara lazy;
- menerapkan total timeout;
- menyimpan cookie dalam JSON dengan atomic replace;
- menutup session pada cleanup.

`UpstreamClient` memusatkan TLS policy, base URL, pemetaan error network, status upstream, dan persistensi cookie setelah request.

### Parser

Parser di `src/parser/mybestlink_parser.py` adalah fungsi murni: HTML masuk, dict/list keluar. Parser tidak melakukan network I/O dan diuji menggunakan fixture HTML kecil. Pemisahan ini mencegah perubahan markup menyebar ke handler.

### Portal ujian

Flow ujian mengikuti redirect autentikasi dari elearning ke portal ujian. Setiap URL hasil `Location`, meta-refresh, atau link jadwal diselesaikan dengan `urljoin` lalu divalidasi terhadap scheme, hostname, dan port portal ujian. Ini mencegah redirect tak dipercaya/SSRF.

## Error contract

Error API yang ditangani memakai envelope:

```json
{
  "status": "error",
  "message": "deskripsi aman"
}
```

- `400`: request/parameter tidak valid.
- `404`: route tidak ditemukan.
- `415`: content type tidak didukung.
- `502`: portal upstream timeout, tidak dapat dihubungi, format berubah, atau memberi status tak terduga.
- `500`: error internal tak terduga; detail hanya masuk server log.

## Batasan deployment

Satu application mempunyai satu cookie jar upstream. Model ini mempertahankan kontrak API lama tetapi hanya aman untuk satu pengguna aktif per proses. Dukungan multi-user memerlukan kontrak sesi inbound (misalnya opaque session ID), penyimpanan sesi terisolasi, TTL, dan rate limit; perubahan tersebut sengaja tidak dimasukkan karena akan memutus client saat ini.

API tidak memiliki autentikasi inbound. Jalankan pada `127.0.0.1` atau lindungi dengan reverse proxy yang memiliki TLS dan autentikasi.

## Strategi test

- `tests/test_config.py`: parsing environment dan secure default.
- `tests/test_parsers.py`: kontrak field dashboard/jadwal.
- `tests/test_exam_service.py`: parsing redirect dan validasi trusted host.
- `tests/test_api.py`: health, JSON error, 404, dan validasi koordinat.

Semua test offline dan tidak mengirim request ke portal BSI.
