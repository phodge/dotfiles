# set up our dotfiles repo
if [ -n "$BASHPID" -o -n "$BASH_VERSION" ]; then
    DOTFILES_PATH="$(dirname $(dirname ${BASH_SOURCE[0]}))"
else
    DOTFILES_PATH="$(dirname $(dirname ${(%):-%N}))"
fi

test -z "$ZSH_SHOW_GIT_STATE" && export ZSH_SHOW_GIT_STATE=1
if [ "$ZSH_SHOW_GIT_STATE" != "1" ]; then
    # set the old flag
    export ZSHNOGIT=1
fi

if echo $HOME | grep -q ^/Users/; then
    export IS_MACOS=1
else
    export IS_MACOS=
fi

# PATH modifications
if [[ $IS_MACOS ]]; then
    # homebrew
    PATH_HIGH="/usr/local/opt/coreutils/libexec/gnubin:$PATH_HIGH"
fi
# this repo
PATH_HIGH="$DOTFILES_PATH/bin:$PATH_HIGH"
PATH_HIGH="$DOTFILES_PATH/reference-repository-utils.git/bin:$PATH_HIGH"

# have pipx install stuff directly into $HOME/bin on macos
if [[ $IS_MACOS ]]; then
    export PIPX_BIN_DIR="$HOME/bin"
fi

# do we have pyenv in ~/.pyenv
if [ -e ~/.pyenv ]; then
    export PYENV_ROOT="$HOME/.pyenv"
    PATH_HIGH="$PYENV_ROOT/bin:$PATH_HIGH"
fi

if [ -e ~/.cargo ]; then
    PATH_HIGH="$HOME/.cargo/bin:$PATH_HIGH"
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
# XXX: on ubuntu 22.04 this adds a 'Enter PIN for authenticator' prompt to
# shell startup so maybe we don't want this?
if [[ $IS_MACOS ]]; then
    test -z "$TMUX" && test -e ~/.ssh/id_rsa && ssh-add -K ~/.ssh/id_rsa 2>/dev/null || :
fi

if [ -n "$ZSH_NAME" ]; then
    source $DOTFILES_PATH/shell/zsh.sh
else
	# don't put duplicate lines or lines starting with space in the history.
	# See bash(1) for more options
	HISTCONTROL=ignoredups:erasedups

	# append to the history file, don't overwrite it
	shopt -s histappend

	# check the window size after each command and, if necessary,
	# update the values of LINES and COLUMNS.
	shopt -s checkwinsize

    if [ -e $HOME/src/git-completion.bash ]; then
        source $HOME/src/git-completion.bash
    fi
    source $DOTFILES_PATH/shell/bash_prompt_wizard.sh
fi

# Note: we want to do this for bash _and_ zsh so that we don't accidentally
# trim history file down when running bash
export HISTSIZE=1000000
export SAVEHIST=1000000

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
        $EDITOR +"au VimEnter * nested Git | bw 1"
    else
        $EDITOR +"Shell hg status" +"bw 1"
    fi
}

# custom aliases
alias l='ls -lah --color=always'
alias ll='ls -lah --color=always'
alias v=vim
alias n=nvim
alias n2='NVIM_TS_LSP=1 nvim'
alias rm='rm -i'
alias mv='mv -i'
alias cp='cp -i'
alias j=jerjerrod
alias s=show_status
alias ss=show_status_long
alias g=edit_status
alias i2='ipython2 --TerminalInteractiveShell.confirm_exit=False'
alias i3='ipython3 --TerminalInteractiveShell.confirm_exit=False'
alias recon='git -c core.hooksPath=/no/hooks rebase --continue'
if [[ $WANT_GIT_REVISE = 1 ]]; then
    alias rebas='git -c core.hooksPath=/no/hooks revise -e -i'
else
    alias rebas='git -c core.hooksPath=/no/hooks rebase -i'
fi
alias f='find *'
alias c='git commit'
alias ca='git commit --amend'
alias cnv='git commit --no-verify'
alias canv='git commit --amend --no-verify'
alias co='git checkout'
alias dc='docker-compose'
alias gf='git fetch -p'
alias gp='git pull --rebase'
alias gP='git push'


irebas() {
    while :; do
        rebas -i "$@" && continue
        return $?
    done
}

