# bash completion for mykit

_mykit_completions() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    opts="list setup stats env stack mcp install remove sync prefetch reset update lint dedupe doctor completion"

    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    case "${prev}" in
        stack)
            COMPREPLY=( $(compgen -W "use set list edit" -- ${cur}) )
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
            COMPREPLY=( $(compgen -W "db-helper ecc-suite mengto-skills prompt-architect --global --all" -- ${cur}) )
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
