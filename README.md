# AMK Heritage Trail Race 2026

A real-time **Amazing Race** event platform for the Ang Mo Kio Heritage Trail. Teams race across 12 heritage checkpoints in the AMK neighbourhood, submitting photos/videos via Telegram. An HQ dashboard monitors live progress with a map, leaderboard, and photo gallery.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLOUD SERVICES                                 │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────────────────────────┐  │
│  │  Telegram     │  │  Google Drive  │  │  Google Gemini Vision (future) │  │
│  │  Bot API      │  │  (photo/video  │  │  (auto-identify checkpoints)   │  │
│  │               │  │   storage)     │  │                                │  │
│  └──────┬───────┘  └───────▲┬───────┘  └──────────────┬─────────────────┘  │
└─────────┼──────────────────┼┼──────────────────────────┼────────────────────┘
          │  webhook/poll   │ │ upload/download          │ identify photo
          │                  │ │                          │
┌─────────┼──────────────────┼┼──────────────────────────┼────────────────────┐
│         │   PRODUCTION SERVER (finflowfx.biz)          │                    │
│         │                  │ │                          │                    │
│  ┌──────▼──────────────────▼─┼──────────────────────────▼──────────────┐   │
│  │              Nginx (reverse proxy + SSL)                          │   │
│  │              Let's Encrypt HTTPS                                   │   │
│  └──────────────────────┬────────────────────────────────────────────┘   │
│                         │ :443 → :8000                                    │
│  ┌──────────────────────▼────────────────────────────────────────────┐   │
│  │                    FastAPI + Uvicorn  (:8000)                     │   │
│  │                                                                   │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │   │
│  │  │  Webhook     │  │  Admin API   │  │  Static Files            │ │   │
│  │  │  Router      │  │  Router      │  │  (Dashboard SPA)         │ │   │
│  │  │              │  │              │  │                          │ │   │
│  │  │ /webhook/    │  │ /admin/*     │  │ / → index.html          │ │   │
│  │  │  telegram    │  │              │  │                          │ │   │
│  │  └──────┬───────┘  └──────┬───────┘  └────────────▲─────────────┘ │   │
│  │         │                 │  SSE events     │   REST API calls      │   │
│  │  ┌──────▼─────────────────▼────────────────┼───────────────────┐  │   │
│  │  │              Services Layer              │                   │  │   │
│  │  │                                         │                   │  │   │
│  │  │  ┌──────────┐ ┌───────────┐ ┌────────┐ │                   │  │   │
│  │  │  │ Game     │ │ Telegram  │ │ Race   │ │                   │  │   │
│  │  │  │ Engine   │ │ Service   │ │ Master │ │                   │  │   │
│  │  │  └────┬─────┘ └───────────┘ └────────┘ │                   │  │   │
│  │  │       │                                  │                   │  │   │
│  │  │  ┌────▼─────────┐ ┌───────────────────┐  │                   │  │   │
│  │  │  │ Event Bus    │ │ Vision Service    │  │                   │  │   │
│  │  │  │ (in-memory   │ │ (Gemini API)      │  │                   │  │   │
│  │  │  │  pub/sub)    │ └───────────────────┘  │                   │  │   │
│  │  │  └────┬────────────────────────────────┘                   │  │   │
│  │  └───────┼────────────────────────────────────────────────────┘  │   │
│  │          │                                                       │   │
│  │  ┌───────▼───────────────────────────────────────────────────┐   │   │
│  │  │              SQLite Database (aiosqlite)                  │   │   │
│  │  │                                                           │   │   │
│  │  │  teams │ team_members │ checkpoints │ submissions │       │   │   │
│  │  │  live_telemetry                                             │   │   │
│  │  └───────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              Systemd Service                                     │   │
│  │  amk-heritage-backend.service  →  auto-restart on failure       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                     │
│                                                                          │
│   ┌──────────────────────┐          ┌──────────────────────────────┐    │
│   │  Team Telegram       │          │  HQ Dashboard (Browser)       │    │
│   │  Group Chats         │          │                              │    │
│   │                      │          │  - Live map + GPS markers    │    │
│   │  - Send photos       │          │  - Leaderboard + rankings    │    │
│   │  - Send location     │          │  - Photo/video gallery       │    │
│   │  - /join /status     │          │  - Race controls             │    │
│   │  - Receive updates   │          │  - HQ messaging              │    │
│   │                      │          │  - Event log (SSE)           │    │
│   └──────────────────────┘          └──────────────────────────────┘    │
│                                                                          │
│   ┌──────────────────────┐                                              │
│   │  HQ Telegram Chat    │                                              │
│   │                      │                                              │
│   │  - Receive submissions│                                             │
│   │  - Approve / Reject  │                                              │
│   │  - Assign checkpoint  │                                             │
│   └──────────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Photo Submission Flow

```
Team sends photo in Telegram group
        │
        ▼
Telegram API ──► POST /webhook/telegram
        │
        ▼
Download photo → Save locally → Upload to Google Drive (background)
        │
        ├─── Try AI identification (Gemini Vision)
        │    │
        │    ├── Match found → Auto-approve → +50 pts → Notify team & HQ
        │    │
        │    └── No match (or video) ──► Forward to HQ Telegram
        │                                     │
        │                                     ├── HQ clicks [Approve]
        │                                     │      │
        │                                     │      ▼
        │                                     │   Select checkpoint
        │                                     │      │
        │                                     │      ▼
        │                                     │   +50 pts → Notify team
        │                                     │
        │                                     └── HQ clicks [Reject]
        │                                            │
        │                                            ▼
        │                                         Notify team: "Try again"
        │
        ▼
Event Bus ──► SSE ──► Dashboard updates (map, leaderboard, gallery)
```

### Location Check-in Flow

```
Team sends GPS location in Telegram
        │
        ▼
Telegram API ──► POST /webhook/telegram
        │
        ▼
game_engine.process_location_update()
        │
        ├─── Save telemetry to DB + publish to Event Bus
        │
        └─── Calculate Haversine distance to current checkpoint
             │
             ├─── Within 50m → Auto-approve checkpoint → +50 pts → Advance
             │
             └─── Too far → Ignore
```

---

## Race Mechanics

| Action | Points |
|--------|--------|
| Clear a checkpoint | +50 |
| Complete all 12 checkpoints (bonus) | +100 |
| Maximum possible score | **700** |

Teams progress through 12 checkpoints in order. Each checkpoint requires either a photo submission (approved by HQ or AI) or a GPS check-in within 50m radius.

### Game States

```
NOT_STARTED → IN_PROGRESS → PAUSED → IN_PROGRESS → COMPLETED
                  │                              │
                  └──────── reset ────────────────┘
```

---

## The 12 Checkpoints

| # | Checkpoint | Zone |
|---|-----------|------|
| 1 | Cheng San Community Club | Cheng San |
| 2 | Dragon Playground | Kebun Baru |
| 3 | AMK Town Centre (Heart AMK) | Town Centre |
| 4 | Masjid Al-Muttaqin | Teck Ghee |
| 5 | Church of Christ the King | Yio Chu Kang |
| 6 | ActiveSG Sport Park @ Teck Ghee | Teck Ghee |
| 7 | Teck Ghee Court Market & Food Centre | Teck Ghee |
| 8 | Kebun Baru Birdsinging Club | Kebun Baru |
| 9 | Kebun Baru Market & Food Centre | Kebun Baru |
| 10 | Ang Mo Kio Joint Temple | Town Centre |
| 11 | Merlion (Ang Mo Kio) | Town Centre |
| 12 | Ang Mo Kio Community Centre (Finish) | Town Centre |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Uvicorn (async) |
| Telegram | aiogram v3 |
| Database | SQLite via SQLAlchemy + aiosqlite |
| Dashboard | Vanilla HTML/CSS/JS SPA (Leaflet.js for maps) |
| Cloud Storage | Google Drive (OAuth2) |
| AI Vision | Google Gemini (planned, currently stub) |
| Server | Nginx, Let's Encrypt, Systemd |
| Tunnel | Cloudflare Tunnel (cloudflared) |

---

## Project Structure

```
heritage_trail/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app, lifespan, webhook/polling setup
│   │   ├── config.py             # Pydantic settings (from .env)
│   │   ├── database.py           # SQLAlchemy async engine + session
│   │   ├── models/               # ORM models (Team, Checkpoint, Submission, etc.)
│   │   ├── schemas/              # Pydantic schemas for API validation
│   │   ├── routers/
│   │   │   ├── webhook.py        # Telegram webhook handler
│   │   │   └── admin.py          # Admin REST API + GDrive proxy
│   │   ├── services/
│   │   │   ├── game_engine.py    # Core race logic (scoring, advancement)
│   │   │   ├── telegram_service.py
│   │   │   ├── race_master.py    # Race lifecycle controls
│   │   │   ├── event_bus.py      # In-memory pub/sub for SSE
│   │   │   ├── vision_service.py # AI checkpoint ID (stub)
│   │   │   └── geo_service.py    # Haversine distance calculation
│   │   └── static/
│   │       └── index.html        # HQ Dashboard SPA
│   ├── requirements.txt
│   ├── seed_checkpoints.py       # Seeds 12 checkpoints into DB
│   └── heritage_trail.db         # SQLite database
├── checkpoint_images/            # Reference images for checkpoints
├── submissions/                  # Local copy of team submissions
├── dashboard/                    # (Unused) Earlier Node.js design
├── nginx-amk-heritage.conf      # Nginx reverse proxy config
├── amk-heritage-backend.service # Systemd unit file
├── deploy.sh                     # Production deployment script
├── start.sh                      # Local dev launcher (tmux)
├── .env                          # Environment variables (gitignored)
└── .env.example                  # Environment variable template
```

---

## Setup

### Prerequisites

- Python 3.11+
- A Telegram Bot (via [@BotFather](https://t.me/BotFather))
- Google OAuth2 credentials (for Drive storage)
- Google Gemini API key (optional, for AI vision)

### 1. Clone and install

```bash
git clone https://github.com/OriginalNneo/amk_heritage.git
cd heritage_trail/backend
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp ../.env.example ../.env
```

Edit `.env` with your values:

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Token from @BotFather |
| `TELEGRAM_WEBHOOK_URL` | Public HTTPS URL for webhook (leave empty for polling mode) |
| `RACE_MASTER_USER_ID` | Telegram user ID of the race marshal |
| `DATABASE_URL` | SQLite connection string (default: `sqlite+aiosqlite:///./heritage_trail.db`) |
| `VISION_API_KEY` | Google Gemini API key |
| `GDRIVE_CLIENT_ID` | Google OAuth2 client ID |
| `GDRIVE_CLIENT_SECRET` | Google OAuth2 client secret |
| `GDRIVE_REFRESH_TOKEN` | Google OAuth2 refresh token |
| `GDRIVE_FOLDER_ID` | Google Drive folder ID for submissions |
| `HQ_CHAT_ID` | Telegram group ID for HQ marshals |

### 3. Seed checkpoints

```bash
python seed_checkpoints.py
```

### 4. Run (development)

```bash
# Quick start with tmux (backend + setup)
bash ../start.sh

# Or manually:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Run (production)

```bash
bash deploy.sh
```

This copies the project to `/opt/amk_heritage/`, installs dependencies, and creates a systemd service.

---

## API Endpoints

### Race Controls

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/race/start` | Start the race |
| POST | `/admin/race/pause` | Pause the race |
| POST | `/admin/race/resume` | Resume the race |
| POST | `/admin/race/end` | Force-end the race |
| POST | `/admin/race/reset` | Reset all progress |
| GET | `/admin/race/status` | Current race status |

### Teams

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/teams` | List all teams |
| POST | `/admin/teams` | Create a team |
| GET | `/admin/teams/{id}` | Team details |
| PUT | `/admin/teams/{id}` | Update team |
| POST | `/admin/teams/{id}/score?delta=N` | Adjust score |
| POST | `/admin/teams/{id}/advance` | Skip to next checkpoint |

### Submissions & Gallery

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/submissions` | All submissions |
| GET | `/admin/teams/{id}/gdrive-images` | Team photos from Google Drive |
| GET | `/admin/gdrive-image/{file_id}` | Proxy-serve a GDrive file |

### Real-time

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/events/stream` | SSE event stream (map markers + race events) |

### Telegram Webhook

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhook/telegram` | Receives Telegram updates |

---

## Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/join <name>` | Join the race (register as a team member) |
| `/status` | Check current team progress |
| `/checkpoints` | View all checkpoint names |
| `/hint` | Get a hint for the current checkpoint |

---

## Dashboard Features

- **Live map** with real-time GPS markers from teams (Leaflet.js)
- **Leaderboard** with scores, progress bars, rank badges, and pace tracking
- **Photo/video gallery** per team (sourced from Google Drive)
- **Race controls** (start, pause, resume, end, reset)
- **HQ messaging** (send to individual teams or broadcast to all)
- **Event log** with live updates via Server-Sent Events
- **5 AMK zones** displayed: Town Centre, Teck Ghee, Kebun Baru, Cheng San, Yio Chu Kang

---

## License

Private project for AMK Heritage Trail 2026.
