# Quick bash code for mool commands auto completion. Works for bash and zsh.

__mool_cmds="do_build do_clean do_test do_test_changes"
__mool_ret_code=0

__echo_error() { echo -e "\033[31mError: $*\033[0m"; }

__mool_fetch_suggestions()
{
    local rule=${COMP_WORDS[COMP_CWORD]}

    # BUILD_ROOT should be set.
    if [ "${BUILD_ROOT}" == "" ]; then
        __echo_error "BUILD_ROOT is not set!"
        __mool_ret_code=1
        return
    fi

    # Rule prefix should always be mool.
    if ! [[ "$rule" =~ mool\..* ]]; then
        COMPREPLY=("mool.")
        return
    fi

    # Determine the partial valid rule name entered.
    local prefix_tokens=$(echo $rule | sed 's/\.[^\.]*$//g')

    # Make full path of directory.
    local relative_path=$(echo $prefix_tokens | sed 's/^mool//' | tr '.' '/')
    local dir_path="${BUILD_ROOT}${relative_path}"
    local bld_file="$dir_path/BLD"

    local ALL_DIRS BLD_RULES BLD_ALL_KEY
    if [ -d $dir_path ]; then
        ALL_DIRS=$(ls -l $dir_path | grep '^d' | awk '{print $NF}' | sed 's/$/./')
    fi
    if [ -f $bld_file ]; then
        BLD_RULES=$(cat $bld_file | grep '^"' | cut -d '"' -f 2)
        BLD_ALL_KEY="ALL"
    fi

    local suggestions=""
    for suggestion in $ALL_DIRS $BLD_RULES $BLD_ALL_KEY; do
        suggestions="$suggestions $prefix_tokens.$suggestion"
    done
    COMPREPLY=( $( compgen -W "$suggestions" -- $rule) )
}

__mool_autocomplete_main()
{
    local cur=${COMP_WORDS[COMP_CWORD]}
    local prev=${COMP_WORDS[COMP_CWORD-1]}
    local cmd=${COMP_WORDS[1]}
    __mool_ret_code=0

    case "$prev" in
        bu)
            COMPREPLY=( $( compgen -W "$__mool_cmds" -- $cur ) )
            return 0
            ;;
        do_clean)
            COMPREPLY=("")
            return 0
            ;;
        do_build | do_test)
            __mool_fetch_suggestions
            return $__mool_ret_code
            ;;
    esac

    # do_build and do_test can have multiple rules together. This is to help
    # completing rules after first rule.
    case "$cmd" in
        do_build | do_test)
            __mool_fetch_suggestions
            return $__mool_ret_code
            ;;
    esac
}

# Hack for zsh shell. It works in my zsh version 5.0.2 atleast.
# Needs to be checked for other versions.
if [[ -n ${ZSH_VERSION-} ]]; then
    autoload -U +X compinit && compinit
    autoload -U +X bashcompinit && bashcompinit
fi

complete -o nospace -o default -F __mool_autocomplete_main bu
