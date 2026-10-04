# Campus Customs: Yale Apparel Shop + AI Shopping Assistant (HW4)

A full-stack storefront for **Campus Customs**, a Yale spirit-wear shop, with a **PydanticAI chatbot** that looks up real products, prices and stock, updates the page with search results, remembers logged-in customers, and follows strict safety and privacy rules.

- **Frontend:** Vite + React + TypeScript (`frontend/`)
- **Backend:** FastAPI + PydanticAI agent (`backend/`), model `gpt-5.6` through Portkey's OpenAI-compatible API
- **Data:** SQLite database plus product images (local-only data pack, **not in git**)

## Where to look (for grading)

| What | File |
|---|---|
| How the whole system works (architecture, model fields, tools, safety, specs) | [`output/harness.md`](output/harness.md) (start with the **Problem 12** section) |
| Live site test with screenshots | [`output/app_check.html`](output/app_check.html) (screenshots in [`output/app_check_images/`](output/app_check_images/)) |
| Usability improvements (filters, Going Fast, theme, bulldog, async, privacy) | [`output/usability.md`](output/usability.md) |
| Design changes (fonts, color, hierarchy, motion, product cards, chat) | [`output/design.md`](output/design.md) |
| Append-only agent audit trail | [`output/audit_trail.json`](output/audit_trail.json) |
| Every prompt used to build it, by problem | [`AI_prompts.md`](AI_prompts.md) |

> GitHub shows `app_check.html` as source code. To view it as a webpage, clone the repo and open the file in a browser. The screenshots are also viewable directly in `output/app_check_images/`.

## The agent (4 files in `backend/`)

| File | Role |
|---|---|
| `prompts/prompt.md` | System prompt: Campus Customs voice, how to use the tools, results-page rules, customer memory and page context, safety rules |
| `agent.py` | Agent wiring: Portkey model, prompt and context instructions, output checks (no invented prices or quantities, privacy, no links), step-by-step loop that writes the audit trail |
| `tools.py` | Read-only tools: `search_products`, `get_product_details`, `check_stock`, `list_categories` (plus product-card and results-page builders) |
| `models.py` | PydanticAI structured types: `ShopReply`, tool results, chat request and response, customer, page context, audit entry |

Supporting backend modules: `main.py` (FastAPI routes), `catalog.py` (read-only catalogue queries and filters), `auth.py` (accounts and sessions), `chat_history.py` (saved chats), `privacy.py` (redaction, reply checks, rate limit), `audit.py` (append-only audit trail).

## Setup

### 1. Place the data pack (not included in this repo)

The database and product images are local-only. Put them in a `data/` folder at the top of the project:

```
hw4/
└── data/
    ├── campus_customs.db     # SQLite: catalogue, inventory, users, chat_messages
    └── products/             # product images referenced by the catalogue (*.jpg)
```

### 2. Add your API key

```bash
cp .env.example .env
# edit .env and set PORTKEY_API_KEY=<your Portkey key>
```

`.env` is git-ignored. Never commit a real key.

### 3. Install

Requires Python 3.12+ and Node 20+.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd frontend && npm install && cd ..
```

## Run

Use two terminals, both starting in the project folder (`hw4/`).

**Backend (FastAPI + agent), port 8000:**
```bash
cd backend
../.venv/bin/uvicorn main:app --reload --port 8000
```
(If your virtual environment is activated, `uvicorn main:app --reload --port 8000` works too.)

**Frontend (Vite dev server), port 5174:**
```bash
cd frontend
npm run dev
```

Open **http://127.0.0.1:5174**. The frontend forwards `/api` and `/images` to the backend on port 8000. To use a different backend URL, set `BACKEND_URL`, e.g. `BACKEND_URL=http://127.0.0.1:8010 npm run dev`. API docs are at http://127.0.0.1:8000/docs.

On first start, the backend adds a `sessions` table and two nullable columns to `chat_messages` in your local database if they're missing. It never deletes data.

## Features

- **Shop:**
  - Home, Products (search plus **Shop For / Product Type / Color / Size / Price** filters with live counts), product detail (zoom, per-size stock), **🔥 Going Fast** (lowest-stock items) and About.
  - Accounts: create account and log in, with PBKDF2-hashed passwords and HttpOnly session cookies.
  - **☀ / ☾** light/dark theme and a cursor-following bulldog on the home page.
- **Chatbot:**
  - Answers from live product data: exact prices, and stock by size, including clear out-of-stock answers.
  - Opens a results page of product cards for category questions.
  - Understands "it" and "this" from the page you're on.
  - Saves chats for logged-in customers (guests' chats aren't saved).
- **Safety:**
  - The agent sees only the customer's name and email.
  - Card numbers, phone numbers, addresses and passwords are removed before the model or the database see them.
  - Replies are checked for invented numbers, requests for personal data, and links.
  - Rate limit, 10-model-call loop limit, and an append-only audit trail of every agent step.

## Project layout

```
hw4/
├── AI_prompts.md
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── frontend/                 # Vite React TypeScript app
├── backend/
│   ├── main.py               # FastAPI app — run with: uvicorn main:app --reload --port 8000
│   ├── agent.py
│   ├── models.py
│   ├── tools.py
│   ├── prompts/
│   │   └── prompt.md
│   └── (catalog.py, auth.py, chat_history.py, privacy.py, audit.py)
└── output/
    ├── harness.md
    ├── design.md
    ├── usability.md
    ├── app_check.html
    ├── app_check_images/     # screenshots linked from app_check.html
    └── audit_trail.json
```

Local-only data pack (not in git): `data/campus_customs.db` and `data/products/`.
