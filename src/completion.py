import sys
import os
from pathlib import Path
from src.config import load_manifest, KIT_DIR

ZSH_COMPLETION_SCRIPT = """#compdef mykit

_mykit() {
    local curcontext="$curcontext" state line
    typeset -A opt_args

    _arguments -C \\
        '1: :->command' \\
        '*: :->args'

    case $state in
        command)
            local -a commands
            commands=(
                'list:Show status of MCPs, custom agents, core and optional skills'
                'stats:View system analytics, token savings, and adapter connectivity'
                'env:Interactive setup wizard for MCP API keys and secrets'
                'stack:View or switch stack profiles (personal, work, full)'
                'mcp:View or toggle MCP servers (enable, disable)'
                'install:Install optional skill to pwd (or --global)'
                'remove:Remove optional skill from pwd (or --global)'
                'sync:Synchronize all skills, MCPs, and agents across adapters'
                'update:Update remote GitHub skills to latest commits'
                'lint:Check skill frontmatter and symlink integrity (--fix)'
                'dedupe:Detect semantic overlaps across skills'
                'doctor:Run health check on manifest, MCP secrets, and adapters'
                'completion:Generate or install zsh/bash tab completion'
            )
            _describe -t commands 'mykit command' commands
            ;;
        args)
            case $words[2] in
                stack)
                    if [[ $#words -eq 3 ]]; then
                        local -a stack_cmds
                        stack_cmds=('use' 'set' 'list')
                        _describe -t stack_cmds 'stack command' stack_cmds
                    elif [[ $#words -eq 4 ]]; then
                        local -a profiles
                        profiles=('personal' 'work' 'full')
                        _describe -t profiles 'profile' profiles
                    fi
                    ;;
                mcp)
                    if [[ $#words -eq 3 ]]; then
                        local -a mcp_cmds
                        mcp_cmds=('enable' 'disable' 'list')
                        _describe -t mcp_cmds 'mcp command' mcp_cmds
                    fi
                    ;;
                env)
                    if [[ $#words -eq 3 ]]; then
                        local -a env_cmds
                        env_cmds=('setup')
                        _describe -t env_cmds 'env command' env_cmds
                    fi
                    ;;
                install|enable|remove|disable)
                    if [[ $#words -eq 3 ]]; then
                        local -a skills
                        skills=($(mykit_get_optionals))
                        _describe -t skills 'optional skill' skills
                    fi
                    ;;
                completion)
                    local -a comp_opts
                    comp_opts=('zsh' 'bash' 'install')
                    _describe -t comp_opts 'completion target' comp_opts
                    ;;
            esac
            ;;
    esac
}

mykit_get_mcps() {
    echo "context7 github google-docs google-slides mysql playwright memory brave-search"
}

mykit_get_optionals() {
    echo "db-helper ecc-suite mengto-skills prompt-architect"
}

_mykit "$@"
"""

BASH_COMPLETION_SCRIPT = """# bash completion for mykit

_mykit_completions() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    opts="list stats env stack mcp install remove sync update lint dedupe doctor completion"

    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    case "${prev}" in
        stack)
            COMPREPLY=( $(compgen -W "use set list personal work full" -- ${cur}) )
            return 0
            ;;
        mcp)
            COMPREPLY=( $(compgen -W "enable disable list context7 github google-docs google-slides mysql playwright memory brave-search" -- ${cur}) )
            return 0
            ;;
        env)
            COMPREPLY=( $(compgen -W "setup" -- ${cur}) )
            return 0
            ;;
        install|remove)
            COMPREPLY=( $(compgen -W "db-helper ecc-suite mengto-skills prompt-architect --global" -- ${cur}) )
            return 0
            ;;
        completion)
            COMPREPLY=( $(compgen -W "zsh bash install" -- ${cur}) )
            return 0
            ;;
    esac
}

complete -F _mykit_completions mykit
"""

def generate_completion(shell_type):
    if shell_type == "zsh":
        print(ZSH_COMPLETION_SCRIPT.strip())
    elif shell_type == "bash":
        print(BASH_COMPLETION_SCRIPT.strip())
    elif shell_type == "install":
        install_completion()

def install_completion():
    home = Path.home()
    zshrc = home / ".zshrc"
    bashrc = home / ".bashrc"

    comp_dir = KIT_DIR / "completions"
    comp_dir.mkdir(parents=True, exist_ok=True)

    zsh_file = comp_dir / "_mykit"
    with open(zsh_file, 'w', encoding='utf-8') as f:
        f.write(ZSH_COMPLETION_SCRIPT.strip())

    bash_file = comp_dir / "mykit.bash"
    with open(bash_file, 'w', encoding='utf-8') as f:
        f.write(BASH_COMPLETION_SCRIPT.strip())

    line_to_add = f'source "{zsh_file.resolve()}"'

    if zshrc.exists():
        content = zshrc.read_text(encoding='utf-8', errors='ignore')
        if str(zsh_file) not in content:
            with open(zshrc, 'a', encoding='utf-8') as f:
                f.write(f"\n# mykit tab completion\ncompdef _mykit mykit\n{line_to_add}\n")
            print(f"✓ Appended zsh completion loader to {zshrc}")
        else:
            print(f"✓ zsh completion already installed in {zshrc}")

    print("\033[1;32m🎉 Tab completion installed! Run 'source ~/.zshrc' to activate tab completion.\033[0m")
