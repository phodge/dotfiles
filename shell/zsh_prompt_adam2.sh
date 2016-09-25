# === git repo info ===

# Default values for the appearance of the prompt. Configure at will.
ZSH_THEME_GIT_PROMPT_PREFIX="%B%F{black}["
ZSH_THEME_GIT_PROMPT_SUFFIX="%B%F{black}]"
ZSH_THEME_GIT_PROMPT_SEPARATOR="%B%F{black}|"
ZSH_THEME_GIT_PROMPT_BRANCH="%{$fg_bold[green]%}"
ZSH_THEME_GIT_PROMPT_MASTER="%{$fg_bold[red]%}"
ZSH_THEME_GIT_PROMPT_STAGED="%{$fg[green]%}%{●%G%}"
ZSH_THEME_GIT_PROMPT_CONFLICTS="%{$fg[red]%}%{≠%G%}"
ZSH_THEME_GIT_PROMPT_CHANGED="%{$fg[red]%}%{⚡%G%}"
ZSH_THEME_GIT_PROMPT_BEHIND="%{$fg[red]↓%G%}"
ZSH_THEME_GIT_PROMPT_AHEAD="%{$fg[green]↑%G%}"
ZSH_THEME_GIT_PROMPT_UNTRACKED="%{$fg[yellow]…%G%}"
ZSH_THEME_GIT_PROMPT_CLEAN="%{$fg_bold[green]%}%{✔%G%}"
ZSH_THEME_GIT_PROMPT_CACHE="true"

# ↑ ✔ green
# ↓ ⚡  red
# ♦ … ≠ ":" yellow
# [$branch|status|remote]

function zsh_prompt_gitinfo() {
    precmd_update_git_vars
    if [ -n "$__CURRENT_GIT_STATUS" ]; then
        if [[ "$GIT_BRANCH" == "master" ]]; then
            STATUS="$ZSH_THEME_GIT_PROMPT_PREFIX$ZSH_THEME_GIT_PROMPT_MASTER$GIT_BRANCH%{${reset_color}%}"
        else
            STATUS="$ZSH_THEME_GIT_PROMPT_PREFIX$ZSH_THEME_GIT_PROMPT_BRANCH$GIT_BRANCH%{${reset_color}%}"
        fi
        STATUS="$STATUS$ZSH_THEME_GIT_PROMPT_SEPARATOR"
        if [ "$GIT_STAGED" -ne "0" ]; then
            STATUS="$STATUS$ZSH_THEME_GIT_PROMPT_STAGED%{${reset_color}%}$GIT_STAGED"
        fi
        if [ "$GIT_UNTRACKED" -ne "0" ]; then
            STATUS="$STATUS$ZSH_THEME_GIT_PROMPT_UNTRACKED%{${reset_color}%}"
        fi
        if [ "$GIT_CONFLICTS" -ne "0" ]; then
            STATUS="$STATUS$ZSH_THEME_GIT_PROMPT_CONFLICTS%{${reset_color}%}$GIT_CONFLICTS"
        fi
        if [ "$GIT_CHANGED" -ne "0" ]; then
            STATUS="$STATUS$ZSH_THEME_GIT_PROMPT_CHANGED%{${reset_color}%}$GIT_CHANGED"
        fi
        if [ "$GIT_CHANGED" -eq "0" ] && [ "$GIT_CONFLICTS" -eq "0" ] && [ "$GIT_STAGED" -eq "0" ] && [ "$GIT_UNTRACKED" -eq "0" ]; then
            STATUS="$STATUS$ZSH_THEME_GIT_PROMPT_CLEAN"
        fi
        STATUS="$STATUS$ZSH_THEME_GIT_PROMPT_SEPARATOR"
        if [ "$GIT_BEHIND" -ne "0" ]; then
            STATUS="$STATUS$ZSH_THEME_GIT_PROMPT_BEHIND%{${reset_color}%}$GIT_BEHIND"
        fi
        if [ "$GIT_AHEAD" -ne "0" ]; then
            STATUS="$STATUS$ZSH_THEME_GIT_PROMPT_AHEAD%{${reset_color}%}$GIT_AHEAD"
        fi
        if [ "$GIT_BEHIND" -eq "0" ] && [ "$GIT_AHEAD" -eq "0" ]; then
            STATUS="$STATUS$ZSH_THEME_GIT_PROMPT_CLEAN%{${reset_color}%}"
        fi
        STATUS="$STATUS%{${reset_color}%}$ZSH_THEME_GIT_PROMPT_SUFFIX"
        echo "$STATUS"
    fi
}

