let s:dotfiles_repo = fnamemodify(resolve(expand('<sfile>')), ':h:h:h')

fun! <SID>ReloadSkills()
  call InTmuxWindow('homely update ' . shellescape(s:dotfiles_repo) . ' --nopull -o agent_skills',
        \ {'name': 'reload_agent_skills', 'reuse': v:true})
endfun

aug AutoReloadSkills
exe 'au! BufWritePost ' . s:dotfiles_repo . '/skills/*/SKILL.md call <SID>ReloadSkills()'
aug end
