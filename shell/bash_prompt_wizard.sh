# user should customise these with his own list of awesome things
prompt_wizard_plugins_line1="bash_wizard_who bash_wizard_path"
if which git &>/dev/null; then
    prompt_wizard_plugins_line1="$prompt_wizard_plugins_line1 bash_wizard_gitbranch"
fi
if which fast-hg-status &> /dev/null; then
    prompt_wizard_plugins_line1="$prompt_wizard_plugins_line1 bash_wizard_hgbranch"
fi
prompt_wizard_plugins_line2="bash_wizard_jobcount bash_wizard_exitcode bash_wizard_prompt"
prompt_wizard_plugins_line2="bash_wizard_prompt"

wizard_prompt_color_primary=
wizard_prompt_color_secondary=

PS1='`LAST_EXIT=$?;__generate_bash_prompt`'

__generate_bash_prompt() {
    local  reset='\e[0m'

    local   bold='\e[1m'
    local    dim='\e[2m'
    local  under='\e[4m'
    local  blink='\e[5m'
    local invert='\e[6m'
    local   hide='\e[7m'

    local    black='\e[30m'
    local      red='\e[31m'
    local    green='\e[32m'
    local   yellow='\e[33m'
    local     blue='\e[34m'
    local     pink='\e[35m'
    local     cyan='\e[36m'
    local palegray='\e[37m'

    local       gray='\e[90m'
    local    palered='\e[91m'
    local  palegreen='\e[92m'
    local paleyellow='\e[93m'
    local   paleblue='\e[94m'
    local   palepink='\e[95m'
    local   palecyan='\e[96m'
    local      white='\e[97m'

    local    warning='\e[41m\e[97m'

    prompt_color_primary=${!wizard_prompt_color_primary-$white}
    prompt_color_secondary=${!wizard_prompt_color_secondary-$reset}

    for func in $prompt_wizard_plugins_line1; do
        echo -n "$($func)"
    done
    echo
    for func in $prompt_wizard_plugins_line2; do
        echo -n "$($func)"
    done
}

bash_wizard_who() {
    echo -ne "$prompt_color_primary[$prompt_color_secondary$USER"
    echo -ne "$prompt_color_primary@$prompt_color_secondary`hostname`"
    echo -ne "$prompt_color_primary] $reset"
}
bash_wizard_path() {
    echo -ne "$gray"
    echo -n "${PWD/$HOME/\~} "
    echo -ne $reset
}
bash_wizard_hgbranch() {
    state="$(hg_fast_state)"
    if [ -n "$state" ]; then
        echo -ne "$palegreen[$(hg_fast_state)]$reset "
    fi
}
bash_wizard_gitbranch() {
    local branch=$(git branch --no-color 2>/dev/null | grep '^\*' | cut -b 3-)
    if [ -n "$branch" ]; then
        echo -ne "$green[$branch]"
        # also check if there is anything stashed
        local stashcount=$(git stash list 2>/dev/null | wc -l)
        if [ -n "$stashcount" -a "0" != "$stashcount" ]; then
            echo -ne "[$pink+$stashcount$green]"
        fi
        echo -ne "$reset "
    fi
}
bash_wizard_colortest() {
    # all the colours
    echo -ne "$black black$reset"
    echo -ne "$red red$reset"
    echo -ne "$green green$reset"
    echo -ne "$yellow yellow$reset"
    echo -ne "$blue blue$reset"
    echo -ne "$pink pink$reset"
    echo -ne "$cyan cyan$reset"
    echo -ne "$palegray palegray$reset"
    echo -ne "$gray gray$reset"
    echo -ne "$palered palered$reset"
    echo -ne "$palegreen palegreen$reset"
    echo -ne "$paleyellow paleyellow$reset"
    echo -ne "$paleblue paleblue$reset"
    echo -ne "$palepink palepink$reset"
    echo -ne "$palecyan palecyan$reset"
    echo -ne "$white white$reset"
}
bash_wizard_jobcount() {
    # need an extra "echo" inside to trim the whitespace off the zero
    local count=$(echo $(jobs | wc -l))
    if [ -n "$count" -a 0 != "$count" ]; then
        echo -ne "$blue{$count}$reset "
    fi
}
bash_wizard_exitcode() {
    if [ 0 != $LAST_EXIT ]; then
        echo -en "$red$LAST_EXIT!$reset "
    fi
}
bash_wizard_prompt() {
    echo -en "$prompt_color_primary\$$reset "
}
