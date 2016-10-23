" .vimproject stuff
augroup VimProject
augroup end
au! VimProject BufRead * call <SID>FindVimProject()

let s:sourced = {}

function! <SID>FindVimProject()
  " look for a .vimproject relative to the current file and source it
  let l:where = expand('%:p:h')
  while strlen(l:where) > 2
    let l:projectrtp = l:where . '/.vimproject'
    let l:vimrc = l:projectrtp . '/vimrc.vim'
    if filereadable(l:vimrc)
      let b:project = l:projectrtp
      if ! get(s:sourced, l:vimrc)
        exe 'source' l:vimrc
        let s:sourced[l:vimrc] = 1
      endif
      call <SID>SetupAutocmds(l:projectrtp)
      call <SID>LocalFTPlugin(l:projectrtp)
      return
    endif
    let l:where = fnamemodify(l:where, ':h')
  endwhile
endfunction

function! <SID>SetupAutocmds(projectrtp)
  " - set up autocmd's such that ftplugin and after/ftplugin files are sourced
  exe printf("au! VimProject BufRead %s/** call <SID>LocalFTPlugin('%s')", a:projectrtp, a:projectrtp)
  "   when editing the files
  " - anything else? No I don't think so ...
endfunction


function! <SID>LocalFTPlugin(projectrtp)
  let l:ext = expand('<afile>:e')
  let l:ftplugin = a:projectrtp . '/ftplugin/' . l:ext . '.vim'
  if filereadable(l:ftplugin)
    exe 'source' l:ftplugin
  endif
endfunction
