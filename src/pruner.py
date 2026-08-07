import shutil
from pathlib import Path
from src.config import load_manifest, load_state, SETUP_PROFILE_KEYWORDS

# Universal core developer utilities (keyword-based, used for SKILL pruning)
UNIVERSAL_UTILITIES = {
    'git', 'testing', 'security',
    'refactor', 'cleaner', 'verification', 'performance',
    'architecture', 'architect', 'quality', 'debug', 'skill-create',
    'instinct', 'status', 'loop', 'tdd', 'mcp', 'prompt',
    'docs', 'doc', 'readme', 'fix',
}


# Universal agents: always deployed regardless of active tech-stack profile.
# These provide value across ANY project (architecture, review, security, etc.)
UNIVERSAL_AGENTS = {
    # Orchestration & planning
    'architect', 'code-architect', 'chief-of-staff', 'planner',
    # Code quality & review
    'code-reviewer', 'code-explorer', 'code-simplifier', 'refactor-cleaner',
    'comment-analyzer', 'silent-failure-hunter',
    # Testing & reliability
    'e2e-runner', 'tdd-guide', 'pr-test-analyzer', 'build-error-resolver',
    # Security & performance
    'security-reviewer', 'performance-optimizer',
    # Docs & specs
    'doc-updater', 'docs-lookup', 'spec-miner',
    # AI agents
    'agent-evaluator', 'loop-operator',
    # Infrastructure & DB
    'database-reviewer', 'network-architect', 'network-config-reviewer', 'homelab-architect',
    # Accessibility & design
    'a11y-architect', 'type-design-analyzer', 'seo-specialist',
    # Conversation & analysis
    'conversation-analyzer',
}


# Wizard shows a single "design" checkbox; selecting it must also pull in
# "ui"-named skills (ui-demo, motion-ui, glass-dark-ui, ...) since those
# don't contain the literal substring "design". Expansion happens only at
# match time (get_profile_keywords) — the raw stored include list keeps
# just "design", so profile summaries/lists still show one clean entry.
ROLE_KEYWORD_EXPANSIONS = {
    "design": ["design", "ui"],
    "planning": ["planning", "plan"],
}

# Keywords longer than 3 chars that still need exact-token matching instead
# of raw substring matching, because they collide with unrelated words that
# happen to start with the same letters (e.g. "product" inside
# "production-audit", "plan" inside "plankton-code-quality"). Global
# substring matching is relied upon elsewhere (e.g. "next" matching
# "nextjs-turbopack", "spring" matching "springboot-patterns"), so this is a
# targeted exception rather than a blanket behavior change.
TOKEN_EXACT_KEYWORDS = {"product", "plan"}

def _expand_role_keywords(keywords):
    expanded = list(keywords)
    for kw in keywords:
        for extra in ROLE_KEYWORD_EXPANSIONS.get(kw, []):
            if extra not in expanded:
                expanded.append(extra)
    return expanded

def slugify_profile(profile_name):
    return profile_name.replace(":", "-").replace("/", "-")

# Profile is the top-level unit: ~/.agent-skills/store/profiles/<profile>/<pack>/
PROFILES_STORE_BASE = Path("~/.agent-skills/store/profiles").expanduser()

def profile_pack_dir(profile_name, pack_key):
    return PROFILES_STORE_BASE / slugify_profile(profile_name) / pack_key

def get_profile_enable_optionals(profile_name):
    state = load_state()
    if profile_name.startswith("custom:"):
        custom_name = profile_name.split(":", 1)[1]
        return state.get("custom_profiles", {}).get(custom_name, {}).get("enable_optionals", [])
    manifest = load_manifest()
    return manifest.get("profiles", {}).get(profile_name, {}).get("enable_optionals", [])