# tell ripgrep where to find its RC file
export RIPGREP_CONFIG_PATH="$DOTFILES_PATH/.ripgreprc"

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
    # modify PATH now if it hasn't been done yet
    if [ -z "$PATH_MODIFIED" ]; then
        export PATH_MODIFIED=1
        PATH="$PATH_HIGH""$PATH"
    fi

    shell_init_completions

    shell_post_init
}

shell_init_completions() {
    completions_zsh="$HOME/.completions.zsh.sh"
    completions_bash="$HOME/.completions.bash.sh"

    if [ -n "$ZSH_NAME" ]; then
        completions="$completions_zsh"
    else
        completions="$completions_bash"
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
    local removed_some=0
    find "$@" -type d -empty | while read d; do
        echo "rmdir $d"
        rmdir "$d"
        removed_some=1
    done

    if [ $removed_some -eq 1 ]; then
        for arg in "$@"; do
            # try again for any arg that still exists
            test -d "$arg" && rmempty "$arg"
        done
    fi
}

pushthis() {
    local ref="$1";
    shift
    local choice=

    if [ -z "$PUSHTO" ]; then
        while [ -z "$choice" ]; do
            echo -n "Dest branch: "
            read choice
        done
        PUSHTO="$choice"
    else
        echo -n "Dest branch [$PUSHTO]: "
        read choice
        if [ -n "$choice" ]; then
            PUSHTO="$choice"
        fi
    fi

    echo "$ git push origin '${ref}:refs/heads/$PUSHTO' '$@'"
    git push origin "${ref}:refs/heads/$PUSHTO" "$@"
}
fpushthis() {
    local ref="$1"
    shift
    pushthis "$ref" --force-with-lease "$@"
}

__peter_fnm_init() {
    which fnm &>/dev/null || return

    if [ -n "$ZSH_NAME" ]; then
        eval $(fnm env)
    elif [ -n "$BASHPID" ]; then
        # bash needs fnm completions installed on startup
        eval "$(fnm completions --shell bash)"
        eval $(fnm env)
    fi
}

shell_post_init() {
    # initialise fnm for current shell if it is installed
    __peter_fnm_init

    for fn in $(echo $DOTFILES_POST_INIT); do
        $fn || echo "dotfiles init.sh POST-INIT ERROR: $fn() failed" >&2
        unset -f $fn 2>/dev/null || :
    done
    unset -f shell_post_init
}

countdown() {
    local seconds=$1
    shift
    local prefix="$1"
    shift

    while [ $seconds -gt 0 ]; do
        if [ $seconds -gt 59 ]; then
            let min=($seconds/60);
            let sec="($seconds-($min*60))"
            timestr="${min}m ${sec}s"
        else
            timestr="${seconds}s"
        fi
        echo "$prefix${timestr}!'"
        sleep 1
        let seconds=$seconds-1
    done
}

shell_then_hibernate() {
    if [[ $IS_MACOS ]]; then
        echo "shell_then_hibernate() does not work in MacOS" >&2
        return 1
    fi

    local me=$USER
    if [ "$#" -gt 0 ]; then
        cmd="$@"
    else
        cmd=$SHELL
    fi

    if [ -n "$SHELL_THEN_POWEROFF" ]; then
        hibernate_cmd="poweroff"
        verb="Shutdown"
    else
        hibernate_cmd="systemctl hibernate"
        verb="Hibernation"
    fi

    # Note the use of -E (--preserve-env) here so that commands like
    # 'caffeinate' have what they need to keep a system awake
    cmd2=''
    i=20
    while [ $i -gt 0 ]; do
        cmd2="$cmd2 echo '$verb in ${i}s!'; sleep 1;"
        let i=$i-1
    done
    sudo -E bash -ic "sudo -E -u $me bash -ic '$cmd'; $cmd2 $hibernate_cmd"
}
shell_then_poweroff() {
    export SHELL_THEN_POWEROFF=1
    shell_then_hibernate "$@"
}

# these mainly exist for tmux's <F4> + <S-F4> keyboard shortcuts
repo_todo_list_view() {
    nvim __no_file__ '+setlocal buftype=nofile' +RepoTodoList +1bw +redraw +messages
}
repo_todo_list_add() {
    nvim __no_file__ '+setlocal buftype=nofile' +RepoTodoList +1bw '+normal! G' +RepoTodoAdd
}
