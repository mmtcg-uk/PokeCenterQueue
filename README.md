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

### Run locally
export DISCORD_WEBHOOK_URL="your webhook"
export CHECK_INTERVAL_SECONDS=15
python main.py

## Deploy (Railway)
- Deploy repo
- Add env variables
- Done 🎉