def get_profile_keywords(profile_name):
    state = load_state()
    keywords = None
    if profile_name.startswith("custom:"):
        custom_name = profile_name.split(":", 1)[1]
        custom_profiles = state.get("custom_profiles", {})
        if custom_name in custom_profiles:
            keywords = custom_profiles[custom_name].get("include", [])
    if keywords is None and profile_name.startswith("custom:") and "profile_keywords" in state:
        keywords = state.get("profile_keywords", [])
    if keywords is None:
        manifest = load_manifest()
        profiles = manifest.get("profiles", {})
        prof = profiles.get(profile_name, profiles.get("personal", {}))
        keywords = prof.get("include", [])
    return _expand_role_keywords(keywords)

def is_skill_relevant(skill_name, profile_keywords):
    if "*" in profile_keywords:
        return True

    lower_name = skill_name.lower()
    parts = lower_name.replace('-', ' ').replace('_', ' ').split()
    
    # 1. Exact or keyword match against active stack profile
    for kw in profile_keywords:
        kw_lower = kw.lower()
        if len(kw_lower) <= 3 or kw_lower in TOKEN_EXACT_KEYWORDS:
            if kw_lower in parts:
                return True
        elif kw_lower in lower_name:
            return True

    # 2. Match against universal developer utilities
    for util in UNIVERSAL_UTILITIES:
        if len(util) <= 3 or util in TOKEN_EXACT_KEYWORDS:
            if util in parts:
                return True
        elif util in lower_name:
            return True
            
    return False

TECH_ALIAS_MAP = {
    'nextjs': 'next',
    'next.js': 'next',
    'nodejs': 'node',
    'node.js': 'node',
    'vuejs': 'vue',
    'vue.js': 'vue',
    'nuxtjs': 'nuxt',
    'nuxt.js': 'nuxt',
    'nestjs': 'nest',
    'nest.js': 'nest',
    'fastifyjs': 'fastify',
    'fastify.js': 'fastify',
    'sveltejs': 'svelte',
    'svelte.js': 'svelte',
    'angularjs': 'angular',
    'angular.js': 'angular',
    'golang': 'go',
    'reactnative': 'react-native',
    'react-native': 'react-native',
    'k8s': 'kubernetes',
    'postgresql': 'postgres',
    'mongo': 'mongodb',
    'springboot': 'springboot',
    'spring-boot': 'springboot',
    'fastapi': 'fastapi',
    'fast-api': 'fastapi',
}

KNOWN_TECH_STACK_KEYWORDS = set(SETUP_PROFILE_KEYWORDS).union(TECH_ALIAS_MAP.keys())


def _extract_tech_keywords_from_name(name):
    clean_str = name.lower().replace('_', ' ')
    words = clean_str.replace('-', ' ').split()
    found = set()

    # 1. Single token matching with alias resolution
    for word in words:
        std = TECH_ALIAS_MAP.get(word, word)
        if std in KNOWN_TECH_STACK_KEYWORDS or word in KNOWN_TECH_STACK_KEYWORDS:
            found.add(std)
            found.add(word)

    # 2. 2-gram matching for compound tech stacks (e.g. 'react native', 'spring boot', 'github actions')
    for i in range(len(words) - 1):
        bigram_space = f"{words[i]} {words[i+1]}"
        bigram_hyphen = f"{words[i]}-{words[i+1]}"
        bigram_concat = f"{words[i]}{words[i+1]}"

        for bg in (bigram_space, bigram_hyphen, bigram_concat):
            std = TECH_ALIAS_MAP.get(bg, bg)
            if std in KNOWN_TECH_STACK_KEYWORDS or bg in KNOWN_TECH_STACK_KEYWORDS:
                found.add(std)
                found.add(bg)

    return found


