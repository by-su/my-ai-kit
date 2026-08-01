# 🧰 my-ai-kit

**Antigravity, Claude Code, OpenAI Codex, Gemini CLI** 등 여러 AI 코딩 에이전트의 스킬(Skills), 커스텀 서브 에이전트(Subagents), MCP 설정, 프로프트를 한 곳에서 중앙 관리하고 단 한 줄의 명령어(`mykit sync`)로 완벽하게 복구/동기화하는 **Multi-Agent Config & Skill Manager**입니다.

---

## 📌 핵심 기억할 사항 (Cheat Sheet)

### 1. 자주 쓰는 CLI 명령어
터미널 어디서나 실행할 수 있도록 `PATH`에 등록하여 사용합니다.

| 명령어 | 설명 |
| :--- | :--- |
| `mykit list` | 활성화된 스택 프로필, MCP 서버, 커스텀 서브 에이전트(`agents/*.md`), Core 및 Local 스킬 조회 |
| `mykit mcp` | 등록된 MCP 서버 활성화 상태 조회 및 토글 (`mykit mcp enable \| disable <mcp-name>`) |
| `mykit stack` | 현재 스택 프로필 조회 및 전환 (`mykit stack use personal \| work \| full`) |
| `mykit install <skill-name>` | **현재 작업 중인 프로젝트 디렉터리(`pwd`)** 내부로 Optional 스킬 설치 (`.claude/skills`, `.gemini/skills`) |
| `mykit install <skill-name> --global` | Optional 스킬을 전역(Global) 스코프로 설치 |
| `mykit remove <skill-name>` | 현재 작업 중인 프로젝트 디렉터리(`pwd`)에서 Optional 스킬 제거 |
| `mykit sync` | `manifest.yaml` 기반 스택 프로필, 활성화된 MCP, 커스텀 서브 에이전트, Core/Local 스킬 전체 동기화 |
| `mykit completion install` | **Zsh / Bash 터미널 자동 완성(Tab Completion)** 1초 등록 |
| `mykit update [skill-name]` | 외부 GitHub 스킬 최신 커밋으로 업데이트 및 Lockfile 갱신 |
| `mykit lint [--fix]` | 스킬 YAML 문법, 이름 중복 충돌 및 깨진 심볼릭 링크 자동 점검 (`--fix` 옵션으로 유령 링크 자동 정리) |
| `mykit dedupe [threshold]` | 스킬 간 키워드/내용 겹침을 분석하여 유사 중복 스킬 탐지 (기본 30%) |
| `mykit doctor` | 설정 파일 검증, MCP 헬스체크/시크릿 키 진단 및 에이전트별 연결 상태 점검 |

---

## ⌨️ 터미널 자동 완성 (Tab Completion)

터미널에서 `mykit <Tab>` 키를 누르면 모든 명령어와 스킬 이름이 **자동 완성**됩니다.

```bash
# 1. 자동 완성 1초 등록
mykit completion install

# 2. 터미널 갱신
source ~/.zshrc
```

---

## 🤖 커스텀 서브 에이전트 (Custom Subagents) 동기화

`agents/` 폴더에 마크다운(`*.md`) 형태로 서브 에이전트 페르소나 및 전용 지침을 작성해 두면, `mykit sync` 한 줄로 **Claude Code, Antigravity, OpenAI Codex 에이전트 경로로 자동 배포**됩니다.

* `agents/reviewer.md`: 시니어 코드 리뷰어 서브 에이전트
* `agents/architect.md`: 시스템 아키텍트 서브 에이전트

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

## ⚡ 스택 프로필 (Stack Profiles) 관리

회사 PC와 개인 PC의 개발 스택이 다르거나 270+ 스킬 전체를 전부 로드해야 할 때 프로필 한 줄로 유연하게 전환할 수 있습니다.

```bash
# 1. 개인 PC 스택 모드 (TS/JS, React, Python, Java, Kotlin, SpringBoot, Prisma 등)
mykit stack use personal

# 2. 회사 PC 스택 모드 (회사 전용 기술 스택)
mykit stack use work

# 3. 전체 모드 (필터링 없이 270+ 스킬 전부 로드)
mykit stack use full
```

---

## 📂 스코프(Scope) 분리 아키텍처

* **Core 스킬 (Global Scope)**:  
  어디서나 항상 필요한 필수 스킬로, 사용자 홈 디렉터리(`~/.claude/plugins/`, `~/.gemini/antigravity-cli/skills/`)로 전역 배포됩니다.
* **Optional 스킬 (Local `pwd` Scope)**:  
  프로젝트별로 선택해서 쓰는 스킬로, **내가 현재 위치한 프로젝트 디렉터리(`pwd`)의 `.claude/skills/`, `.gemini/skills/` 내부로만 심볼릭 링크**가 생성되어 해당 프로젝트를 열었을 때만 AI가 읽습니다.

---

## 📂 디렉터리 구성 및 역할

```text
my-ai-kit/
├── README.md                    # 사용 가이드 및 명령어 치트시트
├── manifest.yaml                # 중앙 관리 마니페스트 (Core/Optional/MCP/Profiles 지정)
├── manifest.lock.json           # 외부 GitHub 스킬 커밋 SHA 고정 장부
├── bootstrap.sh                 # 새 컴퓨터 1-Line 초기화 스크립트
├── .env.example                 # MCP API 키/시크릿 보관용 템플릿
├── agents/                      # 커스텀 서브 에이전트 페르소나 정의 (reviewer.md, architect.md 등)
├── completions/                 # Zsh / Bash 터미널 자동 완성 스크립트
├── bin/
│   └── mykit                    # 메인 CLI 실행 파일
├── core/                        # 항상 전역으로 설치되는 자체 Core 스크립트/스킬
│   └── git-workflow/SKILL.md
├── optional/                    # 필요 시 프로젝트(`pwd`)별로 설치하는 Optional 스크립트/스킬
│   └── db-helper/SKILL.md
├── adapters/                    # 에이전트별(Antigravity, Claude, Codex) 전역/로컬 자동 링크 어댑터
└── src/                         # CLI 엔진 (Config, Symlink, Fetcher, MCP, Linter, Dedupe, Pruner, Completion)
```

---

## 🚀 워크플로우 가이드

### 1. 특정 프로젝트 폴더에서 스킬 설치 및 사용하기 (Local Scope)
```bash
# 1. 내 프로젝트 폴더로 이동
cd ~/workspace/my-react-project

# 2. 이 프로젝트에서만 사용할 Optional 스킬 설치
mykit install prompt-architect

# -> 해당 프로젝트 폴더 내부(./.claude/skills/prompt-architect)로 가상 링크 생성!
```

---

### 2. 새 컴퓨터에서 환경 1초 복구하기 (Bootstrap)
새 컴퓨터로 옮겼을 때 아래 스크립트 한 줄로 기존 세팅을 100% 동일하게 재현합니다:

```bash
# PATH 등록 (~/.zshrc 또는 ~/.bashrc)
export PATH="$HOME/workspace/my-ai-kit/bin:$PATH"

# 복구 실행
./bootstrap.sh
```

---

## 🔒 보안 및 버전 고정 (`manifest.lock.json`)
* 외부 GitHub 스킬은 `auto_update: false`로 설정하면 `manifest.lock.json`에 기록된 **Git Commit SHA** 버전만 고정되어 설치되므로, 외부 수정으로 인한 오염을 방지할 수 있습니다.
* 스킬 최신화가 필요할 땐 언제든 `mykit update <skill-name>`을 실행하세요.
