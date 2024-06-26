# === random zsh settings ===

# CTRL+U backspaces from the cursor to the start of the line, rather than destroying the entire line
bindkey \^U backward-kill-line


# Uncomment the following line to use case-sensitive completion.
CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion. Case
# sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment the following line to disable bi-weekly auto-update checks.
# DISABLE_AUTO_UPDATE="true"

# Uncomment the following line to change how often to auto-update (in days).
# export UPDATE_ZSH_DAYS=13

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
#ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
COMPLETION_WAITING_DOTS="true"

# set history colleciton options
unsetopt share_history
setopt histignorealldups
setopt histignorespace

# git completion for zsh.
# Instructions were found in git-completion.zsh itself
zstyle ':completion:*:*:git:*' script ~/src/git-completion.bash
fpath=(~/.zsh $fpath)


# ============================================================================
# antigen
source $HOME/src/antigen.git/antigen.zsh

# === oh-my-zsh ===

antigen use oh-my-zsh

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# === other plugins ===
antigen bundle git
antigen bundle mercurial
#antigen bundle colored-man-pages
antigen bundle zsh-users/zsh-syntax-highlighting

# we need to be able to disable this bundle altogether when disabling git status globally
if [ "$ZSH_SHOW_GIT_STATE" = "1" ]; then
    antigen bundle olivierverdier/zsh-git-prompt
fi

antigen apply


zsh_no_git() {
    ZSHNOGIT=1 zsh
}



# ============================================================================
# jerjerrod: zsh hook to reset caches on git/hg commands
if type add-zsh-hook &> /dev/null && which jerjerrod &> /dev/null; then
    __wantclear=
    jerjerrod_clearcache() {
        test -n "$ZSHNOGIT" && return

        expanded="$3"
        if echo "$expanded" | grep '^\(git\|hg\) ' &> /dev/null; then
            if ! echo "$expanded" | grep '^git rebase ' &> /dev/null; then
                __wantclear=1
            fi
        fi
        jerjerrod_clearcache_now
    }
    add-zsh-hook preexec jerjerrod_clearcache
    add-zsh-hook zshexit jerjerrod_clearcache_now

    jerjerrod_clearcache_now() {
        test -n "$ZSHNOGIT" && return

        if [ -n "$__wantclear" ]; then
            if [ -n "$JERJERROD_CLEAR_CACHE_IN_SHELL" ]; then
                echo "jerjerrod: Clearing cache now"
                jerjerrod clearcache --local "$PWD"
            fi
            __wantclear=
        fi
    }

    export PS1='`jerjerrod_clearcache_now`'"$PS1"
fi


# ============================================================================
# PROMPT
source $DOTFILES_PATH/shell/zsh_prompt_adam2.sh
