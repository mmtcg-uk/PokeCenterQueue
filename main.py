import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

import requests
from playwright.sync_api import sync_playwright

# 🔥 DEBUG START
print("🔥 BOT STARTING...", flush=True)
print(f"🐍 Python version: {sys.version}", flush=True)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "20"))
MENTION_TEXT = os.getenv("MENTION_TEXT", "@everyone")
BROWSERLESS_WS_URL = os.getenv("BROWSERLESS_WS_URL", "")

print(f"🔑 Webhook set: {bool(DISCORD_WEBHOOK_URL)}", flush=True)
print(f"🌐 Browserless URL set: {bool(BROWSERLESS_WS_URL)}", flush=True)

if not BROWSERLESS_WS_URL:
    raise RuntimeError("❌ BROWSERLESS_WS_URL is not set")

STATE_FILE = Path("state.json")
HEARTBEAT_FILE = Path("heartbeat.txt")

STORES = {
    "US": {
        "name": "Pokémon Center US",
        "flag": "🇺🇸",
        "url": "https://www.pokemoncenter.com/en-us",
    },
    "UK": {
        "name": "Pokémon Center UK",
        "flag": "🇬🇧",
        "url": "https://www.pokemoncenter.com/en-gb",
    },
    "CA": {
        "name": "Pokémon Center Canada",
        "flag": "🇨🇦",
        "url": "https://www.pokemoncenter.com/en-ca",
    },
}

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass

    return {
        code: {
            "was_live": False,
            "last_final_url": None,
        }
        for code in STORES
    }


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def send_discord_message(payload: dict):
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ DISCORD_WEBHOOK_URL not set", flush=True)
        return

    response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)
    response.raise_for_status()


def send_discord_alert(store: Dict[str, str], final_url: str):
    payload = {
        "content": f"{MENTION_TEXT} 🚨 **QUEUE LIVE** 🚨",
        "embeds": [
            {
                "title": f"{store['flag']} {store['name']} Queue Detected",
                "url": store["url"],
                "description": (
                    "🟢 **Queue is LIVE — act fast!**\n\n"
                    f"👉 [Open Store]({store['url']})\n"
                    f"👉 [Join Queue]({final_url})"
                ),
                "color": 16711680,
                "footer": {
                    "text": "PokeCenter Monitor • Live Alert"
                },
            }
        ],
    }

    try:
        send_discord_message(payload)
        print(f"📨 Discord alert sent for {store['name']}", flush=True)
    except Exception as e:
        print(f"Discord error: {e}", flush=True)


def send_status_message(text: str):
    payload = {"content": text}
    try:
        send_discord_message(payload)
    except Exception as e:
        print(f"Status message error: {e}", flush=True)


def detect_queue(page, store_url: str) -> Tuple[bool, str]:
    print(f"🌍 Visiting {store_url}", flush=True)

    response = page.goto(store_url, wait_until="domcontentloaded", timeout=45000)

    status = None if response is None else response.status
    final_url = page.url

    print(f"➡️ Status: {status} | Final URL: {final_url}", flush=True)

    if response is not None and response.status >= 400:
        raise RuntimeError(f"HTTP {response.status} for {store_url}")

    page.wait_for_timeout(3000)

    final_url = page.url
    final_url_lower = final_url.lower()

    try:
        text = page.locator("body").inner_text(timeout=10000).lower()
    except Exception:
        text = ""

    indicators = [
        "queue-it",
        "waiting room",
        "virtual queue",
        "line is paused",
        "you are now in line",
        "queue",
    ]

    is_live = any(x in final_url_lower for x in indicators) or any(
        x in text for x in indicators
    )

    return is_live, final_url


def main():
    state = load_state()

    print("🚀 Watcher started...", flush=True)
    print(f"⏱ Checking every {CHECK_INTERVAL_SECONDS} seconds", flush=True)

    startup_sent = False

    with sync_playwright() as p:
        print("🔌 About to connect to Browserless...", flush=True)

        browser = p.chromium.connect_over_cdp(BROWSERLESS_WS_URL)

        print("✅ Connected to Browserless", flush=True)

        context = browser.new_context(
            user_agent=BROWSER_USER_AGENT,
            locale="en-GB",
            viewport={"width": 1440, "height": 900},
        )

        while True:
            try:
                if not startup_sent:
                    send_status_message("✅ PokeCenter Monitor is online")
                    startup_sent = True

                HEARTBEAT_FILE.write_text(str(int(time.time())))

                for code, store in STORES.items():
                    page = context.new_page()

                    try:
                        is_live, final_url = detect_queue(page, store["url"])
                        was_live = state[code]["was_live"]

                        print(f"{code}: {is_live}", flush=True)

                        if is_live and not was_live:
                            send_discord_alert(store, final_url)

                        state[code]["was_live"] = is_live
                        state[code]["last_final_url"] = final_url

                    except Exception as e:
                        print(f"{code} error: {e}", flush=True)

                    finally:
                        page.close()

                save_state(state)

            except Exception as e:
                print(f"Main loop error: {e}", flush=True)

            time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
