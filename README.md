# 🧰 my-ai-kit

**Antigravity, Claude Code, OpenAI Codex, Gemini CLI** 등 여러 AI 코딩 에이전트의 스킬(Skills), 커스텀 서브 에이전트(Subagents), MCP 설정, 명령어 자동 승인 규칙, 프로프트를 한 곳에서 중앙 관리하고 단 한 줄의 명령어(`mykit sync`)로 완벽하게 복구/동기화하는 **Multi-Agent Config & Skill Manager**입니다.

---

## 📌 핵심 기억할 사항 (Cheat Sheet)

### 1. 자주 쓰는 CLI 명령어
터미널 어디서나 실행할 수 있도록 `PATH`에 등록하여 사용합니다.

| 명령어 | 설명 |
| :--- | :--- |
| `mykit list` | 활성화된 스택 프로필, MCP 서버, 커스텀 서브 에이전트(`agents/*.md`), Core 및 Local 스킬 조회 |
| `mykit setup` | 초기 셋업 마법사로 profile 생성/선택, pruning 언어/스택, 전역 Optional 스킬, 선택한 팩의 pruning 여부, MCP 선택 |
| `mykit install <skill-name>` | **현재 작업 중인 프로젝트 디렉터리(`pwd`)** 내부로 Optional 스킬 설치 및 **자동 중복 스캔 훅(Auto-Dedupe Hook) 연동** |
| `mykit install <skill-name> --global` | Optional 스킬을 전역(Global) 스코프로 설치 및 **자동 중복 스캔 훅 연동** |
| `mykit remove <skill-name>` | 현재 작업 중인 프로젝트 디렉터리(`pwd`)에서 Optional 스킬 제거 |
| `mykit stats` | 시스템 전체 통계 대시보드 (스킬 감축률, 토큰 절약량, 에이전트 연결 현황) |
| `mykit env setup` | MCP API 키 및 시크릿 인터랙티브 자동 대화형 등록 마법사 |
| `mykit mcp` | 등록된 MCP 서버 활성화 상태 조회 및 토글 (`mykit mcp enable \| disable <mcp-name>`) |
| `mykit profile` | 현재 프로필/폴더 바인딩 조회, 수정, 삭제 (`mykit profile use <profile>`는 지금 있는 폴더만 그 프로필에 적용(이동 없음), `--global`을 붙이면 이 컴퓨터의 전역 기본 프로필을 전환, `--worktree`를 붙이면 git worktree를 만들어(또는 재사용해) 그 프로필을 바인딩, `mykit profile bind/unbind`로 다른 폴더 바인딩, `mykit profile edit`, `mykit profile remove <profile>`) |
| `mykit sessions` | 현재 살아있는 mykit 세션(pid, 폴더, 프로필) 목록 조회 — 같은 폴더에서 프로필을 바꾸기 전 다른 세션이 그 폴더를 쓰고 있는지 확인할 때 사용 |
| `mykit sync` | 활성 스킬만 lazy fetch한 뒤 스택 프로필, 안전 명령어, MCP, 서브 에이전트 동기화 |
| `mykit sync --all` | 비활성 Optional까지 포함해 모든 GitHub 스킬을 명시적으로 fetch 후 동기화 |
| `mykit prefetch <skill-name\|--all>` | Optional 스킬을 활성화하지 않고 미리 다운로드 |
| `mykit completion install` | Zsh / Bash 터미널 자동 완성(Tab Completion) 1초 등록 |
| `mykit update [skill-name] [--all]` | fetch된 GitHub 스킬 또는 지정 스킬을 최신 커밋으로 업데이트 및 Lockfile 갱신 |
| `mykit lint [--fix]` | 스킬 YAML 문법, 이름 중복 충돌 및 깨진 심볼릭 링크 자동 점검 (`--fix` 옵션으로 유령 링크 자동 정리) |
| `mykit dedupe [threshold] [--skill <name>] [--all]` | 활성 스킬 간 키워드/내용 겹침을 분석하여 유사 중복 스킬 탐지 (`--all`은 전체 등록 스킬 검사) |
| `mykit doctor` | 설정 파일 검증, 자동 승인 커맨드 목록, MCP 헬스체크 및 에이전트별 연결 상태 점검 |

