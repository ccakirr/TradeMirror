# TradeMirror

A privacy-first trading journal that tells you what a trade risked — before and after you took it.

TradeMirror never connects to a broker. There are no API keys, no credentials, no imported order history: you journal your own trades, and the app turns them into risk metrics, plan-violation findings and a behavioral picture of the account. Every number on a trade's report is a rule you can re-check by hand; a machine-learning score sits next to those rules, never in place of them.

> TradeMirror is a decision-support and self-awareness tool. It is not investment advice and it produces no buy/sell signals.

---

## What it does

- **Accounts and journal** — multiple trading accounts per user, each with its own balance, trade list and realized P&L. Trades are opened with an entry price, size and optional stop/target, then closed with an exit price; P&L settles the account balance automatically.
- **Instrument catalog** — 1,478 instruments (1,372 Binance spot pairs, 106 broker CFDs across forex, metals, energy, indices and stocks). Every price must land on the instrument's tick and every position on its lot step, so a journaled trade is always well-formed.
- **Per-account risk profile** — how the account is *supposed* to trade: risk per trade, trade frequency, average hold times, diversification, plan adherence and sizing discipline.
- **Automatic risk assessment** — once a profile exists, opening and closing a trade each store a scored assessment (`entry` / `exit` stage) from the trained model.
- **Explainable risk report** — one endpoint turns a trade into a list of findings (stop set? risk within limit? reward/risk? exposure? did the exit honor the plan? was the loss held too long?), each with the numbers behind it and a severity level. The findings are scored into an overall `low` / `medium` / `high` class.
- **React workspace** — dashboard, accounts, per-trade detail and behavior panel, in English and Turkish, light and dark.

## Stack

| Layer | Choice |
| --- | --- |
| API | FastAPI, Pydantic v2, Uvicorn |
| Data | PostgreSQL, SQLAlchemy 2, Alembic |
| Auth | Argon2 password hashing (`pwdlib`), JWT bearer tokens (`PyJWT`) |
| ML | scikit-learn logistic regression, loaded from a `joblib` artifact at import |
| Client | React 19 + Vite, no UI framework |
| Runtime | Python 3.14, Node 22, single container |

## Layout

```
backend/
  app/
    api/         FastAPI routers (auth, accounts+trades, predict, instruments)
    core/        settings, JWT/password helpers, auth dependency, instrument catalog
    models/      SQLAlchemy tables
    schemas/     request/response models
    services/    business logic — trades, accounts, risk assessment, risk report
    data/        instruments.json (generated)
  migrations/    Alembic revisions
  scripts/       sync_instruments.py
  tests/         pytest suite (runs against a real database)
frontend/
  src/
    components/  screens and widgets
    lib/         API client, i18n, formatting, client-side trade math
artifacts/       trained model + feature schema + metrics
ml/notebooks/    data audit, preprocessing, model research, model selection
```

---

## Getting started

### Prerequisites

- Python 3.14
- Node 22
- PostgreSQL 16 (a `docker-compose.yml` is included for local use)

### 1. Database

```bash
docker compose up -d postgres
```

This brings up Postgres on `localhost:5432` with user/password/database `trademirror` / `trademirror_dev` / `trademirror`.

### 2. Environment

Copy `.env.example` to `.env` and fill it in:

| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `DATABASE_URL` | yes | — | `postgres://` and `postgresql://` are rewritten to `postgresql+psycopg://` automatically |
| `JWT_SECRET_KEY` | yes | — | any long random string; rotating it invalidates every issued token |
| `MODEL_PATH` | no | `artifacts/product_blowup_risk_logistic_v1.joblib` | |
| `JWT_ALGORITHM` | no | `HS256` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | `60` | |

```dotenv
DATABASE_URL=postgresql://trademirror:trademirror_dev@localhost:5432/trademirror
JWT_SECRET_KEY=change-me
```

### 3. Backend

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/uvicorn backend.app.main:app --reload
```

The API listens on `http://127.0.0.1:8000`; interactive docs are at `/docs`.

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite serves the client on `http://127.0.0.1:5173` and proxies `/api` and `/health` to the backend, so both halves share one origin in development exactly as they do in production.

---

## API

