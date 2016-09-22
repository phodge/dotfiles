if type add-zsh-hook &> /dev/null && which jerjerrod &> /dev/null; then
    __wantclear=
    jerjerrod_clearcache() {
        jerjerrod_clearcache_now
        expanded="$3"
        if echo "$expanded" | grep '^\(git\|hg\) ' &> /dev/null; then
            __wantclear=1
        fi
    }
    add-zsh-hook preexec jerjerrod_clearcache

    jerjerrod_clearcache_now() {
        if [ -n "$__wantclear" ]; then
            jerjerrod clearcache --local "$PWD"
            echo "CLEARING"
            __wantclear=
        fi
    }

    export PS1='`jerjerrod_clearcache_now`'"$PS1"
fi
