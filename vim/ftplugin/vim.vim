nnoremap <SPACE>h :call <SID>GotoHelp()<CR>

function! <SID>GotoHelp()
  let l:word = expand('<cword>')
  let l:synid = synID(line('.'), col('.'), 0)
  let l:synname = synIDattr(l:synid, 'name')
  if l:synname == 'vimFuncName'
    let l:topic = ' %s()'
  elseif l:synname == 'vimOption'
    let l:topic = "'%s'"
  else
    let l:topic = ':%s'
  endif
  execute 'help '.printf(l:topic, l:word)
  wincmd p
endfunction


" use K and CTRL+K for comment/uncomment
if exists('g:vim_peter')
  noremap <buffer> <silent>     K :call <SID>AddComment()<CR>j
  noremap <buffer> <silent> <C-K> :call <SID>DelComment()<CR>j
else
  silent! nunmap <buffer>     K
  silent! nunmap <buffer> <C-K>
endif

function! <SID>AddComment() " {{{
  s,^\(\s*\)\@>\([^"]\),\1"\2,e
endfunction " }}}
function! <SID>DelComment() " {{{
  " try not to move the cursor
  let l:pos = getpos('.')
  s,^\(\s*\)\@>"\%(\s\|TODO:\)\@!,\1,e
  " if cursor is on the same line, move it back to where it was
  if getpos('.')[0] == l:pos[0]
    call setpos('.', l:pos)
  endif
endfunction " }}}
