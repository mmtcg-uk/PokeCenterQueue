# Pokémon Center Queue Notifier

Tracks Pokémon Center queues (US, UK, CA) and sends Discord alerts when they go live.

## Features
- Multi-region tracking
- Discord webhook alerts
- Fast polling (15s default)
- No duplicate alerts

## Setup

### Install
pip install -r requirements.txt

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | ✅ Yes | Webhook for queue alert messages |
| `BROWSERLESS_WS_URL` | ✅ Yes | Browserless WebSocket endpoint |
| `CHECK_INTERVAL_SECONDS` | No | Poll interval in seconds (default: `20`) |
| `MENTION_TEXT` | No | Mention string in alerts (default: `@everyone`) |
| `STATUS_WEBHOOK_URL` | No | Separate webhook for startup/heartbeat messages. If unset, status messages are silently disabled |

### Run locally
export DISCORD_WEBHOOK_URL="your webhook"
export CHECK_INTERVAL_SECONDS=15
python main.py

## Deploy (Railway)
- Deploy repo
- Add env variables
- Done 🎉
