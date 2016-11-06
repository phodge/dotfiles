augroup ClintInit
augroup end
au! ClintInit BufRead *.c call <SID>TheSetup()

fun! <SID>TheSetup()
  if exists('s:loaded_syntastic_clint_checker')
    return
  endif
  let s:loaded_syntastic_clint_checker = 1
  call g:SyntasticRegistry.CreateAndRegisterChecker({
        \ 'filetype': 'c',
        \ 'name': 'clint',
        \ 'exec': './src/clint.py' })
endfun

" this clint.vim thing I grabbed from the internets
let s:loaded_syntastic_clint_checker = 1

function! SyntaxCheckers_c_clint_GetLocList() dict
  let makeprg = self.makeprgBuild({
              \ 'args': '',
              \ 'args_after': '' })
  let errorformat = '%f:%l:  %m'
  return SyntasticMake({ 'makeprg': makeprg, 'errorformat': errorformat })
endfunction


nnoremap <F5> :Shell ag -ws <C-R><C-W><CR>
nnoremap <F6> :Shell ag -wis <C-R><C-W><CR>

augroup CustomFileType
augroup end
au! CustomFileType BufRead runtime/doc/**.txt setlocal filetype=help textwidth=78 conceallevel=0 colorcolumn=+2 sts=2 ts=8 sw=2 noet
