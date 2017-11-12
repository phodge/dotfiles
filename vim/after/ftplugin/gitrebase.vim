nnoremap <buffer> <cr> :call <SID>ShowRev()<CR>

let s:rebase_py = expand('<sfile>:p:h') . '/gitrebase.py'

fun! <SID>ShowRev()
  " what rev do we want
  let l:line = getline('.')
  let l:ref = matchstr(l:line, '^\S*\s\+\zs\w\+')
  if l:ref == ''
    echoerr "Couldn't determine rev number on this line"
    return
  endif


  " kick off our python script to add marks
  if has('nvim')
    let l:cmd = ['python3', s:rebase_py, bufnr(''), l:ref]
    call jobstart(l:cmd, {'rpc': v:true, 'on_stderr': funcref('<SID>OutputHandler')})
  endif

  return gitmagic#ShowRef(l:ref)
endfun

function! <SID>OutputHandler(jobid, lines, eventtype)
  if a:eventtype == 'stderr'
    let l:nvimlog = expand('~/.nvimlog')
    for l:line in a:lines
      silent exe printf('!echo %s >> %s', shellescape(l:line), l:nvimlog)
    endfor
  endif
endfun
