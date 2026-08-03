# 🧰 my-ai-kit

**Antigravity, Claude Code, OpenAI Codex, Gemini CLI** 등 여러 AI 코딩 에이전트의 스킬(Skills), MCP 설정, 커스텀 명령어, 프로프트를 한 곳에서 중앙 관리하고 단 한 줄의 명령어(`mykit sync`)로 완벽하게 복구/동기화하는 **Multi-Agent Config & Skill Manager**입니다.

---

## 📌 핵심 기억할 사항 (Cheat Sheet)

### 1. 자주 쓰는 CLI 명령어
터미널 어디서나 실행할 수 있도록 `PATH`에 등록하여 사용합니다.

| 명령어 | 설명 |
| :--- | :--- |
| `mykit list` | MCP 서버, Core(전역) 스킬 및 현재 프로젝트(`pwd`) Optional 스킬 상태 조회 |
| `mykit install <skill-name>` | **현재 작업 중인 프로젝트 디렉터리(`pwd`)** 내부로 Optional 스킬 설치 (`.claude/skills`, `.gemini/skills`) |
| `mykit install <skill-name> --global` | Optional 스킬을 전역(Global) 스코프로 설치 |
| `mykit remove <skill-name>` | 현재 작업 중인 프로젝트 디렉터리(`pwd`)에서 Optional 스킬 제거 |
| `mykit sync` | `manifest.yaml` 및 `manifest.lock.json` 기반 Core(전역) 및 Local(`pwd`) 스킬/MCP 전체 동기화 |
| `mykit update [skill-name]` | 외부 GitHub 스킬 최신 커밋으로 업데이트 및 Lockfile 갱신 |
| `mykit lint [--fix]` | 스킬 YAML 문법, 이름 중복 충돌 및 깨진 심볼릭 링크 자동 점검 (`--fix` 옵션으로 유령 링크 자동 정리) |
| `mykit dedupe [threshold]` | 200+ 스킬 간 키워드/내용 겹침을 분석하여 유사 중복 스킬 탐지 (기본 30%) |
| `mykit doctor` | 설정 파일 검증 및 에이전트별 심볼릭 링크 연결 상태 진단 |

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
├── manifest.yaml                # 중앙 관리 마니페스트 (Core/Optional/MCP 지정)
├── manifest.lock.json           # 외부 GitHub 스킬 커밋 SHA 고정 장부
├── bootstrap.sh                 # 새 컴퓨터 1-Line 초기화 스크립트
├── bin/
│   └── mykit                    # 메인 CLI 실행 파일
├── core/                        # 항상 전역으로 설치되는 자체 Core 스크립트/스킬
│   └── git-workflow/SKILL.md
├── optional/                    # 필요 시 프로젝트(`pwd`)별로 설치하는 Optional 스크립트/스킬
│   └── db-helper/SKILL.md
├── adapters/                    # 에이전트별(Antigravity, Claude, Codex) 전역/로컬 자동 링크 어댑터
└── src/                         # CLI 엔진 (Config, Symlink, Fetcher, MCP, Linter, Dedupe)
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
