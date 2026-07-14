# MyBestLink API — English Guide

An unofficial `aiohttp` API that converts MyBest/BSI pages into JSON responses for student profile, lecture schedules, replacement schedules, exams, and exam location validation.

> This project is not an official BSI product. Only use it with accounts and data you are authorized to access.

## Quick start

Requirements: Python 3.11+ and network access to the BSI portals.

```bash
python -m venv .venv
source .venv/Scripts/activate   # Git Bash on Windows
python -m pip install -r requirements.txt
MYBESTLINK_HOST=127.0.0.1 python main.py
```

Check the process:

```bash
curl http://127.0.0.1:8000/health
```

Login before calling authenticated endpoints:

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"USERNAME","password":"PASSWORD"}'

curl http://127.0.0.1:8000/dashboard
curl http://127.0.0.1:8000/jadwal/kuliah
curl 'http://127.0.0.1:8000/jadwal/ujian?type=uas'
```

See [ROUTER.md](ROUTER.md) for the full endpoint contract and [ARCHITECTURE.md](ARCHITECTURE.md) for implementation details.

## Configuration

| Variable | Default | Purpose |
|---|---:|---|
| `MYBESTLINK_HOST` | `0.0.0.0` | Server bind interface. Prefer `127.0.0.1` locally. |
| `MYBESTLINK_PORT` | `8000` | HTTP port. |
| `MYBESTLINK_ELEARNING_BASE_URL` | `https://elearning.bsi.ac.id` | Elearning upstream base URL. |
| `MYBESTLINK_EXAM_BASE_URL` | `https://ujiankampusa.bsi.ac.id` | Exam upstream base URL. |
| `MYBESTLINK_COOKIE_FILE` | `cookies.json` | Persisted session-cookie path. |
| `MYBESTLINK_REQUEST_TIMEOUT` | `30` | Total upstream timeout in seconds. |
| `MYBESTLINK_VERIFY_SSL` | `true` | Verify upstream TLS certificates. |

Accepted booleans: `1/0`, `true/false`, `yes/no`, and `on/off`.

Do not disable TLS verification in production. The `false` option is only an emergency diagnostic escape hatch for a trusted local network performing TLS inspection.

## Development checks

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
ruff check .
python -m compileall -q main.py src tests
```

## Security and session model

The process currently owns one shared upstream session and is intended for personal/single-user deployment. A new login replaces the active login state. The API has no inbound authentication, so do not expose it directly to the public internet. Bind to `127.0.0.1` or place it behind an authenticated reverse proxy.

Session cookies are stored in Git-ignored `cookies.json`; protect that file like a credential. Credentials are forwarded to BSI and are not persisted by this application.
