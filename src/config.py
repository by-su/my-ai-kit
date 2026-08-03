import json
import os
from pathlib import Path

HOME = Path.home()
KIT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = HOME / ".agent-skills" / "store"
STATE_FILE = HOME / ".agent-skills" / "state.json"

def parse_val(val_str):
    val_str = val_str.strip()
    if val_str.lower() in ('true', 'yes'):
        return True
    if val_str.lower() in ('false', 'no'):
        return False
    if (val_str.startswith('"') and val_str.endswith('"')) or (val_str.startswith("'") and val_str.endswith("'")):
        return val_str[1:-1]
    return val_str

def parse_simple_yaml(filepath):
    """
    Lightweight, zero-dependency YAML parser for manifest.yaml structure.
    Falls back to PyYAML if installed.
    """
    try:
        import yaml
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        pass

    result = {}
    current_section = None
    current_list_item = None

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip() or line.strip().startswith('#'):
                continue

            indent = len(line) - len(line.lstrip())
            stripped = line.strip()

            if indent == 0 and stripped.endswith(':'):
                current_section = stripped[:-1].strip()
                result[current_section] = [] if current_section in ['core', 'optional'] else {}
                current_list_item = None
            elif indent == 2 and current_section in ['core', 'optional'] and stripped.startswith('- '):
                current_list_item = {}
                result[current_section].append(current_list_item)
                content = stripped[2:].strip()
                if ':' in content:
                    k, v = content.split(':', 1)
                    current_list_item[k.strip()] = parse_val(v)
            elif indent >= 4 and current_list_item is not None:
                if ':' in stripped:
                    k, v = stripped.split(':', 1)
                    current_list_item[k.strip()] = parse_val(v)
            elif indent >= 2 and isinstance(result.get(current_section), dict):
                if ':' in stripped:
                    k, v = stripped.split(':', 1)
                    result[current_section][k.strip()] = parse_val(v)

    return result

def load_manifest():
    manifest_path = KIT_DIR / "manifest.yaml"
    return parse_simple_yaml(manifest_path)

def load_lockfile():
    lockfile_path = KIT_DIR / "manifest.lock.json"
    if lockfile_path.exists():
        with open(lockfile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"version": "1.0", "skills": {}}

def save_lockfile(data):
    lockfile_path = KIT_DIR / "manifest.lock.json"
    with open(lockfile_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"enabled_optionals": [], "active_profile": "personal"}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def get_active_profile():
    state = load_state()
    return state.get("active_profile", "personal")

def set_active_profile(profile_name):
    state = load_state()
    state["active_profile"] = profile_name
    state.pop("profile_keywords", None)
    save_state(state)

def load_local_state(cwd=None):
    if cwd is None:
        cwd = Path.cwd()
    local_file = Path(cwd) / ".mykit.json"
    if local_file.exists():
        try:
            with open(local_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"enabled_optionals": []}

def save_local_state(state, cwd=None):
    if cwd is None:
        cwd = Path.cwd()
    local_file = Path(cwd) / ".mykit.json"
    with open(local_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


SETUP_KEYWORD_CATEGORIES = {
    "Frontend & Web": [
        "typescript", "javascript", "react", "next", "vue", "nuxt", "svelte", "sveltekit", "angular", "astro", "remix", "tailwind", "electron"
    ],
    "Backend & Server": [
        "node", "express", "nest", "fastify", "bun", "deno",
        "python", "django", "fastapi", "flask", "celery",
        "go", "gin", "fiber",
        "rust", "actix", "axum",
        "java", "kotlin", "springboot", "spring", "jpa", "ktor",
        "csharp", "dotnet", "unity",
        "php", "laravel", "symfony",
        "ruby", "rails",
        "c", "cpp"
    ],
    "Mobile": [
        "react-native", "swift", "swiftui", "ios", "android", "flutter", "dart"
    ],
    "Databases & ORMs": [
        "postgres", "mysql", "sqlite", "mongodb", "redis", "prisma", "drizzle", "typeorm", "sqlalchemy", "elasticsearch", "supabase", "firebase"
    ],
    "DevOps & Cloud": [
        "docker", "kubernetes", "terraform", "helm", "aws", "gcp", "azure", "cloudflare", "github-actions", "nginx"
    ],
    "AI & Data": [
        "langchain", "pytorch", "tensorflow", "openai", "huggingface"
    ],
}

SETUP_PROFILE_KEYWORDS = [kw for cat in SETUP_KEYWORD_CATEGORIES.values() for kw in cat]
