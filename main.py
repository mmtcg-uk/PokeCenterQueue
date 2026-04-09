import json
import os
import time
from pathlib import Path
from typing import Dict, Tuple

import requests

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "15"))
MENTION_TEXT = os.getenv("MENTION_TEXT", "@everyone")
STATE_FILE = Path("state.json")

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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass

    return {
        store_code: {
            "was_live": False,
            "last_final_url": None,
            "last_alerted_url": None,
        }
        for store_code in STORES
    }


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def queue_is_live(store_url: str) -> Tuple[bool, str]:
    response = requests.get(
        store_url,
        headers=HEADERS,
        allow_redirects=True,
        timeout=20,
    )
    response.raise_for_status()

    final_url = response.url
    final_url_lower = final_url.lower()
    body = response.text.lower()

    url_indicators = ["queue-it", "waitingroom", "queue"]
    text_indicators = ["virtual queue", "waiting room", "queue-it", "line is paused"]

    is_live = any(x in final_url_lower for x in url_indicators) or any(
        x in body for x in text_indicators
    )

    return is_live, final_url


def send_discord_alert(store: Dict[str, str], final_url: str):
    mention_parse = []
    if "@everyone" in MENTION_TEXT or "@here" in MENTION_TEXT:
        mention_parse.append("everyone")

    payload = {
        "content": f"{MENTION_TEXT} {store['flag']} {store['name']} queue is LIVE",
        "allowed_mentions": {"parse": mention_parse},
        "embeds": [
            {
                "title": f"{store['flag']} {store['name']} queue is live",
                "url": store["url"],
                "description": (
                    f"[Open Store]({store['url']})\n"
                    f"[Open Queue Page]({final_url})"
                ),
                "fields": [
                    {"name": "Region", "value": store["flag"], "inline": True},
                    {"name": "Store URL", "value": store["url"], "inline": False},
                ],
            }
        ],
    }

    requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)


def main():
    state = load_state()

    print("Watcher started...")
    print(f"Checking every {CHECK_INTERVAL_SECONDS} seconds")

    while True:
        for code, store in STORES.items():
            try:
                is_live, final_url = queue_is_live(store["url"])
                was_live = state[code]["was_live"]

                print(f"{code}: {is_live}")

                if is_live and not was_live:
                    send_discord_alert(store, final_url)
                    print(f"{code} ALERT SENT")

                state[code]["was_live"] = is_live
                state[code]["last_final_url"] = final_url

            except Exception as e:
                print(f"{code} error: {e}")

        save_state(state)
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
