import os
import json
from datetime import datetime

try:
    import sqlite3
except Exception:
    sqlite3 = None


def init_database(db_path, schema_path='schema.sql'):
    """Initialize the SQLite database with schema at db_path."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if sqlite3:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            # Try a few common locations for the schema file so callers don't
            # need to duplicate schema.sql across subfolders (e.g. web/).
            def _locate_schema(p):
                candidates = [p]
                candidates.append(os.path.join(os.path.dirname(__file__), p))
                candidates.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), p))
                candidates.append(os.path.join(os.getcwd(), p))
                for c in candidates:
                    try:
                        if c and os.path.exists(c):
                            return c
                    except Exception:
                        continue
                return None

            sp = _locate_schema(schema_path)
            if sp:
                with open(sp, 'r') as f:
                    schema = f.read()
                    cursor.executescript(schema)
            else:
                raise FileNotFoundError(f"schema not found: {schema_path}")
        except Exception:
            # If schema not found, create minimal tables
            try:
                cursor.execute('CREATE TABLE IF NOT EXISTS mango_state (id INTEGER PRIMARY KEY AUTOINCREMENT, hunger INTEGER, happiness INTEGER, cleanliness INTEGER, energy INTEGER, health INTEGER, age INTEGER, last_updated TEXT)')
                cursor.execute('CREATE TABLE IF NOT EXISTS scores (id INTEGER PRIMARY KEY AUTOINCREMENT, score INTEGER)')
            except Exception:
                pass
        conn.commit()
        conn.close()
    else:
        # JSON-file fallback for environments without sqlite3 (pygbag/WASM)
        json_path = db_path + '.json'
        if not os.path.exists(json_path):
            try:
                with open(json_path, 'w') as jf:
                    json.dump({'mango_state': [], 'scores': []}, jf)
            except Exception:
                pass


def save_state(db_path, mango_state):
    """Save Mango state dict into the database at db_path."""
    if sqlite3:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM mango_state")
            cursor.execute(
                """
                INSERT INTO mango_state
                (hunger, happiness, cleanliness, energy, health, age, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mango_state['hunger'],
                    mango_state['happiness'],
                    mango_state['cleanliness'],
                    mango_state['energy'],
                    mango_state['health'],
                    mango_state['age'],
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
    else:
        json_path = db_path + '.json'
        try:
            data = {'mango_state': [], 'scores': []}
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r') as jf:
                        data = json.load(jf)
                except Exception:
                    data = {'mango_state': [], 'scores': []}
            # append the new state as the latest
            entry = mango_state.copy()
            entry['last_updated'] = datetime.now().isoformat()
            data.setdefault('mango_state', [])
            data['mango_state'].append(entry)
            with open(json_path, 'w') as jf:
                json.dump(data, jf)
        except Exception:
            pass


def load_state(db_path):
    """Load Mango state from database at db_path, return dict or None."""
    if sqlite3:
        if not os.path.exists(db_path):
            return None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM mango_state ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            if result:
                return {
                    'hunger': result[1],
                    'happiness': result[2],
                    'cleanliness': result[3],
                    'energy': result[4],
                    'health': result[5],
                    'age': result[6],
                    'last_updated': result[7],
                }
        except Exception:
            return None
        return None
    else:
        json_path = db_path + '.json'
        if not os.path.exists(json_path):
            return None
        try:
            with open(json_path, 'r') as jf:
                data = json.load(jf)
            states = data.get('mango_state', [])
            if not states:
                return None
            last = states[-1]
            return last
        except Exception:
            return None

def save_score(db_path, score):
    """Save a score either in sqlite or JSON fallback."""
    if sqlite3:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO scores (score) VALUES (?)", (score,))
            conn.commit()
            conn.close()
        except Exception:
            pass
    else:
        json_path = db_path + '.json'
        try:
            data = {'mango_state': [], 'scores': []}
            if os.path.exists(json_path):
                with open(json_path, 'r') as jf:
                    data = json.load(jf)
            data.setdefault('scores', []).append({'score': int(score), 'ts': datetime.now().isoformat()})
            with open(json_path, 'w') as jf:
                json.dump(data, jf)
        except Exception:
            pass

def get_high_score(db_path):
    """Return the highest score from sqlite or JSON fallback."""
    if sqlite3:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(score) FROM scores")
            result = cursor.fetchone()
            conn.close()
            return result[0] if result and result[0] is not None else 0
        except Exception:
            return 0
    else:
        json_path = db_path + '.json'
        if not os.path.exists(json_path):
            return 0
        try:
            with open(json_path, 'r') as jf:
                data = json.load(jf)
            scores = data.get('scores', [])
            if not scores:
                return 0
            return max(int(s.get('score', 0)) for s in scores)
        except Exception:
            return 0