# === hg repo info ===

function zsh_prompt_hginfo() {
    local state="$(hg_fast_state)"
    if [ -n "$state" ]; then
        echo "%F{yellow}[$state]%{${reset_color}%}"
    fi
}


# === other prompt segment functions ===

zsh_prompt_shortpath() {
    echo '%~'
}

zsh_prompt_userathost() {
    echo "%B%F{$prompt_adam2_color3}%n%b%F{$prompt_adam2_color2}@%B%F{$prompt_adam2_color3}%m"
}

zsh_prompt_clock() {
    echo '%B%F{yellow}%D{%H:%M}'
}

zsh_prompt_jobcount() {
    echo "%1(j/$prompt_l_sqparen%B%F{blue}bg:%j$prompt_r_sqparen/)"
}

zsh_prompt_laststatus() {
    echo "%(?//$prompt_l_sqparen%B%F{red}%?$prompt_r_sqparen)"

}



# === set up prompts ===

# Setup vim mode
function zle-line-init zle-keymap-select {
    PS1="$prompt_gfx_bbox"

    # get text from megaprompt plugins
    for func in $zsh_prompt_lprompt_segments; do
        PS1="$PS1$($func)"
    done

    PS1="$PS1%b%F{white}$prompt_char %b%f%k"

    VIM_PROMPT="$prompt_l_sqparen%b%F{yellow}NORMAL$prompt_r_sqparen"
    RPROMPT="${${KEYMAP/vicmd/$VIM_PROMPT}/(main|viins)/}"
    for func in $zsh_prompt_rprompt_segments; do
        RPROMPT="$RPROMPT$($func)"
    done

    zle reset-prompt
}

prompt_adam2_setup () {
    # Some can't be local
    local prompt_gfx_tlc prompt_gfx_mlc prompt_gfx_blc

    prompt_start=$'%{\e(0%}'
    prompt_end=$'%{\e(B%}'
    prompt_gfx_tlc=$prompt_start$'\x6c'$prompt_end
    prompt_gfx_mlc=$prompt_start$'\x78'$prompt_end
    prompt_gfx_blc=$prompt_start$'\x6d'$prompt_end
    prompt_gfx_hyphen=$'\x71'
    local phyph=$prompt_start$prompt_gfx_hyphen$prompt_end

    prompt_adam2_color1=${zsh_prompt_color_line-'green'}
    # Colour scheme
    prompt_adam2_color2=${zsh_prompt_color_heading-grey}   # current directory
    prompt_adam2_color3=${zsh_prompt_color_user-white}    # user@host
    prompt_adam2_color4=${4:-'white'}   # user input

    prompt_gfx_tbox="%B%F{$prompt_adam2_color1}${prompt_gfx_tlc}%b%F{$prompt_adam2_color1}${phyph}"
    prompt_gfx_bbox="%B%F{$prompt_adam2_color1}${prompt_gfx_blc}%b%F{$prompt_adam2_color1}${phyph}"

    # This is a cute hack.  Well I like it, anyway.

    prompt_l_paren="%B%F{246}("
    prompt_r_paren="%B%F{246})"
    prompt_l_sqparen="%B%F{246}["
    prompt_r_sqparen="%B%F{246}]"

    local tl=
    for func in $zsh_prompt_topleft_segments; do
        txt="$($func)"
        if [ -n "$txt" ]; then
            if [ -n "$tl" ]; then
                # add pipe between sections
                tl="$tl%B%F{245}|"
            fi
            tl="${tl}%B%F{$prompt_adam2_color2}$txt"
        fi
    done

    local tr=
    for func in $zsh_prompt_topright_segments; do
        txt="$($func)"
        if [ -n "$txt" ]; then
            if [ -n "$tr" ]; then
                # add pipe between sections
                tr="$tr%B%F{246}|"
            fi
            tr="${tr}%B%F{$zsh_prompt_color_heading}$txt"
        fi
    done
    if [ -n "$tr" ]; then
        tr="%B%F{246}[$tr%B%F{246}]"
    fi

    prompt_line_1a="$prompt_gfx_tbox$prompt_l_paren$tl$prompt_r_paren%b%F{$prompt_adam2_color1}"
    prompt_line_1b="$tr%b%F{$prompt_adam2_color1}${phyph}"

    prompt_char="%(!.#.>)"

    prompt_opts=(cr subst percent)

}

