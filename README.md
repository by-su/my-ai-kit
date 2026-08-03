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
| `mykit profile` | 현재 프로필 조회, 전환, 수정, 삭제 (`mykit profile use <profile>`, `mykit profile edit`, `mykit profile remove <profile>`) |
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

매번 터미널 명령어를 실행할 때마다 사람이 승인 버튼을 누르지 않아도 되도록, **안전한 읽기/조회/빌드/테스트 명령어**를 모든 에이전트(Claude Code, Antigravity, Gemini, Codex)에 자동 승인으로 일괄 등록합니다.

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

회사 PC와 개인 PC의 개발 스택이 다르거나 270+ 스킬 전체를 전부 로드해야 할 때 프로필 한 줄로 유연하게 전환할 수 있습니다.

```bash
mykit profile
mykit profile edit
mykit profile remove <profile-name>
```

`mykit profile edit`는 profile 생성/수정 및 스킬/MCP 셋업을 진행하며, `mykit profile remove`는 지정한 커스텀 profile을 삭제합니다.

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
