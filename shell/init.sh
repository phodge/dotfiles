# set up our dotfiles repo
if [ -n "$BASHPID" ]; then
    DOTFILES_PATH="$(dirname $(dirname ${BASH_SOURCE[0]}))"
else
    DOTFILES_PATH="$(dirname $(dirname ${(%):-%N}))"
fi

# PATH modifications
PATH="$DOTFILES_PATH/bin:$PATH"

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
