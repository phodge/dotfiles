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

export EDITOR=vim

# custom aliases
alias l='ls -lah --color=always'
alias ll='ls -lah --color=always'
alias v=vim
alias n=nvim
alias rm='rm -i'
alias mv='mv -i'
alias cp='cp -i'
alias j=jerjerrod