All paths are prefixed with `/api/v1`. Authenticated routes expect `Authorization: Bearer <token>`.

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health` | — | liveness probe (unprefixed) |
| `POST` | `/auth/register` | — | create a user (409 if the email exists) |
| `POST` | `/auth/login` | — | exchange email + password for a token |
| `GET` | `/auth/me` | ✓ | current user |
| `GET` | `/instruments/` | — | the tradable catalog with tick and lot steps |
| `POST` | `/predict/` | — | score a raw feature payload against the model |
| `POST` | `/accounts/` | ✓ | create a trading account |
| `GET` | `/accounts/` | ✓ | list active accounts |
| `PUT` | `/accounts/{account_id}/risk-profile` | ✓ | create or replace the account's risk profile |
| `GET` | `/accounts/{account_id}/risk-profile` | ✓ | read it (404 until one is saved) |
| `POST` | `/accounts/{account_id}/trades` | ✓ | open a trade |
| `GET` | `/accounts/{account_id}/trades` | ✓ | the journal, newest first |
| `GET` | `/accounts/{account_id}/trades/{trade_id}` | ✓ | one trade |
| `POST` | `/accounts/{account_id}/trades/{trade_id}/close` | ✓ | close it at an exit price and settle P&L |
| `POST` | `/accounts/{account_id}/trades/{trade_id}/risk-assessments` | ✓ | store a manual assessment |
| `GET` | `/accounts/{account_id}/trades/{trade_id}/risk-assessments` | ✓ | assessment history |
| `GET` | `/accounts/{account_id}/trades/{trade_id}/risk-report` | ✓ | the explainable report |

Prices and sizes are serialized as plain decimal strings (never `1E-8`), because the client parses them as exact numbers.

---

## The risk model

`artifacts/product_blowup_risk_logistic_v1.joblib` is a logistic regression trained on 50,000 rows of the `retail_trader_master.csv` retail-trader dataset, against a `blew_up` target. It does not predict that an account *will* fail; it classifies how closely the account's habits resemble profiles that already lost serious capital.

**Features (11):** `starting_capital`, `account_age_months`, `instrument`, `risk_per_trade_pct`, `trades_per_month`, `uses_stop_loss`, `avg_win_hold_days`, `avg_loss_hold_days`, `diversification`, `follows_plan`, `position_sizing_discipline`.

**Held-out metrics (`product_v1`):** ROC AUC 0.638 · precision 0.506 · recall 0.785 · F1 0.615. The operating threshold is 0.4166 — tuned toward recall, since missing a fragile account costs more than an extra warning.

**Classes:** `score ≥ 0.70` → high · `score ≥ 0.4166` → medium · otherwise low.

The notebooks that produced it live in `ml/notebooks/` (`00_data_audit` → `03_product_model_selection`). The training data under `data/` is not committed, so the notebooks need the dataset supplied locally before they will run.

## How a risk report is built

`backend/app/services/risk_report.py` walks a trade through six checks and emits a finding per rule. Each finding carries a code, a level (`good` / `info` / `warn` / `bad`) and the raw values behind it — the wording lives in the client so both languages read naturally.

| Check | Findings |
| --- | --- |
| Stop and what it risks | `stop_missing`, `stop_set`, `risk_within_limit`, `risk_above_limit`, `risk_far_above_limit` |
| What the plan expected back | `target_missing`, `rr_strong`, `rr_thin`, `rr_negative` |
| Size against the account | `exposure_high`, `exposure_extreme` |
| How it actually ended | `exit_target`, `exit_stop`, `exit_manual`, `exit_manual_no_plan`, `loss_exceeded_stop` |
| Hold time vs. this account's own averages | `held_loss_too_long`, `cut_win_early` |
| The model, last | `model_low`, `model_medium`, `model_high`, `model_missing`, `profile_missing` |

Findings are scored (`warn` = 1, `bad` = 2; the model contributes 0/2/4 for low/medium/high) and the total decides the report's class: 4+ is high, 2+ is medium. Risk is measured against the balance as it stood *before* the trade settled, so a losing trade is never flattered by the balance it shrank. Without a saved profile the report falls back to a 2%-per-trade limit and says so.

---

## Tests

```bash
.venv/bin/python -m pytest backend/tests
```

The suite exercises the real application against a real database — it registers users, opens trades and cleans up after itself. Point `DATABASE_URL` at a development database and make sure migrations are applied first.

## Instrument catalog

`backend/app/data/instruments.json` is generated, not hand-edited:

```bash
.venv/bin/python -m backend.scripts.sync_instruments
```

Binance spot pairs (with their real tick and lot filters) are pulled live; the CFD block is a curated list of symbols brokers conventionally offer, with the tick sizes a five-digit broker normally quotes — adjust it against a specific broker's contract schedule if you need exact specs. Position sizes are journaled in units of the base asset, not lots, because P&L settles as `(exit − entry) × position_size`.

## Deployment

The `Dockerfile` builds the React client first, then copies `frontend/dist` into the Python image. At startup the container runs `alembic upgrade head` and then Uvicorn; the API keeps its `/api` prefix and every other request is served the SPA entry point.

```bash
docker build -t trademirror .
docker run -p 8000:8000 -e DATABASE_URL=... -e JWT_SECRET_KEY=... trademirror
```

It is set up for Railway, which supplies `DATABASE_URL` and `PORT`.
