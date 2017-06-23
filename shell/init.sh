# set up our dotfiles repo
if [ -n "$BASHPID" ]; then
    DOTFILES_PATH="$(dirname $(dirname ${BASH_SOURCE[0]}))"
else
    DOTFILES_PATH="$(dirname $(dirname ${(%):-%N}))"
fi

# PATH modifications
PATH_HIGH="$DOTFILES_PATH/bin:$PATH_HIGH"

# add our locally compiled man files
MANPATH=$HOME/man:$MANPATH

# add our SSH key to ssh agent
test -z "$TMUX" && ssh-add -K ~/.ssh/id_rsa 2>/dev/null || :

# function to quickly get hg branch name and status - used in zsh prompt and bash prompt
hg_fast_state() {
    here="$(realpath "$PWD")"
    while [ -n "$here" -a / != "$here" ]; do
        if [ -e "$here/.hg" ]; then
            fast-hg-status
            cat "$here/.hg/branch"
            return
        fi
        here="$(dirname "$here")"
    done
}

if [ -n "$ZSH_NAME" ]; then
    source $DOTFILES_PATH/shell/zsh.sh
else
    shopt -s histappend

    if [ -e $HOME/src/git-completion.bash ]; then
        source $HOME/src/git-completion.bash
    fi
    source $DOTFILES_PATH/shell/bash_prompt_wizard.sh
fi

EDITOR=vim
which nvim &> /dev/null && EDITOR=nvim
export EDITOR

in_git_repo() {
    here="$(realpath "$PWD")"
    while [ -n "$here" -a / != "$here" ]; do
        if [ -e "$here/.git" ]; then
            return 0
        fi
        here="$(dirname "$here")"
    done
    return 1
}

show_status() {
    if in_git_repo; then
        git status
    else
        hg status
    fi
}

show_status_long() {
    if in_git_repo; then
        git diff --cached
    else
        echo "Git staging area not available" >&2
        return 1
    fi
}

edit_status() {
    if in_git_repo; then
        $EDITOR +"au VimEnter * nested Gstatus | bw 1"
    else
        $EDITOR +"Shell hg status" +"bw 1"
    fi
}

# custom aliases
alias l='ls -lah --color=always'
alias ll='ls -lah --color=always'
alias v=vim
alias n=nvim
alias rm='rm -i'
alias mv='mv -i'
alias cp='cp -i'
alias j=jerjerrod
alias s=show_status
alias ss=show_status_long
alias g=edit_status
alias i2='ipython2 --TerminalInteractiveShell.confirm_exit=0'
alias i3='ipython3 --TerminalInteractiveShell.confirm_exit=0'



# register a python/click based script for completion generation
__click_completion="homely"
want_click_completion() {
    __click_completion="$__click_completion $*"
}

# this function should be the last thing in your .bashrc/.zshrc
shell_init_done() {
    completions="$HOME/.completions.sh"

    # modify PATH now if it hasn't been done yet
    if [ -z "$PATH_MODIFIED" ]; then
        export PATH_MODIFIED=1
        PATH="$PATH_HIGH""$PATH"
    fi

    # is the file is present and less than 4 hours old, use it
    if find "$completions" -cmin -240 &> /dev/null; then
        source "$completions"
        return
    fi

    # empty the completions file
    : > "$completions"

    for cmd in $(echo $__click_completion); do
        echo "Generating completions for $cmd ..."
        if which $cmd &> /dev/null; then
            echo "# Completions for $cmd ..." >> "$completions"
            upper=$(echo $cmd | tr '[:lower:]' '[:upper:]')
            eval "_${upper}_COMPLETE=source $cmd" >> "$completions"
            echo >> "$completions"
        fi
    done

    source "$completions"
}
