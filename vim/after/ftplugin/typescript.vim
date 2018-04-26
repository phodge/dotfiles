if ! &l:diff
  setlocal foldmethod=indent
  setlocal foldcolumn=1
  setlocal foldlevel=1
endif

" use & to search for variables
if g:vim_peter
  nnoremap <buffer> &  /<C-R>=<SID>GetVarSearch()<CR><CR>
  nnoremap <buffer> g& ?<C-R>=<SID>GetVarSearch()<CR><CR>
  function! <SID>GetVarSearch() " {{{
    let l:old_iskeyword = &l:iskeyword
    try
      setlocal iskeyword+=$
      return escape(expand('<cword>'), '$\') . '\>'
    finally
      let &l:iskeyword = l:old_iskeyword
    endtry
  endfunction " }}}
else
  silent! nunmap <buffer> &
  silent! nunmap <buffer> g&
endif

" helper mappings
if g:vim_peter
  inoremap <buffer> ,T throw new Error("TODO: finish this");<ESC>F:llvt"
else
  iunmap <buffer> ,T
endif

" goto definition and such
nnoremap <buffer> <space>d :YcmCompleter GoToDefinition<CR>

" use K and CTRL+K for comment/uncomment
if g:vim_peter
  noremap <buffer> <silent>     K :call <SID>AddComment()<CR>j
  noremap <buffer> <silent> <C-K> :call <SID>DelComment()<CR>j
else
  silent! nunmap <buffer>     K
  silent! nunmap <buffer> <C-K>
endif

function! <SID>AddComment() " {{{
  s,^\(\s*\)\@>\(//\)\@!\ze\S,\1//,e
endfunction " }}}
function! <SID>DelComment() " {{{
  " try not to move the cursor
  let l:pos = getpos('.')
  s,^\(\s*\)\@>//\%(\s\|\u\+-\d\+\)\@!,\1,e
  " if cursor is on the same line, move it back to where it was
  if getpos('.')[0] == l:pos[0]
    call setpos('.', l:pos)
  endif
endfunction " }}}