def is_agent_profile_relevant(agent_name, profile_keywords):
    """
    Dynamic profile match for agents:
    - If agent name does NOT target a specific tech stack (e.g. 'spec-writer', 'architect', 'evaluator'),
      it is treated as a general-purpose agent and is ALWAYS included.
    - If agent name specifically targets one or more tech stacks (e.g. 'django-expert', 'nextjs-turbopack-specialist'),
      it is included ONLY if the user's active profile includes at least one of those tech stacks.
    """
    if "*" in profile_keywords:
        return True

    tech_stacks_in_agent = _extract_tech_keywords_from_name(agent_name)

    # If agent is not tied to any specific tech stack, it is a general agent -> Always include!
    if not tech_stacks_in_agent:
        return True

    # If agent targets specific tech stack(s), check if user enabled at least one
    profile_lower = set()
    for kw in profile_keywords:
        kw_l = kw.lower()
        profile_lower.add(kw_l)
        profile_lower.add(TECH_ALIAS_MAP.get(kw_l, kw_l))

    return bool(tech_stacks_in_agent.intersection(profile_lower))

def prune_skills_for_profile(ecc_base_dir, target_dir, profile_name="personal"):
    ecc_base = Path(ecc_base_dir).expanduser()
    target_dir = Path(target_dir).expanduser()
    
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    keywords = get_profile_keywords(profile_name)
    included = []
    excluded = []
    
    # 1. Prune skills directory
    skills_dir = ecc_base / "skills"
    if skills_dir.exists():
        for item in skills_dir.iterdir():
            if item.is_dir():
                if is_skill_relevant(item.name, keywords):
                    dest = target_dir / item.name
                    shutil.copytree(item, dest)
                    included.append(item.name)
                else:
                    excluded.append(item.name)
                    
    # 2. Filter ECC Custom Commands by profile relevance
    commands_dir = ecc_base / "commands"
    if commands_dir.exists():
        for cmd_file in commands_dir.glob("*.md"):
            cmd_name = cmd_file.stem
            if is_skill_relevant(cmd_name, keywords):
                cmd_dest_dir = target_dir / cmd_name
                cmd_dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(cmd_file, cmd_dest_dir / "SKILL.md")
                included.append(f"command:{cmd_name}")
            else:
                excluded.append(f"command:{cmd_name}")

    return included, excluded

def prune_mengto_skills_for_profile(mengto_base_dir, target_dir, profile_name="personal"):
    mengto_base = Path(mengto_base_dir).expanduser()
    target_dir = Path(target_dir).expanduser()
    
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    keywords = get_profile_keywords(profile_name)
    included = []
    excluded = []

    ag_dir = mengto_base / "agent-skills"
    if ag_dir.exists():
        for category in ag_dir.iterdir():
            if category.is_dir():
                for skill_folder in category.iterdir():
                    if skill_folder.is_dir():
                        # Include UI, Web Design, and Writing/Codex categories always
                        if is_skill_relevant(skill_folder.name, keywords) or category.name in ("ui", "web-design", "codex", "media"):
                            dest = target_dir / skill_folder.name
                            shutil.copytree(skill_folder, dest)
                            included.append(skill_folder.name)
                        else:
                            excluded.append(skill_folder.name)

    return included, excluded

def prune_pack_agents_for_profile(agents_src_dir, target_dir, profile_name="personal"):
    """
    Filters agent .md files from a skill pack's agents/ directory.
    Inclusion logic (OR):
      1. Agent stem is in UNIVERSAL_AGENTS -> always included regardless of profile
      2. Agent name matches active profile keywords via is_skill_relevant()
    """
    src = Path(agents_src_dir).expanduser()
    target = Path(target_dir).expanduser()

    if not src.exists():
        return [], []

    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    keywords = get_profile_keywords(profile_name)
    included = []
    excluded = []

    for agent_file in sorted(src.glob("*.md")):
        stem = agent_file.stem
        if stem in UNIVERSAL_AGENTS or is_agent_profile_relevant(stem, keywords):
            shutil.copy2(agent_file, target / agent_file.name)
            included.append(stem)
        else:
            excluded.append(stem)

    return included, excluded
