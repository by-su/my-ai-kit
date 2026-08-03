import os
import sys
import re
from pathlib import Path
from src.config import load_manifest, load_state, load_local_state
from src.symlink import resolve_skill_path

def extract_tokens(text):
    """Extracts normalized word tokens from markdown content."""
    clean_text = re.sub(r'```[\s\S]*?```', '', text)
    clean_text = re.sub(r'[^\w\s]', ' ', clean_text.lower())
    tokens = set(w for w in clean_text.split() if len(w) > 2)
    return tokens

def calculate_jaccard_similarity(set1, set2):
    """Calculates Jaccard similarity score between two token sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return (intersection / union) * 100

def get_dedupe_skill_items(manifest, include_all=False, cwd=None):
    if include_all:
        return manifest.get("core", []) + manifest.get("optional", [])

    state = load_state()
    local_state = load_local_state(cwd)
    global_enabled = set(state.get("enabled_optionals", []))
    local_enabled = set(local_state.get("enabled_optionals", []))
    disabled = set(state.get("disabled_optionals", []))

    items = list(manifest.get("core", []))
    for item in manifest.get("optional", []):
        name = item.get("name")
        is_default = item.get("default_enabled", False)
        if name in local_enabled or name in global_enabled or (is_default and name not in disabled):
            items.append(item)
    return items

def run_dedupe(threshold=40.0, focus_skill=None, include_all=False, cwd=None):
    manifest = load_manifest()
    all_skills = get_dedupe_skill_items(manifest, include_all=include_all, cwd=cwd)
    
    print(f"\033[1;36m🔍 Running mykit dedupe (Semantic Overlap Detector)...\033[0m")
    print(f"Similarity Threshold: {threshold}%\n")

    skill_tokens = {}

    for item in all_skills:
        skill_name = item.get("name")
        skill_path = resolve_skill_path(item)

        if not skill_path or not skill_path.exists():
            continue

        if skill_path.is_dir():
            sub_skills = list(skill_path.glob("*/SKILL.md")) + list(skill_path.glob("*.md"))
            for sub in sub_skills:
                sub_name = sub.parent.name if sub.name == "SKILL.md" else sub.stem
                try:
                    with open(sub, 'r', encoding='utf-8', errors='ignore') as f:
                        skill_tokens[f"{skill_name}/{sub_name}"] = extract_tokens(f.read())
                except Exception:
                    pass
        else:
            try:
                with open(skill_path, 'r', encoding='utf-8', errors='ignore') as f:
                    skill_tokens[skill_name] = extract_tokens(f.read())
            except Exception:
                pass

    scope_label = "total" if include_all else "active"
    print(f"Analyzing {len(skill_tokens)} {scope_label} skill documents for semantic overlaps...")
    
    names = list(skill_tokens.keys())
    overlaps = []

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            name1, name2 = names[i], names[j]
            tokens1, tokens2 = skill_tokens[name1], skill_tokens[name2]
            
            score = calculate_jaccard_similarity(tokens1, tokens2)
            if score >= threshold:
                overlaps.append((score, name1, name2))

    overlaps.sort(key=lambda x: x[0], reverse=True)

    if focus_skill:
        overlaps = [
            overlap for overlap in overlaps
            if overlap[1].split("/", 1)[0] == focus_skill or overlap[2].split("/", 1)[0] == focus_skill
        ]

    if not overlaps:
        if focus_skill:
            print(f"\033[1;32m🎉 No significant semantic overlaps found for '{focus_skill}'!\033[0m")
        else:
            print("\033[1;32m🎉 No significant semantic overlaps found among skills!\033[0m")
    else:
        if focus_skill:
            print(f"\033[1;33m⚠️ Found {len(overlaps)} potential overlapping pair(s) involving '{focus_skill}':\033[0m\n")
        else:
            print(f"\033[1;33m⚠️ Found {len(overlaps)} potential overlapping skill pair(s):\033[0m\n")
        for score, n1, n2 in overlaps[:15]:
            print(f"  • \033[1;35m[{score:.1f}% Similarity]\033[0m {n1} ↔ {n2}")

    return overlaps
