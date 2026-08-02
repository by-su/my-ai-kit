# ⚡ my-ai-kit 퀵 스타트 가이드 (Quick Start Guide)

**my-ai-kit**은 Antigravity, Claude Code, OpenAI Codex, Gemini CLI 등 여러 AI 에이전트의 **스킬(Skills), MCP 서버, 커스텀 서브 에이전트(Subagents), 안전 커맨드 승인 규칙**을 한곳에서 중앙 관리하고 단 한 줄로 동기화하는 멀티 에이전트 설정 관리자입니다.

---

## 🚀 1. 3초 원클릭 초기화 (Bootstrap)

새로운 컴퓨터나 터미널 환경에서 아래 명령어를 실행하면 환경 구축이 끝납니다:

```bash
# 1. 1-Line 초기화 실행
./bootstrap.sh

# 2. 터미널 갱신
source ~/.zshrc
```

---

## 💻 2. 핵심 명령어 치트시트 (Cheat Sheet)

| 명령어 | 설명 | 비고 |
| :--- | :--- | :--- |
| `mykit list` | 현재 스택 프로필, MCP, 서브 에이전트, 스킬 목록 상태 조회 | 현황 확인 |
| `mykit sync` | 마니페스트 기반 전체 에이전트(Claude, Antigravity, Codex) 동기화 | 핵심 배포 |
| `mykit reset` | 찌꺼기 심볼릭 링크 및 구버전 설정 100% 클린 리셋 | 초기화 |
| `mykit stats` | 시스템 통계 대시보드 (스킬 감축률, 토큰 절약량, 에이전트 연결 현황) | 시각화 |
| `mykit env setup` | MCP API 키 및 시크릿 인터랙티브 대화형 등록 마법사 | 키 세팅 |
| `mykit stack` | 개발 스택 프로필 조회 및 전환 (`mykit stack use personal \| work \| full`) | 스택 스위칭 |
| `mykit mcp` | MCP 서버 켜기/끄기 토글 (`mykit mcp enable \| disable <mcp-name>`) | MCP 관리 |
| `mykit doctor` | MCP 헬스체크, 시크릿 키 검증, 에이전트 연결 상태 점검 | 진단 |
| `mykit completion install` | Zsh / Bash 터미널 자동 완성(Tab Completion) 1초 등록 | 편의 기능 |
| `mykit install <skill>` | 현재 작업 중인 프로젝트 디렉터리(`pwd`)로 스킬 설치 | 프로젝트 로컬 |
| `mykit lint [--fix]` | 스킬 YAML 문법, 이름 중복 충돌 및 깨진 링크 자동 검사 | 검증 |
| `mykit dedupe` | 스킬 간 텍스트/내용 겹침을 분석하여 유사 중복 탐지 | 중복 점검 |

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

## 🎛️ 4. 회사 PC vs 개인 PC 스택 스위칭 (`mykit stack`)

개발 환경에 따라 필요한 스킬만 로드하여 토큰 소비량을 80% 이상 절감합니다.

```bash
# 개인 PC 스택 모드 (TS/JS, React, Python, Java, Kotlin, SpringBoot, Prisma 등)
mykit stack use personal

# 회사 PC 스택 모드 (회사 전용 스택)
mykit stack use work

# 전체 모드 (필터링 없이 270+ 스킬 모두 로드)
mykit stack use full
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

`git`, `ls`, `cat`, `grep`, `python3`, `npm test` 등 21개 안전 명령어는 매번 사람이 승인 버튼을 누르지 않아도 **모든 에이전트에서 자동 실행**됩니다. ([`manifest.yaml`](file:///Users/bysu/workspace/my-ai-kit/manifest.yaml)에서 커스텀 변경 가능)
