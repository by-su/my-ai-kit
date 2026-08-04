import json
import os
import time
from pathlib import Path
from src.config import HOME, get_active_profile

SESSIONS_FILE = HOME / ".agent-skills" / "sessions.json"


def load_sessions() -> dict:
    if SESSIONS_FILE.exists():
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_sessions(sessions: dict) -> None:
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)


def is_pid_alive(pid) -> bool:
    if not isinstance(pid, int):
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False
    return True


def record_session_start(session_id: str, pid: int) -> None:
    sessions = load_sessions()
    sessions[session_id] = {
        "pid": pid,
        "profile": get_active_profile(),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    save_sessions(sessions)


def record_session_end(session_id: str) -> None:
    sessions = load_sessions()
    if session_id in sessions:
        sessions.pop(session_id)
        save_sessions(sessions)


def list_active_sessions() -> dict:
    sessions = load_sessions()
    alive = {sid: info for sid, info in sessions.items() if is_pid_alive(info.get("pid"))}
    if alive != sessions:
        save_sessions(alive)
    return alive
