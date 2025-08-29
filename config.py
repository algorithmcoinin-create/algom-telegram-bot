import os, json
from dotenv import load_dotenv

# For local runs; on Render, env vars are provided by the dashboard
load_dotenv()

# --- Required env vars ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_PIN = os.getenv("ADMIN_PIN", "6789")

# Firebase
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "")  # paste the FULL JSON here (as one line) in Render
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "")            # e.g. https://your-project-id-default-rtdb.firebaseio.com/

def get_firebase_creds_dict():
    """Return creds as a python dict (supports plain JSON or base64)."""
    if not FIREBASE_CREDENTIALS:
        return None
    try:
        return json.loads(FIREBASE_CREDENTIALS)
    except Exception:
        import base64
        try:
            return json.loads(base64.b64decode(FIREBASE_CREDENTIALS).decode("utf-8"))
        except Exception:
            return None
