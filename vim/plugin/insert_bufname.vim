function! <SID>InsertBufname() abort
  let l:bufnr = input('Buffer number: ')
  if l:bufnr ==# ''
    return ''
  endif
  return bufname(str2nr(l:bufnr))
endfunction

inoremap <C-R>b <C-R>=<SID>InsertBufname()<CR>
cnoremap <C-R>b <C-R>=<SID>InsertBufname()<CR>
