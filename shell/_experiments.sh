DEVICE_UUID=$(test -e $HOME/.config/experiments_uuid && cat $HOME/.config/experiments_uuid)

exp_unused() {
    export $1=0
}

_exp_reload() {
    source $HOME/dotfiles/experiments.sh
}

_exp_is_active() {
    local exp_name=$1
    if [ -n "$BASHPID" -o -n "$BASH_VERSION" ]; then
        # if feature has already been activated then we can bail out already
        test "${!exp_name}" = 1 && return
    else
        eval "local exp_value=\$${exp_name}"
        test "$exp_value" = 1 && return
    fi

    return 1
}

exp_by_device() {
    local exp_name=$1
    shift

    # bail out early if experiment is already active
    # XXX: this doesn't work - if we run exp_reload() then all environment
    # variables that are already turned can't be reset back to zero.
    _exp_is_active $exp_name && return

    export $exp_name=0
    for uuid in $@; do
        if test "$DEVICE_UUID" = "$uuid"; then
            export $exp_name=1
            break
        fi
    done
}

exp_reload() {
    echo "--- Reloading Experiments ---"
    _exp_reload
}
