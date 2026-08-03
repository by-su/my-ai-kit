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
                'setup:Choose or create profile, global skills, pruning, and MCPs'
                'stats:View system analytics, token savings, and adapter connectivity'
                'env:Interactive setup wizard for MCP API keys and secrets'
                'profile:View, switch, or edit profiles'
                'mcp:View or toggle MCP servers (enable, disable)'
                'install:Install optional skill to pwd (or --global)'
                'remove:Remove optional skill from pwd (or --global)'
                'sync:Synchronize active skills, MCPs, and agents across adapters'
                'prefetch:Download GitHub skills without enabling them'
                'reset:Reset all agent configs and symlinks cleanly'
                'update:Update fetched remote GitHub skills to latest commits'
                'lint:Check skill frontmatter and symlink integrity (--fix)'
                'dedupe:Detect semantic overlaps across skills'
                'doctor:Run health check on manifest, MCP secrets, and adapters'
                'completion:Generate or install zsh/bash tab completion'
            )
            _describe -t commands 'mykit command' commands
            ;;
        args)
            case $words[2] in
                profile|stack)
                    if [[ $#words -eq 3 ]]; then
                        local -a profile_cmds
                        profile_cmds=('use' 'set' 'list' 'edit' 'remove' 'delete')
                        _describe -t profile_cmds 'profile command' profile_cmds
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
                install|enable|remove|disable|prefetch)
                    if [[ $#words -eq 3 ]]; then
                        local -a skills
                        skills=($(mykit_get_optionals))
                        _describe -t skills 'optional skill' skills
                    fi
                    ;;
                sync|update)
                    local -a common_opts
                    common_opts=('--all')
                    _describe -t common_opts 'option' common_opts
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
    echo "db-helper ecc-suite mengto-skills prompt-architect app-store-screenshots spec-kit pm-skills"
}
"""

BASH_COMPLETION_SCRIPT = """# bash completion for mykit

_mykit_completions() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    opts="list setup stats env profile stack mcp install remove sync prefetch reset update lint dedupe doctor completion"

    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    case "${prev}" in
        profile|stack)
            COMPREPLY=( $(compgen -W "use set list edit remove delete" -- ${cur}) )
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
        install|remove|prefetch)
            COMPREPLY=( $(compgen -W "db-helper ecc-suite mengto-skills prompt-architect app-store-screenshots spec-kit pm-skills --global --all" -- ${cur}) )
            return 0
            ;;
        sync|update)
            COMPREPLY=( $(compgen -W "--all" -- ${cur}) )
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

    comp_dir = KIT_DIR / "completions"
    comp_dir.mkdir(parents=True, exist_ok=True)

    zsh_file = comp_dir / "_mykit"
    with open(zsh_file, 'w', encoding='utf-8') as f:
        f.write(ZSH_COMPLETION_SCRIPT.strip())

    bash_file = comp_dir / "mykit.bash"
    with open(bash_file, 'w', encoding='utf-8') as f:
        f.write(BASH_COMPLETION_SCRIPT.strip())

    if zshrc.exists():
        lines = zshrc.read_text(encoding='utf-8', errors='ignore').splitlines()
        new_lines = [l for l in lines if "mykit" not in l and "compdef _mykit" not in l and "_mykit" not in l]
        
        # Clean zshrc and add proper fpath completion loading
        zsh_entry = f'\n# mykit CLI PATH & Completion\nexport PATH="{KIT_DIR}/bin:$PATH"\nfpath=("{comp_dir}" $fpath)\nautoload -U compinit && compinit -u\ncompdef _mykit mykit\n'
        
        with open(zshrc, 'w', encoding='utf-8') as f:
            f.write("\n".join(new_lines) + zsh_entry)
            
        print(f"✓ Fixed and updated zsh completion in {zshrc}")

    print("\033[1;32m🎉 Zsh Tab completion cleanly installed!\033[0m")
