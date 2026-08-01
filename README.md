# 🧰 my-ai-kit

**Antigravity, Claude Code, OpenAI Codex, Gemini CLI** 등 여러 AI 코딩 에이전트의 스킬(Skills), MCP 설정, 커스텀 명령어, 프로프트를 한 곳에서 중앙 관리하고 단 한 줄의 명령어(`mykit sync`)로 완벽하게 복구/동기화하는 **Multi-Agent Config & Skill Manager**입니다.

---

## 📌 핵심 기억할 사항 (Cheat Sheet)

### 1. 자주 쓰는 CLI 명령어
터미널 어디서나 실행할 수 있도록 `PATH`에 등록하여 사용합니다.

| 명령어 | 설명 |
| :--- | :--- |
| `mykit list` | 현재 설치된 Core 스킬 및 Optional 스킬의 활성화 상태 조회 |
| `mykit install <skill-name>` | Optional 스킬 활성화 및 심볼릭 링크 동기화 |
| `mykit remove <skill-name>` | Optional 스킬 비활성화 (링크 제거) |
| `mykit sync` | `manifest.yaml` 및 `manifest.lock.json` 기반 전체 동기화 |
| `mykit update [skill-name]` | 외부 GitHub 스킬 최신 커밋으로 업데이트 및 Lockfile 갱신 |
| `mykit doctor` | 설정 파일 검증 및 에이전트별 심볼릭 링크 연결 상태 진단 |

---

## 📂 디렉터리 구성 및 역할

```text
my-ai-kit/
├── README.md                    # 사용 가이드 및 명령어 치트시트
├── manifest.yaml                # 중앙 관리 마니페스트 (Core/Optional 지정)
├── manifest.lock.json           # 외부 GitHub 스킬 커밋 SHA 고정 장부
├── bootstrap.sh                 # 새 컴퓨터 1-Line 초기화 스크립트
├── bin/
│   └── mykit                    # 메인 CLI 실행 파일
├── core/                        # 항상 설치되는 자체 Core 스크립트/스킬
│   └── git-workflow/SKILL.md
├── optional/                    # 선택형 자체 Optional 스크립트/스킬
│   └── db-helper/SKILL.md
├── adapters/                    # 에이전트별(Antigravity, Claude, Codex) 자동 링크 어댑터
└── src/                         # CLI 엔진 (Config, Symlink, Fetcher)
```

---

## 🚀 워크플로우 가이드

### 1. 내가 직접 만든 새로운 스킬 추가하기
1. `core/` (필수) 또는 `optional/` (선택) 폴더에 스킬 폴더 생성 후 `SKILL.md` 작성:
   ```markdown
   ---
   name: my-custom-skill
   description: 내 전용 코드 정적 분석 도우미
   ---
   # My Custom Skill Rules
   1. 코드를 작성하기 전 함수 타입을 명확히 정의합니다.
   ```
2. `manifest.yaml`에 등록:
   ```yaml
   optional:
     - name: "my-custom-skill"
       description: "내 전용 코드 정적 분석 도우미"
       source: "local"
       path: "optional/my-custom-skill"
       default_enabled: true
   ```
3. `mykit sync` 실행으로 에이전트에 반영!

---

### 2. 외부 GitHub 오픈소스 스킬 추가하기
1. `manifest.yaml`에 외부 GitHub URL 등록:
   ```yaml
   optional:
     - name: "everything-claude"
       description: "Everything Claude Code 최신 스킬 팩"
       source: "github"
       url: "https://github.com/affableshin/everything-claude-code.git"
       auto_update: true   # sync 때마다 최신 커밋 자동 반영
       default_enabled: false
   ```
2. `mykit install everything-claude` 실행! (자동 clone 및 에이전트 링크 동기화)

---

### 3. 새 컴퓨터에서 환경 1초 복구하기 (Bootstrap)
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
