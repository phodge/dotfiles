nnoremap <buffer> <cr> :call <SID>ShowRev()<CR>
com! -nargs=0 -buffer RebaseAddSeparator call <SID>AddSeparator()

let s:rebase_py = expand('<sfile>:p:h') . '/gitrebase.py'

" jump down to "REVIEW BELOW" line if it is present
call search('REVIEW BELOW', 'c')

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
    let l:python3 = get(g:, 'python3_host_prog', 'python3')
    let l:cmd = [l:python3, s:rebase_py, bufnr(''), l:ref]
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

let s:chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

fun! <SID>AddSeparator()
  let l:curpos = getcurpos()
  try
    " check to see what "exec touch ..." lines already exist in the file
    let l:exectouch = {}
    for l:linenr in range(1, line('$'))
      let l:line = getline(l:linenr)
      if l:line =~ '^exec touch [A-Z] '
        let l:char = strpart(l:line, 11, 1)
        let l:exectouch[l:char] = 1
      endif
    endfor

    echo l:exectouch

    for l:char in split(s:chars, '\zs')
      " check to see if there is already an "exec touch ..." line for this
      " character
      if get(l:exectouch, l:char)
        continue
      endif

      " if the file has already been created, don't use it again
      if filereadable(l:char)
        continue
      endif

      " add an exec line for this file
      let l:newline = 'exec touch %s && git add %s && git commit -m "===== SEPARATOR ====="'
      call setpos('.', l:curpos)
      call append(line('.'), printf(l:newline, l:char, l:char))
      return
    endfor

    echoerr 'No separator file available'
  finally
    call setpos('.', l:curpos)
  endtry
endfun
