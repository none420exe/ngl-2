import requests
import json
import time
import random
import uuid
import os
import datetime
import logging
import sys

sys.stdout.reconfigure(encoding='utf-8')

# ========================= CONFIGURATION =========================
USERNAME = "nanou62208"
TARGET_TIME = "20:00"          # ← CHANGE THIS (24h format) Example: "20:00" for 8 PM Tunis time

API_URL = "https://ngl.link/api/submit"
COUNTER_FILE = "counter.json"
STOP_FILE = "stop.txt"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
]
# ================================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_counter():
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return int(data.get('counter', 1)), data.get('last_updated')
        except:
            pass
    return 1, None


def save_counter(counter):
    try:
        with open(COUNTER_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'counter': counter,
                'last_updated': datetime.datetime.now().isoformat()
            }, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save counter: {e}")


def should_stop():
    return os.path.exists(STOP_FILE)


def already_sent_today(last_updated):
    """Check if we already sent today to avoid duplicates on restart"""
    if not last_updated:
        return False
    try:
        last_date = datetime.datetime.fromisoformat(last_updated).date()
        today = datetime.datetime.now().date()
        return last_date == today
    except:
        return False


def send_message(counter):
    if should_stop():
        logger.info("🛑 Stop file detected. Shutting down.")
        return False

    message = f"Day {counter} of asking you out ❤️"
    device_id = str(uuid.uuid4())

    payload = {
        "username": USERNAME,
        "question": message,
        "deviceId": device_id
    }

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "https://ngl.link",
        "Referer": f"https://ngl.link/{USERNAME}"
    }

    try:
        time.sleep(random.uniform(3, 8))
        response = requests.post(API_URL, json=payload, headers=headers, timeout=20)

        if response.status_code in (200, 201, 204):
            logger.info(f"✅ SUCCESS | Day {counter} sent")
            return True
        else:
            logger.error(f"❌ Failed | Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


def main():
    logger.info("="*60)
    logger.info("🚀 NGL Daily Bot Started")
    logger.info("="*60)

    counter, last_updated = load_counter()

    # Smart logic to avoid duplicate sends on restart
    if already_sent_today(last_updated):
        logger.info(f"📌 Already sent Day {counter-1} today. Waiting for tomorrow.")
    else:
        logger.info(f"📤 Sending Day {counter} now...")
        if send_message(counter):
            save_counter(counter + 1)
            counter += 1

    while True:
        if should_stop():
            break

        sleep_seconds = calculate_sleep_seconds()
        time.sleep(sleep_seconds)

        if send_message(counter):
            save_counter(counter + 1)
            counter += 1


def calculate_sleep_seconds():
    now = datetime.datetime.now()
    target = datetime.datetime.combine(now.date(), datetime.time.fromisoformat(TARGET_TIME))
    
    if now >= target:
        target += datetime.timedelta(days=1)
    
    seconds = int((target - now).total_seconds())
    logger.info(f"⏰ Next message scheduled at {target.strftime('%Y-%m-%d %H:%M')}")
    return seconds


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")