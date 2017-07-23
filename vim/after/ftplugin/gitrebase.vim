nnoremap <buffer> <cr> :call <SID>ShowRev()<CR>

fun! <SID>ShowRev()
  " what rev do we want
  let l:line = getline('.')
  let l:ref = matchstr(l:line, '^\S*\s\+\zs\w\+')
  if l:ref == ''
    echoerr "Couldn't determine rev number on this line"
    return
  endif

  return gitmagic#ShowRef(l:ref)
endfun

