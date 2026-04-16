# Build & Deploy

## Local Setup

1. Use Python 3.12.
2. Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

3. Set runtime environment variables as needed:

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
export DB_PATH="./postings.db"
export PORT=8080
```

## Run Locally

```bash
python main.py
```

Health and feed checks:

```bash
curl http://localhost:8080/health
curl "http://localhost:8080/feed?since=0"
```

## Test

```bash
python3 -m pytest tests -q
```

## Docker

The container uses `python:3.12-slim`, installs the Chromium system libraries
required by Playwright, and downloads the Playwright Chromium browser during the
image build.

```bash
docker build -t jojo-scraper .
docker run --rm -p 8080:8080 \
  -e DISCORD_WEBHOOK_URL \
  -e DB_PATH=/tmp/postings.db \
  jojo-scraper
```

## Polling Interval Tuning

Polling intervals can be tuned without code changes:

```bash
export POLL_GREENHOUSE_MINUTES=15
export POLL_ASHBY_MINUTES=15
export POLL_LEVER_MINUTES=15
export POLL_AMAZON_MINUTES=30
export POLL_APPLE_MINUTES=30
export POLL_WORKDAY_MINUTES=60
```

The active production policy now polls only direct company-controlled sources.
