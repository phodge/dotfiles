# user should customise these with his own list of awesome things
prompt_wizard_plugins_line1="bash_wizard_who bash_wizard_path"
if which git &>/dev/null; then
    prompt_wizard_plugins_line1="$prompt_wizard_plugins_line1 bash_wizard_gitbranch"
fi
if which fast-hg-status &> /dev/null; then
    prompt_wizard_plugins_line1="$prompt_wizard_plugins_line1 bash_wizard_hgbranch"
fi
prompt_wizard_plugins_line2="bash_wizard_jobcount bash_wizard_exitcode bash_wizard_prompt"

if [ -z "$wizard_prompt_color_primary" ]; then
	wizard_prompt_color_primary=gray
fi
if [ -z "$wizard_prompt_color_secondary" ]; then
	wizard_prompt_color_secondary=palegray
fi

PS1='`LAST_EXIT=$?;__generate_bash_prompt`'

__generate_bash_prompt() {
    local  reset='\001\e[0m\002'

    local   bold='\001\e[1m\002'
    local    dim='\001\e[2m\002'
    local  under='\001\e[4m\002'
    local  blink='\001\e[5m\002'
    local invert='\001\e[6m\002'
    local   hide='\001\e[7m\002'

    local    black='\001\e[30m\002'
    local      red='\001\e[31m\002'
    local    green='\001\e[32m\002'
    local   yellow='\001\e[33m\002'
    local     blue='\001\e[34m\002'
    local     pink='\001\e[35m\002'
    local     cyan='\001\e[36m\002'
    local palegray='\001\e[37m\002'

    local       gray='\001\e[90m\002'
    local    palered='\001\e[91m\002'
    local  palegreen='\001\e[92m\002'
    local paleyellow='\001\e[93m\002'
    local   paleblue='\001\e[94m\002'
    local   palepink='\001\e[95m\002'
    local   palecyan='\001\e[96m\002'
    local      white='\001\e[97m\002'

    local    warning='\001\e[41m\e[97m\002'

    prompt_color_primary=${!wizard_prompt_color_primary-$white}
    prompt_color_secondary=${!wizard_prompt_color_secondary-$reset}

    for func in $prompt_wizard_plugins_line1; do
        $func
    done
    echo
    for func in $prompt_wizard_plugins_line2; do
        $func
    done
    echo -ne "$reset"
}

bash_wizard_who() {
    echo -ne "$prompt_color_primary[$prompt_color_secondary$USER"
    echo -ne "$prompt_color_primary@$prompt_color_secondary`hostname`"
    echo -ne "$prompt_color_primary] $reset"
}
bash_wizard_path() {
    echo -ne "$gray"
    echo -n "${PWD/$HOME/~} "
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
        echo -ne "$blue{$count} "
    fi
}
bash_wizard_exitcode() {
    if [ 0 != $LAST_EXIT ]; then
        echo -en "${red}"
        echo -en "${LAST_EXIT}! "
    fi
}
bash_wizard_prompt() {
    echo -ne "$prompt_color_primary\$ "
}
