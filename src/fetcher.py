import subprocess
from pathlib import Path
from src.config import CACHE_DIR, load_lockfile, save_lockfile

def fetch_skill_repo(name, url, commit_sha=None, auto_update=False):
    fetched_dir = CACHE_DIR / "fetched" / name
    fetched_dir.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if not fetched_dir.exists():
            print(f"📥 Cloning remote skill '{name}' from {url}...")
            cmd = ["git", "clone", "--depth", "1", url, str(fetched_dir)]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        elif auto_update:
            print(f"🔄 Auto-updating '{name}' to latest commit...")
            subprocess.run(["git", "-C", str(fetched_dir), "pull", "--depth", "1"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(["git", "-C", str(fetched_dir), "fetch", "--depth", "1"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if not auto_update and commit_sha:
            subprocess.run(["git", "-C", str(fetched_dir), "checkout", commit_sha], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        res = subprocess.run(["git", "-C", str(fetched_dir), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        current_sha = res.stdout.strip()
        
        lockfile = load_lockfile()
        lockfile.setdefault("skills", {})[name] = {
            "url": url,
            "commit": current_sha
        }
        save_lockfile(lockfile)
        return current_sha
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Failed to fetch git repository for '{name}' ({url}). Please check if the URL exists or requires authentication.")
        return None

def update_skill_repo(name, url):
    fetched_dir = CACHE_DIR / "fetched" / name
    fetched_dir.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🔄 Updating '{name}' to latest commit from {url}...")
    try:
        if not fetched_dir.exists():
            cmd = ["git", "clone", "--depth", "1", url, str(fetched_dir)]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        else:
            subprocess.run(["git", "-C", str(fetched_dir), "fetch", "origin"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "-C", str(fetched_dir), "pull", "--rebase"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        res = subprocess.run(["git", "-C", str(fetched_dir), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        current_sha = res.stdout.strip()

        lockfile = load_lockfile()
        lockfile.setdefault("skills", {})[name] = {
            "url": url,
            "commit": current_sha
        }
        save_lockfile(lockfile)
        
        print(f"✅ Updated '{name}' lockfile to commit: {current_sha[:8]}")
        return current_sha
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Failed to update '{name}' ({url}).")
        return None
