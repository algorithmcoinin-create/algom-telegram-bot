import os, json
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_PIN = os.getenv("ADMIN_PIN", "6789")

# Firebase
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "")

def get_firebase_creds_dict():
    if not FIREBASE_CREDENTIALS:
        return None
    try:
        return json.loads(FIREBASE_CREDENTIALS)
    except Exception:
        # allow base64-encoded or escaped JSON if needed later
        import base64
        try:
            return json.loads(base64.b64decode(FIREBASE_CREDENTIALS).decode("utf-8"))
        except Exception:
            return None
