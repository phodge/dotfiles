" create our autocmd group
augroup gitmagic
augroup end

" Abort loading if we don't have necessary features.
" You can test if gitmagic is in a working state by wrapping your code in:
"
"   if gitmagic#loaded
"     ...
"   endif
"
let gitmagic#loaded = 0
if !exists('*win_getid')
  finish
endif
let gitmagic#loaded = 1

fun! gitmagic#ShowIndex()
  return <SID>ShowGitLog('git diff --cached')
endfun

fun! gitmagic#ShowRef(ref)
  return <SID>ShowGitLog('git log -p -1 '.a:ref)
endfun

let s:previewwindows = {}

fun! <SID>ShowGitLog(gitcmd)
  let l:mainbuf = bufnr('')
  let l:preview_win_id = get(s:previewwindows, l:mainbuf, 0)
  if l:preview_win_id
    " destroy the window we were using to preview the thing
    try
      let l:winnr = win_id2win(l:preview_win_id)
      if l:winnr
        exe l:winnr.'close'
      endif
    finally
      unlet s:previewwindows[l:mainbuf]
    endtry
  endif

  " make a new window for viewing the file contents
  let l:oldwin = win_getid()
  rightbelow vnew
  let s:previewwindows[l:mainbuf] = win_getid()
  try
    setlocal buftype=nofile bufhidden=wipe
    exe 'read !'.a:gitcmd
    silent! exe 'file '.fnameescape(a:gitcmd)
    setfiletype git
    normal! ggdd
    setlocal readonly nomodifiable

    " set up an autocmd to self-destruct this window when it is the last
    " window left
    au! gitmagic WinEnter <buffer> if winnr('$') == 1 | close | endif

    redraw!
  finally
    " jump back to the original window
    call win_gotoid(l:oldwin)
  endtry
endfun
