# ⚡ my-ai-kit 퀵 스타트 가이드 (Quick Start Guide)

**my-ai-kit**은 Antigravity, Claude Code, OpenAI Codex, Gemini CLI 등 여러 AI 에이전트의 **스킬(Skills), MCP 서버, 커스텀 서브 에이전트(Subagents), 안전 커맨드 승인 규칙**을 한곳에서 중앙 관리하고 단 한 줄로 동기화하는 멀티 에이전트 설정 관리자입니다.

---

## 🚀 1. 3초 원클릭 초기화 (`./bootstrap.sh`)

새로운 컴퓨터나 터미널 환경에서 아래 명령어를 실행하면 전체 AI 환경 구축이 끝납니다:

```bash
# 1. 1-Line 초기화 실행
./bootstrap.sh

# 2. 터미널 갱신
source ~/.zshrc
```

### ⚙️ `./bootstrap.sh`가 내부에서 처리하는 작업
* **`bin/mykit` 실행 권한 자동 부여**: `chmod +x` 실행
* **터미널 `PATH` 자동 등록**: `~/.zshrc` 및 `~/.bashrc`에 `mykit` 실행 경로 자동 연결
* **초기 선택 마법사 실행**: 터미널에서 직접 실행하면 profile 생성/선택, pruning 언어/스택, 전역 Optional 스킬, 선택한 팩의 pruning 여부, MCP 선택
* **충돌하는 Claude Code 플러그인 확인**: mykit이 관리하는 팩과 겹치는 콘텐츠를 profile 구분 없이 통째로 로드하는 플러그인(예: `ecc@ecc`)이 켜져 있으면 끌지 물어봄 (아래 설명 참고)
* **활성 GitHub 스킬 lazy 다운로드**: 기본 활성 스킬만 다운로드하고 비활성 Optional은 필요할 때 가져옴
* **재현 가능한 기본 설치**: 외부 GitHub 스킬은 기본적으로 lockfile commit을 사용하고 자동 업데이트하지 않음
* **전체 에이전트 동기화 (`mykit sync`)**:
  - 6개 활성 MCP 서버 4개 에이전트에 자동 주입
  - 21개 안전 명령어 자동 승인 규칙 일괄 배포
  - 내 기술 스택(TS/JS, React, Python, Java, SpringBoot 등) 맞춤 80% 스킬 토큰 다이어트
  - 커스텀 서브 에이전트(`agents/*.md`) 4개 에이전트에 자동 심볼릭 링크 연결

### ⚠️ 왜 "충돌하는 플러그인" 체크가 필요한가

`pm` 같은 좁은 profile을 쓰는데도 `mykit list`/스킬 목록에 관련 없는 `ecc:video-editing`, `ecc:videodb` 같은 스킬이 잔뜩 "locked by plugin"으로 떠 있는 문제가 실제로 있었습니다. 원인은 mykit이 아니라 **Claude Code 마켓플레이스 플러그인**이었습니다: `ecc@ecc` 플러그인(`github.com/affaan-m/ECC`)이 mykit의 `ecc-suite` 팩(`github.com/affaan-m/everything-claude-code`, 같은 제작자)과 사실상 같은 콘텐츠를 담고 있는데, 플러그인은 profile 개념이 없어서 **켜져 있으면 무조건 전체를 로드**합니다. `mykit profile use`로 아무리 프로필을 바꿔도 이 플러그인 스킬은 그대로 남습니다 — mykit의 pruning이 관여할 수 있는 대상이 아니기 때문입니다.

그래서 `mykit setup` 마지막 단계에서 이런 known conflict를 감지하면 끌지 물어보게 만들었습니다. 직접 다시 켜고 싶다면 `/plugin`으로 관리하거나 `~/.claude/settings.json`의 `enabledPlugins`에서 값을 `true`로 되돌리면 됩니다.

---

## 💻 2. 핵심 명령어 치트시트 (Cheat Sheet)

