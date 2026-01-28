# Save current allexport state and enable it
push_allexport() {
    case "$(set -o | grep allexport)" in
        *on)  __old_allexport=on  ;;
        *off) __old_allexport=off ;;
    esac
    set -o allexport
}

# Restore previous allexport state
pop_allexport() {
    if [ "$__old_allexport" = on ]; then
        set -o allexport
    else
        set +o allexport
    fi
    unset __old_allexport
}

# we do "source this_script.sh"
SCRIPT_DIR=$(dirname "${BASH_SOURCE[0]}")
pushd "$SCRIPT_DIR"
push_allexport
source .env
pop_allexport
popd

echo DB_NAME=$DB_NAME
