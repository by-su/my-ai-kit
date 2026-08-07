# bash completion for mykit

_mykit_completions() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    opts="list setup stats env profile stack mcp language install remove sync prefetch reset update lint dedupe doctor completion"

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
        language)
            COMPREPLY=( $(compgen -W "get set sync" -- ${cur}) )
            return 0
            ;;
        env)
            COMPREPLY=( $(compgen -W "setup" -- ${cur}) )
            return 0
            ;;
        install|remove|prefetch)
            COMPREPLY=( $(compgen -W "app-store-screenshots coolify copilotkit ecc-suite inspect-ai mengto-skills openui pm-pdlc-conductor pm-skills posthog prompt-architect promptfoo screenshot-to-code shadcn-ui spec-kit storybook --all" -- ${cur}) )
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