| 명령어 | 설명 | 비고 |
| :--- | :--- | :--- |
| `mykit list` | 현재 스택 프로필, MCP, 서브 에이전트, 스킬 목록 상태 조회 | 현황 확인 |
| `mykit setup` | profile 생성/선택, pruning 언어/스택, 전역 Optional 스킬, 선택한 팩의 pruning 여부, MCP 선택 | 초기 설정 |
| `mykit sync` | 활성 스킬만 lazy fetch 후 전체 에이전트(Claude, Antigravity, Codex) 동기화 | 핵심 배포 |
| `mykit sync --all` | 비활성 Optional까지 모두 fetch 후 동기화 | 전체 사전 다운로드 |
| `mykit prefetch <skill>` | 스킬을 활성화하지 않고 미리 다운로드 | 선택 다운로드 |
| `mykit reset` | 찌꺼기 심볼릭 링크 및 구버전 설정 100% 클린 리셋 | 초기화 |
| `mykit stats` | 시스템 통계 대시보드 (스킬 감축률, 토큰 절약량, 에이전트 연결 현황) | 시각화 |
| `mykit env setup` | MCP API 키 및 시크릿 인터랙티브 대화형 등록 마법사 | 키 세팅 |
| `mykit profile` | 개발 프로필 조회, 전환, 수정 (`mykit profile use <profile>`, `--worktree`로 git worktree 자동 생성+바인딩, `mykit profile edit`) | 프로필 스위칭 |
| `mykit sessions` | 현재 살아있는 mykit 세션(pid, 폴더, 프로필) 목록 조회 | 세션 확인 |
| `mykit mcp` | MCP 서버 켜기/끄기 토글 (`mykit mcp enable \| disable <mcp-name>`) | MCP 관리 |
| `mykit doctor` | MCP 헬스체크, 시크릿 키 검증, 에이전트 연결 상태 점검 | 진단 |
| `mykit completion install` | Zsh / Bash 터미널 자동 완성(Tab Completion) 1초 등록 | 편의 기능 |
| `mykit install <skill>` | 현재 작업 중인 프로젝트 디렉터리(`pwd`)로 스킬 설치 | 프로젝트 로컬 |
| `mykit lint [--fix]` | 스킬 YAML 문법, 이름 중복 충돌 및 깨진 링크 자동 검사 | 검증 |
| `mykit dedupe` | 스킬 간 텍스트/내용 겹침을 분석하여 유사 중복 탐지 | 중복 점검 |

Bootstrap 옵션:

```bash
./bootstrap.sh --dry-run
./bootstrap.sh --non-interactive
./bootstrap.sh --no-path
./bootstrap.sh --no-agent-instructions
```

---

## 🔑 3. MCP API 키 등록하기 (`mykit env setup`)

터미널에서 대화형 마법사로 안전하게 API 키를 등록합니다:

```bash
mykit env setup
```

* `GITHUB_TOKEN`, `BRAVE_API_KEY` 등을 묻는 창이 나오면 키를 입력합니다.
* 이미 있는 키는 엔터(Enter)를 눌러 그대로 유지할 수 있습니다.
* 키 입력 후 `mykit doctor`를 실행하면 **`🟢 Ready`** 상태로 진단됩니다.

---

## 🎛️ 4. 프로필 스위칭 (`mykit profile`)

개발 환경에 따라 필요한 스킬만 로드하여 토큰 소비량을 80% 이상 절감합니다. 두 가지 모드가 있습니다.

### 4-1. 폴더별 프로필 (기본 동작, 권장)

`mykit profile use <profile>`은 기본적으로 **이 컴퓨터의 전역 기본 프로필은 그대로 두고, 지금 있는 이 폴더만** 그 프로필에 묶습니다(이동 없음). 같은 컴퓨터에서 다른 폴더/세션은 계속 기존 프로필을 쓰고, 지금 이 폴더에서 하는 작업 종류(기획 vs 개발)에 따라 필요한 스킬만 바꿔 쓰고 싶을 때 사용합니다.

```bash
cd ~/projects/a-folder

# 기획할 땐
mykit profile use pm

# 개발할 땐 (같은 폴더, 프로필만 교체 — pm 스킬은 정리되고 typescript 스킬로 깨끗하게 교체됨)
mykit profile use typescript
```

다른(지금 있지 않은) 폴더를 특정 프로필에 미리 붙여두고 싶다면 `mykit profile bind <profile> [path]`, 해제는 `mykit profile unbind [path]`.

