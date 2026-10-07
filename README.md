# 📊 Smart E-commerce Price Tracker & Alert System

A production-grade price tracking application built with Streamlit, SQLAlchemy, APScheduler, and BeautifulSoup4. Track prices across Amazon, Flipkart, and any e-commerce site, visualize trends, and get alerted when prices drop.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔍 Web Scraping | Amazon, Flipkart, and generic fallback (Open Graph / JSON-LD) |
| 🗄️ Database | SQLAlchemy ORM with SQLite (or PostgreSQL) |
| ⏱ Auto-Scheduler | APScheduler background job — check prices on a configurable interval |
| 🔔 Alerts | Console + optional SMTP email when price drops below threshold |
| 📈 Charts | Interactive Plotly price-history charts and comparison bar chart |
| 🔐 Config | All secrets managed via `.env` (python-dotenv) |
| 🧪 Tests | pytest unit tests for scraper and database layers |

---

## 🗂 Project Structure

```
price_tracker/
├── main.py                        # Streamlit frontend (entry point)
├── requirements.txt
├── .env.example                   # Template — copy to .env
│
├── app/
│   ├── config.py                  # Centralised settings via python-dotenv
│   │
│   ├── scraper/
│   │   ├── __init__.py
│   │   └── scraper.py             # ProductScraper — Amazon / Flipkart / Generic
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   └── models.py              # SQLAlchemy ORM models + DatabaseManager
│   │
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── job_manager.py         # APScheduler background price-check job
│   │
│   └── utils/
│       ├── __init__.py
│       └── notifier.py            # Console + SMTP alert dispatcher
│
├── data/                          # SQLite DB lives here (auto-created)
├── logs/                          # Log files (auto-created)
└── tests/
    └── test_core.py               # pytest unit tests
```

---

## ⚡ Quick Start

### 1. Clone / Download

```bash
git clone <repo-url>
cd price_tracker
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your preferences:

```env
DATABASE_URL=sqlite:///data/price_tracker.db
CHECK_INTERVAL_MINUTES=30

# Optional — enable email alerts
EMAIL_ENABLED=false
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_RECIPIENT=notify@example.com
```

> **Gmail tip:** Use an [App Password](https://myaccount.google.com/apppasswords) (not your normal password) when `EMAIL_ENABLED=true`.

### 5. Run the app

```bash
streamlit run main.py
```

Open your browser at **http://localhost:8501**

### 6. Run tests (optional)

```bash
python -m pytest tests/ -v
```

---

## 🖥 UI Walkthrough

### Products Tab
- Paste any Amazon / Flipkart / e-commerce URL and click **Scrape & Track**
- Optionally set an alert price and email in the same form
- Each product card shows: current price, availability, site, last checked
- Per-card actions: **History**, **Refresh**, **Set Alert**, **Remove**

### Price Charts Tab
- Overview bar chart comparing all tracked product prices
- Detailed line chart per product with min/max annotations and stats table

### Alerts Tab
- View and delete active price-drop alerts

### Sidebar
- Start / Stop the background scheduler
- Adjust check interval (5–240 minutes)
- Trigger an immediate manual check of all products

---

## 🏗 Architecture

```
User (Browser)
    │
    ▼
Streamlit UI (main.py)
    │
    ├──► ProductScraper        (requests + BeautifulSoup4 + lxml)
    │         │
    │         └──► ScrapedProduct (dataclass result)
    │
    ├──► DatabaseManager       (SQLAlchemy → SQLite / PostgreSQL)
    │         │
    │         ├── Product table
    │         ├── PriceHistory table
    │         └── Alert table
    │
    ├──► PriceCheckScheduler   (APScheduler BackgroundScheduler)
    │         │ runs every N minutes
    │         └──► scrape → record → notify
    │
    └──► AlertNotifier         (console log + optional SMTP email)
```

---

## 🔧 Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///data/price_tracker.db` | SQLAlchemy DB URL |
| `CHECK_INTERVAL_MINUTES` | `30` | Auto price-check frequency |
| `EMAIL_ENABLED` | `false` | Enable SMTP email alerts |
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server host |
| `SMTP_PORT` | `587` | SMTP port (TLS) |
| `SMTP_USER` | — | Your email address |
| `SMTP_PASSWORD` | — | App password |
| `ALERT_RECIPIENT` | — | Where to send alerts |
| `REQUEST_TIMEOUT` | `15` | HTTP timeout (seconds) |
| `SCRAPE_DELAY` | `2` | Politeness delay between requests |
| `LOG_LEVEL` | `INFO` | Python logging level |

---

## 📝 Notes & Limitations

- **Amazon / Flipkart anti-scraping:** Both sites actively block scrapers. Scraping may fail intermittently depending on region, IP, and session. For reliable production use, consider a proxy service or official Product Advertising API.
- **Rate limiting:** The `SCRAPE_DELAY` setting adds a polite pause between requests to reduce the chance of being blocked.
- **PostgreSQL:** Change `DATABASE_URL` to `postgresql://user:pass@host:5432/dbname` and install `psycopg2-binary`.
- **Deployment:** Works great on a VPS or Raspberry Pi. Run with `nohup streamlit run main.py &` or wrap in a systemd service.

---

## 📄 License

MIT — free for personal and commercial use.
