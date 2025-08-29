import time
from typing import Optional, Dict, Any
from firebase_admin import credentials, initialize_app, db
from config import get_firebase_creds_dict, FIREBASE_DB_URL

_app = None

def init_firebase():
    global _app
    if _app:
        return _app
    creds_dict = get_firebase_creds_dict()
    if not creds_dict:
        raise RuntimeError("FIREBASE_CREDENTIALS is missing or invalid")
    if not FIREBASE_DB_URL:
        raise RuntimeError("FIREBASE_DB_URL is not set")
    cred = credentials.Certificate(creds_dict)
    _app = initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})
    return _app

# Paths
USERS = "users"
EVENTS = "events"

def _user_ref(user_id):
    return db.reference(f"{USERS}/{user_id}")

def _events_ref():
    return db.reference(EVENTS)

# --- User helpers ---

def upsert_user(user: Dict[str, Any]):
    init_firebase()
    ref = _user_ref(user["user_id"])
    existing = ref.get() or {}
    existing.update({
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "username": user.get("username"),
        "language_code": user.get("language_code", "en"),
    })
    if "created_at" not in existing:
        existing["created_at"] = int(time.time())
        if user.get("referrer"):
            existing["referrer"] = int(user["referrer"])
    ref.set(existing)

def set_login(user_id: int, email: str, wallet: Optional[str]):
    init_firebase()
    _user_ref(user_id).update({"email": email, "wallet": wallet})

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    init_firebase()
    return _user_ref(user_id).get()

def add_balance(user_id: int, amount: int, evtype: str):
    init_firebase()
    ref = _user_ref(user_id)
    u = ref.get() or {}
    u["balance"] = int(u.get("balance", 0)) + int(amount)
    ref.update({"balance": u["balance"]})
    _events_ref().push({
        "user_id": user_id,
        "type": evtype,
        "value": int(amount),
        "ts": int(time.time()),
    })

def can_claim_daily(user_id: int) -> bool:
    init_firebase()
    u = _user_ref(user_id).get() or {}
    last = int(u.get("last_daily", 0) or 0)
    return int(time.time()) - last >= 24*3600

def set_daily_claimed(user_id: int):
    init_firebase()
    _user_ref(user_id).update({"last_daily": int(time.time())})

def tap_increment(user_id: int, goal: int):
    init_firebase()
    ref = _user_ref(user_id)
    u = ref.get() or {}
    prog = int(u.get("tap_progress", 0)) + 1
    done = prog >= goal
    if done:
        ref.update({"tap_progress": 0, "total_taps": int(u.get("total_taps", 0)) + 1})
        return goal, True
    else:
        ref.update({"tap_progress": prog, "total_taps": int(u.get("total_taps", 0)) + 1})
        return prog, False
