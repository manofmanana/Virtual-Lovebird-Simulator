"""Saving and loading Mango's state and Flappy Mango scores.

On the desktop everything lives in a SQLite database (see schema.sql).
In the browser, files written by the game vanish when the page reloads, so
the same data is kept in the browser's localStorage instead.
"""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from config import IS_WEB

STATE_FIELDS = ("hunger", "happiness", "cleanliness", "energy", "health", "age", "last_updated")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


# ---------- Browser (localStorage) ----------

def _local_storage():
    import platform  # pygbag exposes the browser's window object here
    return platform.window.localStorage


def _web_get(key, default=None):
    try:
        raw = _local_storage().getItem(key)
        return json.loads(raw) if raw else default
    except Exception:
        return default


def _web_set(key, value):
    try:
        _local_storage().setItem(key, json.dumps(value))
    except Exception as e:
        print(f"Could not save {key} to localStorage: {e}")


@contextmanager
def _connect(db_path):
    """A connection that commits on success and is always closed (so Windows can delete the file)."""
    conn = sqlite3.connect(db_path)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


# ---------- Public API ----------

def init_database(db_path):
    """Create the database file and tables if they don't exist yet."""
    if IS_WEB:
        return
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    with open(SCHEMA_PATH, encoding="utf-8") as f, _connect(db_path) as conn:
        conn.executescript(f.read())


def save_state(db_path, mango_state):
    """Save Mango's stats. last_updated is stored as-is: it marks Mango's last birthday."""
    row = {field: mango_state.get(field) for field in STATE_FIELDS}
    row["last_updated"] = row["last_updated"] or datetime.now().isoformat()
    if IS_WEB:
        _web_set("mango_state", row)
        return
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM mango_state")
        conn.execute(
            f"INSERT INTO mango_state ({', '.join(STATE_FIELDS)}) VALUES ({', '.join('?' * len(STATE_FIELDS))})",
            tuple(row.values()),
        )


def load_state(db_path):
    """Return Mango's saved stats as a dict, or None if there's no save yet."""
    if IS_WEB:
        return _web_get("mango_state")
    if not os.path.exists(db_path):
        return None
    with _connect(db_path) as conn:
        row = conn.execute(
            f"SELECT {', '.join(STATE_FIELDS)} FROM mango_state ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return dict(zip(STATE_FIELDS, row)) if row else None


def save_score(db_path, score):
    """Record a Flappy Mango score."""
    if IS_WEB:
        _web_set("high_score", max(score, get_high_score(db_path)))
        return
    with _connect(db_path) as conn:
        conn.execute("INSERT INTO scores (score) VALUES (?)", (int(score),))


def get_high_score(db_path):
    """Return the best Flappy Mango score so far (0 if none)."""
    if IS_WEB:
        return int(_web_get("high_score", 0) or 0)
    if not os.path.exists(db_path):
        return 0
    with _connect(db_path) as conn:
        best = conn.execute("SELECT MAX(score) FROM scores").fetchone()[0]
    return best or 0


def load_settings(settings_path):
    """Return saved volume settings, or {} if none."""
    if IS_WEB:
        return _web_get("settings", {})
    try:
        with open(settings_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_settings(settings_path, settings):
    if IS_WEB:
        _web_set("settings", settings)
        return
    os.makedirs(os.path.dirname(settings_path) or ".", exist_ok=True)
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f)
