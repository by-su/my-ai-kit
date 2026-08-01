 새로운 컴퓨터나 환경에서도 단 하나의 명령어(bootstrap.sh)로 Claude Code, Antigravity, Gemini CLI, OpenAI Codex 등 모든 AI 코딩 에이전트의 설정,
  스킬, MCP, 커스텀 프로프트를 동일하게 재현하고 선택적으로 관리할 수 있는 중앙집중형 AI Agent Skill/Config Manager 구축 가이드입니다.
  ──────
  ### 1. 결론: 가장 추천하는 방식

  **"단일 Git Manifest (manifest.yaml + manifest.lock.json) 기반의 CLI (askill) & 어댑터(Adapter) 패턴"**을 강력히 추천합니다.

  • 핵심 전략:
      1. 단일 저장소(Single Source of Truth): 개인 또는 팀의 dot-ai-skills Git 저장소 하나만 관리합니다.
      2. Git Submodule 대신 Custom Git Fetcher + Lockfile: Git Submodule은 관리가 번거롭고 버그가 자주 발생하므로, 자체 CLI가 SHA 40자 커밋 해시
      기반으로 얕은 복사(shallow fetch)하여 manifest.lock.json으로 고정합니다.
      3. Symlink 우선 배포 (Copy Fallback): 중앙 캐시 디렉터리(~/.agent-skills/cache/)에 외부 스킬을 받고, 각 에이전트의 설정 폴더에는 **심볼릭
      링크(Symlink)**를 연결하여 관리 비용과 디스크 용량을 최소화합니다.
      4. 어댑터(Adapter) 엔진: SKILL.md (Open Agent Skill Standard) 규격을 표준으로 삼고, 어댑터가 도구별 특수 포맷(Claude Code Plugin/Prompt,
      Antigravity Skill, Codex Instructions)으로 자동 자동 변환/배포합니다.

  ──────
  ### 2. 전체 아키텍처

    ┌────────────────────────────────────────────────────────────────────────┐
    │                      Central Repository (dot-ai-skills)                │
    │   - manifest.yaml (Core/Optional 지정)                                   │
    │   - manifest.lock.json (외부 Repo Git Commit SHA 고정)                   │
    │   - core/ & optional/ (자체 제작 스킬)                                    │
    └──────────────────────────────────┬─────────────────────────────────────┘
                                       │
                               [ askill sync / bootstrap ]
                                       │
                                       ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │                   Local Cache (~/.agent-skills/store/)                 │
    │   - fetched/ (github.com/user/repo@commit)                             │
    │   - local/   (core & activated optional skills)                        │
    └──────────────────────────────────┬─────────────────────────────────────┘
                                       │
                         ┌─────────────┼─────────────┐
                         │ (Tool Adapters: Symlink) │
                         ▼                           ▼
    ┌───────────────────────────┐         ┌───────────────────────────┐
    │        Claude Code        │         │   Antigravity / Gemini    │
    │ ~/.claude/plugins/        │         │ ~/.gemini/antigravity-cli/│
    │ ~/.claude/config.json     │         │   skills/                 │
    └───────────────────────────┘         └───────────────────────────┘
                         │                           │
                         └─────────────┬─────────────┘
                                       ▼
                          ┌───────────────────────────┐
                          │       OpenAI Codex        │
                          │ ~/.codex/prompts/         │
                          │ ~/.codex/skills/          │
                          └───────────────────────────┘
    ──────
  ### 3. 예시 디렉터리 구조

    dot-ai-skills/
    ├── bootstrap.sh                 # 신규 컴퓨터 1-Line 설치 스크립트
    ├── manifest.yaml                # 중앙 관리 마니페스트
    ├── manifest.lock.json           # 외부 Git 커밋 고정 Lockfile
    ├── bin/
    │   └── askill                   # CLI 실행 파일 (Python 3 기반)
    ├── core/                        # 항상 설치되는 자체 Core 스크립트/스킬
    │   ├── git-workflow/
    │   │   └── SKILL.md
    │   └── code-review/
    │       └── SKILL.md
    ├── optional/                    # 선택형 자체 Optional 스크립트/스킬
    │   ├── k8s-helper/
    │   │   └── SKILL.md
    │   └── db-migrator/
    │       └── SKILL.md
    ├── adapters/                    # 에이전트별 매핑 logic
    │   ├── __init__.py
    │   ├── base.py
    │   ├── claude_code.py
    │   ├── gemini_antigravity.py
    │   └── codex.py
    └── src/                         # CLI 메인 엔진
        ├── config.py
        ├── fetcher.py
        ├── symlink.py
        └── lockfile.py
    ──────
  ### 4. manifest 예시 (manifest.yaml)

    version: "1.0"

    # 에이전트 공통 설정 / MCP 관리
    global:
      mcp_servers:
        context7:
          command: "npx"
          args: ["-y", "@context7/mcp-server"]
        github:
          command: "npx"
          args: ["-y", "@modelcontextprotocol/server-github"]
          env:
            GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"

    # 필수로 항상 설치/연결되는 Core 스크립트 & 스킬
    core:
      # 자체 관리 Core 스크립트
      - name: "core-git-workflow"
        source: "local"
        path: "core/git-workflow"

      # 외부 GitHub Open-Source 스킬
      - name: "everything-claude-core"
        source: "github"
        url: "https://github.com/affableshin/everything-claude-code.git"
        path: "skills/core-suite"

    # 선택적으로 설치/해제하는 Optional 스킬
    optional:
      - name: "react-best-practices"
        description: "React 19 & Next.js App Router 코드 스타일 체크"
        source: "github"
        url: "https://github.com/vercel/ai-skills.git"
        path: "skills/react"
        default_enabled: false

      - name: "database-helper"
        description: "PostgreSQL & Prisma 마이그레이션 도우미"
        source: "local"
        path: "optional/db-migrator"
        default_enabled: true

    # 도구별 활성화 여부
    targets:
      claude_code: true
      antigravity: true
      codex: true
    ──────
  ### 5. lockfile 예시 (manifest.lock.json)

  askill update 실행 시 생성/갱신되며, 모든 팀원과 새 머신에서 exact 100% 동일한 외부 스킬 버전을 고정합니다.

    {
      "version": "1.0",
      "generated_at": "2026-08-01T23:40:00Z",
      "skills": {
        "everything-claude-core": {
          "url": "https://github.com/affableshin/everything-claude-code.git",
          "commit": "a1b2c3d4e5f67890123456789abcdef012345678",
          "tree_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        },
        "react-best-practices": {
          "url": "https://github.com/vercel/ai-skills.git",
          "commit": "9f8e7d6c5b4a3210987654321fedcba098765432",
          "tree_hash": "c7be1e4c7b80a22830f367fa11c2105151590473950efcf8d91f211516e872e4"
        }
      }
    }
    ──────
  ### 6. CLI 명령어 UX 예시 (askill)

  Python으로 작성되어 별도 파이썬 라이브러리 설치 없이 바로 실행 가능하도록 설계합니다.

    # 1. 초기 설치 및 환경 배포 (새 컴퓨터에서 실행)
    $ askill bootstrap

    # 2. 스킬 목록 확인 (Core / Enabled Optional / Disabled Optional 구분)
    $ askill list
    [Core Skills]
      ✓ core-git-workflow (local)
      ✓ everything-claude-core (github: affableshin/everything-claude-code)

    [Optional Skills]
      [x] database-helper (local) - PostgreSQL & Prisma 마이그레이션 도우미
      [ ] react-best-practices (github: vercel/ai-skills) - React 19 & Next.js 스타일

    # 3. Optional 스킬 설치/활성화
    $ askill install react-best-practices
    > Fetching github.com/vercel/ai-skills@9f8e7d6... done.
    > Enabling skill 'react-best-practices'...
    > Linking to Claude Code, Antigravity, Codex adapters... Done!

    # 4. Optional 스킬 제거/비활성화
    $ askill remove react-best-practices
    > Unlinking skill 'react-best-practices' from all adapters... Done!

    # 5. Lockfile 기반 전제 동기화 (manifest & lockfile 적용)
    $ askill sync

    # 6. 외부 스킬 최신 버전으로 업데이트 및 lockfile 갱신
    $ askill update everything-claude-core

    # 7. 상태 점검 및 깨진 심볼릭 링크 검사
    $ askill doctor
    [✓] Manifest syntax valid.
    [✓] Lockfile synchronized.
    [✓] Claude Code adapter: 4 skills linked.
    [✓] Antigravity adapter: 4 skills linked.
    [✓] Codex adapter: 4 skills linked.
    [✓] No broken symlinks found.
    ──────
  ### 7. 도구별 적용 전략 (Adapters)

  각 AI 도구는 스킬 저장 위치와 형식에 차이가 있습니다. askill 어댑터가 이를 흡수합니다.

   도구         │ 표준 스킬 위치                              │ MCP 위치              │ 어댑터 동작 방식
  ──────────────┼─────────────────────────────────────────────┼───────────────────────┼──────────────────────────────────────────────────────────
   Claude Code  │ ~/.claude/plugins/ 또는 ~/.claude/commands/ │ ~/.claude.json        │ SKILL.md 포맷을 읽고 custom command 및 plugin 디렉터리로
                │                                             │                       │ 심볼릭 링크 생성. MCP JSON 병합.
   Antigravity  │ ~/.gemini/antigravity-cli/skills/           │ ~/.gemini/antigravity │ 표준 SKILL.md (YAML Frontmatter + Markdown) 형태 그대로
                │                                             │ -cli/mcp_config.json  │ 심볼릭 링크 생성. MCP 설정 자동 연동.
   Gemini CLI   │ ~/.gemini/skills/ 또는 ~/.gemini/prompts/   │ ~/.gemini/config.json │ SKILL.md의 prompt 구문을 Gemini prompt 템플릿으로
                │                                             │                       │ 링크/배포.
   OpenAI Codex │ ~/.codex/skills/ 및                         │ ~/.codex/config.json  │ 스킬 폴더 Symlink 매핑 및 커스텀 프로프트를 Codex system
                │ ~/.codex/instructions.md                    │                       │ prompt 디렉터리로 내보내기.

  #### 어댑터 변환 예시 (Antigravity & Claude Code 공통 표준 SKILL.md)

  외부 저장소에서 스킬을 가져올 때 아래와 같은 SKILL.md가 포함되어 있으면 모든 에이전트에서 그대로 인식합니다:

    ---
    name: react-best-practices
    description: Next.js 및 React 19 컴포넌트 작성 규칙
    tools:
      - run_command
      - view_file
    ---
    # React Best Practices
    1. Server Component를 기본으로 사용하세요.
    2. 'use client' 디렉티브는 상태 변경이 발생하는 최하단 컴포넌트에만 선언하세요.
    ──────
  ### 8. MVP 구현 순서

  복잡하게 시작하지 말고, 아래 3단계 순서로 구현하면 반나절 만에 MVP를 완성할 수 있습니다.

  #### [1단계] 저장소 및 Manifest 기본 구축

  1. dot-ai-skills Git repo 생성.
  2. core/ 디렉터리에 자주 쓰는 개인 프롬프트/스킬 저장.
  3. manifest.yaml 작성.

  #### [2단계] 핵심 CLI (askill) 파이썬 스크립트 작성 (bin/askill)

  의존성 없는 Pure Python 3 스크립트로 구현합니다 (urllib, subprocess, json, pathlib, os 활용).

  • fetch_git_repo(url, commit): git clone --depth 1 또는 git fetch로 ~/.agent-skills/store/에 저장.
  • link_skills(): 선택된 스킬들을 ~/.claude/plugins/, ~/.gemini/antigravity-cli/skills/에 os.symlink로 연결.

  #### [3단계] bootstrap.sh 1-Line 스크립트 작성

    #!/usr/bin/env bash
    set -e

    DOTFILES_REPO="https://github.com/YOUR_USERNAME/dot-ai-skills.git"
    TARGET_DIR="$HOME/.dot-ai-skills"

    if [ ! -d "$TARGET_DIR" ]; then
        echo "Cloning dot-ai-skills..."
        git clone "$DOTFILES_REPO" "$TARGET_DIR"
    else
        echo "Updating dot-ai-skills..."
        git -C "$TARGET_DIR" pull
    fi

    # PATH 등록 및 실행권한 부여
    chmod +x "$TARGET_DIR/bin/askill"
    export PATH="$TARGET_DIR/bin:$PATH"

    # 전체 초기화 및 동기화
    "$TARGET_DIR/bin/askill" bootstrap

  새 컴퓨터에서는 curl -fsSL https://raw.githubusercontent.com/.../bootstrap.sh | bash 한 줄로 모든 설치가 종료됩니다.
  ──────
  ### 9. 주의할 점 & 트레이드오프 비교

  #### A. Symlink 방식 vs Copy 방식

  • 추천: Symlink 방식 기본 + Copy Fallback
  • 장점: 본사 repo나 ~/.agent-skills/store/에서 스킬 파일 수정 시, Claude Code / Antigravity / Codex에 즉시 반영됨 (재배포 불필요).
  • 주의점: Windows 환경의 경우 권한 이슈로 symlink 실패 가능. 이때 CLI가 감지하여 자동 Copy로 전환(fallback)되도록 예외 처리 구현.

  #### B. Plugin 묶음 vs 개인 디렉터리 직접 설치

  • 추천: ~/.agent-skills/ 중앙 관리 후 에이전트별 전용 디렉터리로 심볼릭 링크
  • Claude Code 전용 플러그인 형식에 고착되면 Antigravity나 Codex에서 사용하기 까다롭습니다. 스킬 원본은 오픈 스킬 표준(SKILL.md)으로 갖고 있고,
  어댑터가 각 도구의 폴더 구조에 맞게 링크를 걸어주는 것이 유연합니다.

  #### C. 팀/개인 충돌 방지 네이밍 규칙

  • 외부 GitHub 스킬과 자체 스킬의 네임스페이스 충돌을 방지하기 위해 네이밍 접두사를 사용합니다:
      • 자체 core 스킬: core-<name> (예: core-git-review)
      • 외부 오픈소스 스킬: <owner>-<name> (예: affableshin-everything-claude)


  #### D. 보안상 주의할 점

  1. Malicious Prompt Injection 주의: 외부 스킬 repo를 가져올 때, 커밋 SHA를 고정하지 않으면 외부 사용자가 원격 스킬에 악의적인 프롬프트나 bash
  명령어(run_command) 실행 구문을 심어 내 컴퓨터에서 실행시킬 수 있습니다. 반드시 manifest.lock.json으로 Commit SHA를 고정하세요.
  2. API Key 유출 방지: MCP 설정 등에서 API 키는 absolute string으로 저장하지 말고 ${GITHUB_TOKEN}처럼 환경 변수 치환 문법을 사용합니다.
  ──────
  ### 10. 최종 추천 운영 프로세스

  1. 평소 스킬 추가 및 업데이트 작업:
      • 외부 오픈소스 스킬 발굴 → manifest.yaml의 optional에 추가.
      • askill update <skill-name> 실행 → 커밋 SHA 고정 및 manifest.lock.json 자동 업데이트.
      • git commit -am "feat: add new optional skill" && git push
  2. 일회성 프로젝트 작업 시:
      • 특정 프로젝트 전용 스킬이 필요하면 askill install react-best-practices 실행.
      • 작업 종료 후 askill remove react-best-practices 실행.
  3. 새로운 개발용 PC 세팅 시:
      • curl -fsSL https://raw.githubusercontent.com/<your-id>/dot-ai-skills/main/bootstrap.sh | bash
      • 실행 한 번으로 기존에 쓰던 모든 커스텀 스킬, 오픈소스 스킬, MCP 설정이 즉시 복구됩니다.