> ⚠️ **같은 폴더에서 세션 두 개를 동시에 다른 프로필로 돌릴 수는 없습니다.** 로컬 스킬 디렉터리(`.claude/skills`)는 폴더당 하나뿐이라, 세션 A가 general로 열려있는데 세션 B(같은 폴더)에서 `mykit profile use pm`을 실행하면 A가 쓰던 스킬까지 그 자리에서 pm으로 교체됩니다. `mykit profile bind`로 다른 경로를 미리 등록해둬도, 두 세션이 실제로 같은 폴더에서 돌아가는 이상 도움이 안 됩니다.

### 4-1-1. 진짜 동시 작업이 필요할 때 (`--worktree`)

세션마다 실제로 다른 물리적 폴더가 필요하다면 git worktree를 씁니다. `--worktree`를 붙이면 자동으로 만들어(또는 이미 있으면 재사용해) 그 폴더를 프로필에 바인딩합니다.

```bash
mykit profile use pm --worktree              # 기본 경로: ~/.worktrees/<repo-name>/pm
mykit profile use pm --worktree /my/path     # 경로 직접 지정

cd ~/.worktrees/<repo-name>/pm && mykit sync # 안내대로 이동해서 sync
```

git 저장소가 아닌 폴더에서는 에러가 나며, `--global`과는 같이 쓸 수 없습니다.

`mykit profile use <profile>`을 플래그 없이 실행했는데 같은 폴더에서 다른 세션이 이미 떠 있는 게 감지되면, 경고만 출력하고 끝나지 않고 **"대신 git worktree를 새로 만들어서 진행할까요? (y/N)"**라고 직접 물어봅니다.

- `y` → 즉시 worktree를 만들어 그쪽에 바인딩(현재 폴더는 안 건드림), 안내에 따라 그 폴더로 이동해서 sync
- `n` / 그냥 엔터 / 비대화형 환경 → 기존처럼 현재 폴더에 그대로 바인딩하고 진행

(`mykit profile bind`나 `--worktree` 플래그를 직접 쓴 경우는 이미 격리된 경로를 다루는 흐름이라 경고만 뜨고 계속 진행됩니다.) 지금 어떤 세션이 어느 폴더/프로필로 떠 있는지는 `mykit sessions`로 확인하세요.

### 4-2. 회사 PC vs 개인 PC 프로필 스위칭 (`--global`)

한 컴퓨터를 통째로 하나의 프로필로만 쓰고 싶다면(예: 회사 PC는 항상 work, 개인 PC는 항상 personal) `--global` 플래그를 붙입니다. 이 경우 폴더 이동 없이 이 컴퓨터의 전역 기본 프로필 자체가 바뀝니다.

```bash
# 개인 PC 프로필 모드 (TS/JS, React, Python, Java, Kotlin, SpringBoot, Prisma 등)
mykit profile use personal --global

# 회사 PC 프로필 모드 (회사 전용 스택)
mykit profile use work --global

# 전체 모드 (필터링 없이 270+ 스킬 모두 로드)
mykit profile use full --global
```

---

## 🤖 5. 커스텀 서브 에이전트 추가하기 (`agents/`)

`agents/` 폴더에 마크다운(`*.md`) 파일로 역할 및 지침을 작성하면 모든 에이전트로 자동 배포됩니다.

```text
my-ai-kit/agents/
├── reviewer.md   # 시니어 코드 리뷰어 에이전트
└── architect.md  # 시스템 아키텍트 에이전트
```

작성 후 `mykit sync`만 실행하면 Claude, Antigravity, Codex에 자동 연결됩니다.

---

## 🧹 6. 클린 재배포 (Clean Reset & Sync)

기존 설정을 싹 청소하고 완전히 새로 배포하고 싶을 땐 한 줄 콤보 커맨드를 실행하세요:

```bash
mykit reset && mykit sync
```

---

## 🛡️ 7. 안전 명령어 자동 승인 (Auto-Approve Commands)

`git`, `ls`, `cat`, `grep`, `python3`, `npm test` 등 21개 안전 명령어는 Claude Code와 Antigravity CLI에서 명령어 단위 allowlist로 자동 실행됩니다. Codex CLI는 명령어 단위 승인 목록을 지원하지 않아, 대신 `sandbox_mode`/`approval_policy` 설정으로 승인 빈도를 조절합니다. ([`manifest.yaml`](file:///Users/bysu/workspace/my-ai-kit/manifest.yaml)에서 커스텀 변경 가능)
