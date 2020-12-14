# set up our dotfiles repo
if [ -n "$BASHPID" -o -n "$BASH_VERSION" ]; then
    DOTFILES_PATH="$(dirname $(dirname ${BASH_SOURCE[0]}))"
else
    DOTFILES_PATH="$(dirname $(dirname ${(%):-%N}))"
fi

# PATH modifications
# homebrew
PATH_HIGH="/usr/local/opt/coreutils/libexec/gnubin:$PATH_HIGH"
# this repo
PATH_HIGH="$DOTFILES_PATH/bin:$PATH_HIGH"

# do we have pyenv in ~/.pyenv
if [ -e ~/.pyenv ]; then
    export PYENV_ROOT="$HOME/.pyenv"
    PATH_HIGH="$PYENV_ROOT/bin:$PATH_HIGH"
fi

# add our locally compiled man files
MANPATH=$HOME/man:$MANPATH

# if we're running on ubuntu, make an open() alias that uses `gio open`
if [ -e /etc/lsb-release ]; then
    open() {
        # suppress errors from Nautilus
        gio open "$@" 1> /dev/null
    }
fi

# add our SSH key to ssh agent
test -z "$TMUX" && ssh-add -K ~/.ssh/id_rsa 2>/dev/null || :

if [ -n "$ZSH_NAME" ]; then
    source $DOTFILES_PATH/shell/zsh.sh
else
	# don't put duplicate lines or lines starting with space in the history.
	# See bash(1) for more options
	HISTCONTROL=ignoredups:erasedups

	# append to the history file, don't overwrite it
	shopt -s histappend

	# make history / history file sizes a bit more generous
	HISTSIZE=100000
	HISTFILESIZE=100000

	# check the window size after each command and, if necessary,
	# update the values of LINES and COLUMNS.
	shopt -s checkwinsize

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
alias i2='ipython2 --TerminalInteractiveShell.confirm_exit=False'
alias i3='ipython3 --TerminalInteractiveShell.confirm_exit=False'
alias recon='git rebase --continue'
alias f='find *'

# fuzzy-finder settings
export FZF_DEFAULT_OPTS="--inline-info --height 40% --reverse --bind=change:top"
if [ -z "$FZF_DEFAULT_COMMAND" ]; then
	if which rg &> /dev/null; then
		export FZF_DEFAULT_COMMAND='rg --files --glob "!.git"'
	elif which ag &> /dev/null; then
		export FZF_DEFAULT_COMMAND='ag --hidden --ignore .git -g ""'
	elif [ -z "$FZF_WARNED" ]; then
        if which fzf >/dev/null; then
            echo 'WARNING: fzf works better with rg or ag installed' >&2
        fi
        export FZF_WARNED=1
	fi
fi

# make sure we include fuzzy-finder completion for these commands as well
if [ -n "$BASHPID" ]; then
	if which fzf &> /dev/null; then
		complete -F _fzf_path_completion -o default -o bashdefault n
		complete -F _fzf_path_completion -o default -o bashdefault v
		complete -F _fzf_path_completion -o default -o bashdefault j
	fi
fi

dex() {
    local search="$1"
    shift
    docker exec -ti $(docker ps -qf ancestor="$search") "$@"
}

# register a python/click based script for completion generation
__click_completion=""
want_click_completion() {
    __click_completion="$__click_completion $*"
}

unset PATH_MODIFIED

# this function should be the last thing in your .bashrc/.zshrc
shell_init_done() {
    completions_zsh="$HOME/.completions.zsh.sh"
    completions_bash="$HOME/.completions.bash.sh"

    if [ -n "$ZSH_NAME" ]; then
        completions="$completions_zsh"
    else
        completions="$completions_bash"
    fi

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

    # empty the completions file(s)
    : > "$completions_bash"
    : > "$completions_zsh"

    for cmd in $(echo $__click_completion); do
        echo "Generating Bash/Zsh completions for $cmd ..."
        if which $cmd > /dev/null; then
            echo "# Completions for $cmd ..." >> "$completions_bash"
            echo "# Completions for $cmd ..." >> "$completions_zsh"
            upper=$(echo $cmd | tr '[:lower:]' '[:upper:]')
            eval "_${upper}_COMPLETE=source $cmd" >> "$completions_bash"
            eval "_${upper}_COMPLETE=source_zsh $cmd" >> "$completions_zsh"
            echo >> "$completions_bash"
            echo >> "$completions_zsh"
        fi
    done

    # source the correct completions file for our shell
    source "$completions"
}

nudge-watch() {
    socket="$1"
    shift
    echo "WAITING FOR $socket"
    nudge -l "$socket" || return 1
    clear
    date
}

rmempty() {
    find "$@" -type d -empty | while read d; do
        echo "rmdir $d"
        rmdir "$d"
    done
}
