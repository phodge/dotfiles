" use K and CTRL+K for comment/uncomment
if exists('g:vim_peter')
  noremap <buffer> <silent>     K :call <SID>AddComment()<CR>j
  noremap <buffer> <silent> <C-K> :call <SID>DelComment()<CR>j
else
  silent! nunmap <buffer>     K
  silent! nunmap <buffer> <C-K>
endif

function! <SID>AddComment() " {{{
  s,^\(\s*\)\@>\(--\)\@!\ze\S,\1--,e
endfunction " }}}
function! <SID>DelComment() " {{{
  " try not to move the cursor
  let l:pos = getpos('.')
  s,^\(\s*\)\@>--\ze\S,\1,e
  " if cursor is on the same line, move it back to where it was
  if getpos('.')[0] == l:pos[0]
    call setpos('.', l:pos)
  endif
endfunction " }}}
