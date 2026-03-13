# Local Attendance Host

## A lightweight, LAN-only classroom attendance system with real-time tracking and anti-cheat protection

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## What is it?

**Local Attendance Host** is a self-hosted, offline-first attendance tool that runs entirely on your local Wi-Fi network — no internet required. A professor starts a session, shares a PIN or QR code, and students submit their IDs directly from their phones or laptops.

**The problem:** Paper sign-in sheets are slow, easy to forge, and hard to export. Cloud-based tools require internet access and student accounts. **Local Attendance Host** solves all of this: it runs instantly on any laptop, works over classroom Wi-Fi, guards against buddy-punching through multiple anti-cheat layers, and exports clean CSV files in one click.

---

## Demo

> I WILL ADD YOUTUBE VIDEO HERE

---

## Features

- **PIN + QR Session** — Professor generates a 6-digit PIN; a QR code is displayed automatically so students can scan and go directly to the submission form
- **Secret Professor URL** — Dashboard is served at a cryptographically random token URL (`/{token}`), invisible to students
- **Live Attendance Table** — WebSocket-powered real-time updates; new submissions appear instantly without page refresh
- **3-Layer Anti-Cheat:**
  - **Subnet filter** — only devices on the same local network can submit
  - **IP deduplication** — one submission per IP address per session
  - **HttpOnly cookie lock** — browser cookie prevents re-submission even after page reload
- **Device Fingerprinting** — pseudo-MAC fingerprint logged per submission as an extra integrity signal
- **Manual Management** — Professor can manually add, edit, or delete any attendance record mid-session
- **CSV Export** — Download a clean spreadsheet of any session with one click
- **Auto-browser open** — App opens the professor dashboard in the default browser on startup
- **No internet required** — runs 100% on LAN; no external services, no accounts

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, FastAPI, uvicorn |
| Database | SQLite via aiosqlite (WAL mode) |
| Validation | Pydantic v2 |
| Real-time | WebSocket (native FastAPI) |
| Frontend | Vanilla HTML / CSS / JavaScript |
| QR Code | QRCode.js (bundled via CDN) |
| Logging | Custom Python logger → `logs/` directory |

---

## Installation

### For Users (just want to run it)

**Requirements:** Python 3.10 or newer, pip

```bash
# 1. Clone the repository
git clone https://github.com/kvasmmm/attendance.git
cd attendance

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py
```

The app will automatically open the professor dashboard in your default browser. Share the student link (`http://<your-ip>:8000/student.html`) with your class.

---

### For Contributors (development setup)

```bash
# Clone and enter the repo
git clone https://github.com/kvasmmm/attendance.git
cd attendance

# Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# Install all dependencies including dev tools
pip install -r requirements.txt

# Run in development mode (auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> **Tip:** Use `test_main.py` to run the test suite before submitting a PR.

---

## Usage & Configuration

### Basic Workflow

1. Run `python main.py` on your laptop — the professor dashboard opens automatically
2. Click **Start Session** and note the generated PIN
3. Students open `http://<your-ip>:8000/student.html` (or scan the QR code)
4. Students enter their student ID and the PIN, then submit
5. Submissions appear live in the professor table
6. Click **Close Session** when done, then **Export CSV** to download results

### Configuration Q&A

**Q: How do I change the allowed subnet?**
> Edit `config.py`. The `ALLOWED_SUBNET` variable is auto-detected from your machine's local IP. To override it manually, set the value directly:
> ```python
> ALLOWED_SUBNET = "192.168.1"   # only allow 192.168.1.x
> ```

**Q: What is the student ID format?**
> IDs must match `^202\d{6}$` — a 9-digit number starting with `202` (e.g., `202312345`). This is the DGIST student ID format. To change it, update the regex in `schemas.py`:
> ```python
> student_id: str = Field(..., pattern=r"^202\d{6}$")
> ```

**Q: What port does the app use?**
> Port **8000** by default. To change it, edit the `uvicorn.run(...)` call at the bottom of `main.py`.

**Q: Where are logs stored?**
> In the `logs/` directory, one file per run, named `{timestamp}_debug.txt`.

**Q: Can multiple professors use it at the same time?**
> No. The current design supports a single active session at a time. See [Roadmap](#roadmapcurrent-issues) for multi-session plans.

---

## Roadmap / Current Issues

### Known Issues

- **`currentPinFromUrl` hoisting bug** in `frontend/student.js` — the variable is referenced before its declaration inside the URL PIN prefill block. Functionally harmless in most browsers due to `var` hoisting, but should be cleaned up.
- **No HTTPS** — all traffic is plain HTTP. Suitable for trusted classroom LANs only; do not expose to the public internet.
- **Single professor session** — only one session can be active at a time across the entire app instance.

### Planned Features

- [ ] HTTPS support via self-signed certificate (for stricter environments)
- [ ] Multi-session support (parallel sessions for different groups)
- [ ] Optional professor authentication (password-protected dashboard)
- [ ] Student ID format configurable via `.env` file without touching source code
- [ ] Packaged `.exe` / standalone binary for professors who don't have Python installed

---

## Contributing

Contributions are welcome! Please follow these rules:

1. **Open an issue first** — describe the bug or feature before writing code. This avoids duplicated effort.
2. **Fork → branch → PR** — create a feature branch (`feat/your-feature`) or bugfix branch (`fix/your-fix`), then open a pull request against `main`.
3. **Include a description** — PRs without a clear description of what changed and why will not be reviewed.
4. **Keep scope focused** — one PR per bug/feature. Avoid bundling unrelated changes.
5. **Run tests** — make sure `test_main.py` passes before submitting.

```bash
# Run tests
pytest test_main.py
```

---

## License & Support

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

If this project saved you time, feel free to support it:

I WILL ADD HERE AS I SET UP