---

## 🔄 스킬 설치 시 자동 중복 스캔 훅 (Post-Install Auto-Dedupe Hook)

새로운 스킬을 등록(`mykit install <skill-name>`)하면 동기화 완료 직후 **자동으로 `mykit dedupe` 훅이 작동**하여, 새로 추가된 스킬이 활성 스킬과 30% 이상 텍스트/지침이 겹치는지 실시간으로 스캔하고 알려줍니다.

[`manifest.yaml`](file:///Users/bysu/workspace/my-ai-kit/manifest.yaml) 설정:
```yaml
auto_dedupe_on_install: true  # <--- 스킬 설치 시 자동 중복 스캔 훅
```

---

## 🛡️ 안전 명령어 자동 승인 (Auto-Approve Safe Commands)

매번 터미널 명령어를 실행할 때마다 사람이 승인 버튼을 누르지 않아도 되도록, `manifest.yaml`의 `auto_approve_commands` 목록을 각 에이전트에 동기화합니다. 다만 에이전트마다 승인 메커니즘이 달라 동작 방식이 다릅니다:

- **Claude Code / Antigravity CLI**: 명령어별 allowlist를 지원하므로, 목록의 각 명령어가 `~/.claude/settings.json`(`Bash(git:*)` 패턴) 및 `~/.gemini/antigravity-cli/settings.json`(`command(git)` 패턴)의 `permissions.allow`에 실제로 등록됩니다.
- **Codex CLI**: 명령어 단위 allowlist 기능이 없어, 대신 `manifest.yaml`의 `global.codex.sandbox_mode`/`approval_policy` 값을 `~/.codex/config.toml`에 동기화해 승인 빈도 자체를 조절합니다(`approval_policy: "never"`로 바꾸면 프롬프트를 완전히 끌 수 있습니다).

---

## ⚙️ Claude Code 세션 기본 환경변수 (`claude_env_defaults`)

`manifest.yaml`의 `claude_env_defaults` 맵을 `mykit sync`/`mykit setup` 실행 시 `~/.claude/settings.json`의 `env`에 동기화합니다. 이미 값이 존재하는 키는 덮어쓰지 않고, 없는 키만 채워 넣습니다(사용자가 직접 바꾼 값은 항상 보존).

```yaml
claude_env_defaults:
  GATEGUARD_DISABLED: "1"  # ECC의 GateGuard fact-forcing 훅 기본 비활성화
```

- ECC 플러그인에 포함된 GateGuard 훅은 Edit/Write/Bash 전에 "먼저 조사부터 하라"고 강제하는 fact-forcing 게이트입니다.
- 자체 A/B 테스트(gated vs ungated, 함수 단위 채점, 게이트가 실제로 발동했는지 `~/.gateguard/state-*.json`으로 검증) 결과 현재 모델 기준으로는 품질 차이 없이 순수 지연만 발생해, 기본값으로 꺼두도록 설정했습니다.
- 다시 켜고 싶다면 `~/.claude/settings.json`의 `env.GATEGUARD_DISABLED` 값을 지우거나 다른 값으로 바꾸면 됩니다 — 이후 `mykit sync`를 다시 돌려도 그 값은 덮어써지지 않습니다.

---

## 📊 통계 대시보드 (`mykit stats`)

내 맥북의 전체 AI 스킬 절감율, 예상 토큰 절약량, 에이전트 연결 현황을 한눈에 시각화합니다.

```bash
mykit stats
```

---

## 🔑 MCP 시크릿 자동 등록 마법사 (`mykit env setup`)

터미널에서 대화형 마법사로 API 키를 안전하게 세팅할 수 있습니다.

```bash
mykit env setup
```

---

## ⌨️ 터미널 자동 완성 (Tab Completion)

터미널에서 `mykit <Tab>` 키를 누르면 모든 명령어와 스킬 이름이 **자동 완성**됩니다.

---

## 🤖 커스텀 서브 에이전트 (Custom Subagents) 동기화

`agents/` 폴더에 마크다운(`*.md`) 형태로 서브 에이전트 페르소나 및 전용 지침을 작성해 두면, `mykit sync` 한 줄로 **Claude Code, Antigravity, OpenAI Codex 에이전트 경로로 자동 배포**됩니다.

---

## ⚡ MCP 서버 선택적 관리 (`mykit mcp`)

스킬뿐만 아니라 MCP 서버도 개별적으로 켜고 끌 수 있습니다.

```bash
# 1. MCP 목록 및 상태 확인
mykit mcp

# 2. 특정 MCP 켜기
mykit mcp enable mysql

# 3. 특정 MCP 끄기
mykit mcp disable mysql
```

---

## ⚡ 프로필 (Profiles) 관리

개발 스택별로 필요한 스킬만 로드해 토큰 소비량을 줄일 수 있습니다. 두 가지 모드가 있습니다.

```bash
# 폴더 전용 (기본): 지금 있는 폴더만 그 프로필에 적용, 전역 기본값은 그대로
mykit profile use pm
mykit profile bind <profile-name> [path]   # 다른(지금 있지 않은) 폴더를 프로필에 붙이기
mykit profile unbind [path]

# 이 컴퓨터의 전역 기본 프로필 전환 (회사 PC vs 개인 PC처럼 통째로 하나만 쓸 때)
mykit profile use <profile-name> --global

mykit profile
mykit profile edit
mykit profile remove <profile-name>
```

`mykit profile edit`는 profile 생성/수정 및 스킬/MCP 셋업을 진행하며, `mykit profile remove`는 지정한 커스텀 profile을 삭제합니다.

### ⚠️ 같은 폴더에서 프로필을 동시에 여러 개 쓸 수 없는 이유

`.claude/skills` 같은 로컬 스킬 디렉터리는 **폴더 하나당 물리적으로 하나**뿐입니다. 그래서 같은 폴더에서 세션 A(general)와 세션 B(pm)를 동시에 띄워놓고 B에서 `mykit profile use pm`을 실행하면, A가 쓰던 스킬 심볼릭 링크가 그 자리에서 pm 것으로 교체되어 **A도 같이 영향을 받습니다.** `mykit profile bind`로 다른 경로를 미리 등록해둬도 두 세션이 실제로 같은 폴더(cwd)에서 돌아가는 이상 소용없습니다 — 바인딩은 매핑일 뿐, 세션이 어디서 도는지는 안 바꿔주기 때문입니다.

진짜로 동시에 다른 프로필을 쓰려면 각 세션이 **실제로 서로 다른 물리적 폴더**에서 돌아야 합니다. `--worktree` 플래그가 이 과정을 자동화합니다:

```bash
# git worktree를 자동 생성(또는 이미 있으면 재사용)하고 그 폴더를 profile에 바인딩
mykit profile use pm --worktree              # 기본 경로: ~/.worktrees/<repo-name>/pm
mykit profile use pm --worktree /my/path     # 경로 직접 지정

# 만든 뒤에는 안내대로 그 폴더로 이동해서 sync
cd ~/.worktrees/<repo-name>/pm && mykit sync
```

`--worktree`는 git 저장소에서만 동작하며(worktree는 git 기능이라 git이 아닌 폴더는 지원 불가), `--global`과는 함께 쓸 수 없습니다. `mykit profile use <profile>`을 플래그 없이 실행했는데 같은 폴더에서 다른 세션이 이미 감지되면, 그냥 경고만 하고 끝나는 게 아니라 **"대신 git worktree를 새로 만들어서 진행할까요? (y/N)"** 라고 직접 물어봅니다 — `y`를 누르면 즉시 worktree를 만들어 그쪽에 바인딩하고(현재 폴더는 건드리지 않음), `n`이나 그냥 엔터(비대화형 환경 포함)면 기존처럼 현재 폴더에 그대로 바인딩합니다. `mykit profile bind`나 `--worktree` 플래그 사용 시에는 (이미 격리된 경로를 다루는 흐름이라) 경고만 출력되고 계속 진행됩니다. 지금 살아있는 세션과 그 프로필을 확인하려면 `mykit sessions`를 사용하세요.

---

## 🚀 워크플로우 가이드

### 1. 특정 프로젝트 폴더에서 스킬 설치 및 사용하기 (Local Scope)
```bash
# 1. 내 프로젝트 폴더로 이동
cd ~/workspace/my-react-project

# 2. 이 프로젝트에서만 사용할 Optional 스킬 설치
mykit install prompt-architect

# -> 설치 완료 직후 자동 중복 스캔 훅 실행!
```

---

### 2. 새 컴퓨터에서 환경 1초 복구하기 (Bootstrap)
새 컴퓨터로 옮겼을 때 아래 스크립트 한 줄로 기존 세팅을 100% 동일하게 재현합니다:

```bash
./bootstrap.sh
```

기본 bootstrap/sync는 `default_enabled: true`이거나 직접 설치한 활성 스킬만 다운로드합니다. 비활성 Optional 스킬까지 모두 받아두려면 `mykit sync --all` 또는 `mykit prefetch --all`을 명시적으로 실행하세요.

`./bootstrap.sh`를 터미널에서 직접 실행하면 `mykit setup`이 열려 profile 생성/선택, pruning 언어/스택, 전역 Optional 스킬, 선택한 팩의 pruning 여부, MCP 서버를 선택합니다. 첫 setup은 profile을 반드시 하나 생성하고, 아무 언어도 미리 선택하지 않습니다. Pruning 질문은 `ecc-suite` 또는 `mengto-skills`를 전역 Optional로 선택했을 때만 표시됩니다. `↑/↓`로 이동하고 Space 또는 클릭으로 선택을 토글한 뒤 Enter로 다음 단계로 이동합니다. `b`로 이전 단계로 돌아가고, `q`/Esc로 취소합니다. 파이프/CI처럼 비대화형으로 실행될 때는 기존처럼 기본값으로 `mykit sync`만 실행합니다.

설정 저장 직후 `mykit setup`은 **mykit이 관리하는 콘텐츠와 겹치는 Claude Code 플러그인이 켜져 있는지도 확인**합니다. 예를 들어 `ecc@ecc` 마켓플레이스 플러그인(`affaan-m/ECC`)은 mykit의 `ecc-suite` 팩(`affaan-m/everything-claude-code`)과 같은 계열 콘텐츠를 profile 구분 없이 통째로 로드합니다 — 그래서 `pm` 같은 좁은 profile을 쓰고 있어도 이 플러그인이 켜져 있으면 관련 없는 `ecc:*` 스킬이 잔뜩 보이는 문제가 생깁니다(plugin은 mykit profile pruning의 통제 범위 밖이라 항상 전체가 로드됨). 이런 충돌이 감지되면 끌지 물어보고, `[Y/n]`에서 엔터만 눌러도 기본으로 비활성화합니다. `~/.claude/settings.json`의 `enabledPlugins`에 반영되며, 적용은 다음 세션부터입니다.

Bootstrap 안전 옵션:

```bash
./bootstrap.sh --dry-run
./bootstrap.sh --non-interactive
./bootstrap.sh --no-path
./bootstrap.sh --no-agent-instructions
```

Bootstrap이 수정할 수 있는 경로:

```text
~/.zshrc
~/.bashrc
~/.claude/CLAUDE.md
~/.gemini/antigravity-cli/AGENTS.md
~/.codex/instructions.md
~/.codex/AGENTS.md
~/.agent-skills/state.json
Claude/Gemini/Antigravity/Codex MCP config files
```

---

## 🔒 보안 및 버전 고정 (`manifest.lock.json`)
* 외부 GitHub 스킬은 기본 `auto_update: false`입니다. `manifest.lock.json`에 기록된 **Git Commit SHA** 버전으로 고정되어 설치되므로, 외부 수정으로 인한 오염을 방지할 수 있습니다.
* 비활성 Optional GitHub 스킬은 기본 `bootstrap` / `mykit sync`에서 clone하지 않습니다. 필요한 스킬은 `mykit install <skill-name>` 또는 `mykit prefetch <skill-name>`로 가져옵니다.
* 최신 upstream으로 올리려면 `mykit update <skill-name>` 또는 `mykit update --all`을 명시적으로 실행하세요.
