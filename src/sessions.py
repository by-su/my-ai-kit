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


def record_session_start(session_id: str, pid: int, cwd: str) -> None:
    sessions = load_sessions()
    resolved_cwd = str(Path(cwd).resolve())
    sessions[session_id] = {
        "pid": pid,
        "cwd": resolved_cwd,
        "profile": get_active_profile(resolved_cwd),
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


def get_sessions_for_path(path) -> dict:
    """Active sessions whose recorded cwd overlaps with `path` (same dir, or one is an ancestor of the other)."""
    target = Path(path).resolve()
    matches = {}
    for session_id, info in list_active_sessions().items():
        cwd = info.get("cwd")
        if not cwd:
            continue
        session_path = Path(cwd).resolve()
        if session_path == target or session_path in target.parents or target in session_path.parents:
            matches[session_id] = info
    return matches
