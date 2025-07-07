import requests
import time
import os
from datetime import datetime, timezone
import pytz
from dotenv import load_dotenv

load_dotenv()

# Environment variables from Heroku config
LINKUP_USERNAME = os.getenv("LIBRELINKUP_EMAIL")
LINKUP_PASSWORD = os.getenv("LIBRELINKUP_PASSWORD")
LINKUP_COUNTRY = os.getenv("LIBRELINKUP_COUNTRY", "US")
NIGHTSCOUT_URL = os.getenv("NIGHTSCOUT_URL")
NIGHTSCOUT_SECRET = os.getenv("NIGHTSCOUT_API_SECRET")
TIMEZONE = os.getenv("TIMEZONE", "UTC")

API_URL = f"https://api.libreview.io/llu/v2"
LOGIN_URL = "https://api.libreview.io/llu/auth/login

session = requests.Session()

def login():
    print("[INFO] Logging in to LibreLinkUp...")
    payload = {
        "username": LINKUP_USERNAME,
        "password": LINKUP_PASSWORD
    }
    headers = {
        "product": "llu.android",
        "version": "4.7"
    }

    res = session.post(LOGIN_URL, json=payload, headers=headers)
    res.raise_for_status()
    data = res.json()
    token = data["data"]["authTicket"]["token"]
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    })
    print("[INFO] Login successful.")

def get_glucose():
    print("[INFO] Getting glucose data...")
    res = session.get(f"{API_URL}/glucose")
    res.raise_for_status()
    data = res.json()
    return data["data"]

def send_to_nightscout(glucose):
    print("[INFO] Sending glucose data to Nightscout...")
    entries = [{
        "type": "sgv",
        "date": int(datetime.now().timestamp() * 1000),
        "dateString": datetime.now().astimezone(pytz.timezone(TIMEZONE)).isoformat(),
        "sgv": glucose["Value"],
        "device": "LibreLinkUp",
        "direction": glucose.get("Trend", "Flat")
    }]
    res = requests.post(
        f"{NIGHTSCOUT_URL}/api/v1/entries.json",
        headers={"API-SECRET": NIGHTSCOUT_SECRET},
        json=entries
    )
    res.raise_for_status()
    print("[INFO] Successfully sent glucose to Nightscout.")

def main():
    login()
    last_timestamp = None

    while True:
        try:
            data = get_glucose()
            latest = data["glucoseMeasurement"]
            timestamp = latest["Timestamp"]

            if timestamp != last_timestamp:
                send_to_nightscout(latest)
                last_timestamp = timestamp
            else:
                print("[INFO] No new data yet.")

        except Exception as e:
            print(f"[ERROR] {e}")
            login()  # Re-auth on failure

        time.sleep(300)  # Wait 5 minutes

if __name__ == "__main__":
    main()