precmd() {
    local prompt_line_1

    prompt_adam2_choose_prompt

    print -rP "$prompt_line_1"
    PS1="$prompt_line_2%b%F{white}$prompt_char %b%f%k"
    PS2="$prompt_line_2$prompt_gfx_bbox_to_mbox%b%F{white}%_> %b%f%k"
    PS3="$prompt_line_2$prompt_gfx_bbox_to_mbox%b%F{white}?# %b%f%k"

    zle_highlight[(r)default:*]="default:fg=$prompt_adam2_color4"

    jerjerrod_clearcache_now &> /dev/null
}

prompt_adam2_choose_prompt () {
    local prompt_line_1a_width=${#${(S%%)prompt_line_1a//(\%([KF1]|)\{*\}|\%[Bbkf])}}
    local prompt_line_1b_width=${#${(S%%)prompt_line_1b//(\%([KF1]|)\{*\}|\%[Bbkf])}}

    local prompt_padding_size=$(( COLUMNS
    - prompt_line_1a_width
    - prompt_line_1b_width ))

    # Try to fit in long path and user@host.
    if (( prompt_padding_size > 0 )); then
        local prompt_padding
        eval "prompt_padding=\${(l:${prompt_padding_size}::${prompt_gfx_hyphen}:)_empty_zz}"
        prompt_line_1="$prompt_line_1a$prompt_start$prompt_padding$prompt_end$prompt_line_1b"
        return
    fi

    prompt_padding_size=$(( COLUMNS - prompt_line_1a_width ))

    # Didn't fit; try to fit in just long path.
    if (( prompt_padding_size > 0 )); then
        local prompt_padding
        eval "prompt_padding=\${(l:${prompt_padding_size}::${prompt_gfx_hyphen}:)_empty_zz}"
        prompt_line_1="$prompt_line_1a$prompt_start$prompt_padding$prompt_end"
        return
    fi

    # Still didn't fit; truncate
    local prompt_pwd_size=$(( COLUMNS - 5 ))
    prompt_line_1="$prompt_gfx_tbox$prompt_l_paren%B%F{$prompt_adam2_color2}%$prompt_pwd_size<...<%~%<<$prompt_r_paren%b%F{$prompt_adam2_color1}$prompt_start$prompt_gfx_hyphen$prompt_end"
}

# default segments for each section
zsh_prompt_topleft_segments=( zsh_prompt_userathost zsh_prompt_shortpath )
zsh_prompt_topright_segments=( zsh_prompt_clock )
zsh_prompt_rprompt_segments=( zsh_prompt_gitinfo zsh_prompt_hginfo )
zsh_prompt_lprompt_segments=( zsh_prompt_jobcount zsh_prompt_laststatus )


prompt_adam2_setup
