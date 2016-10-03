if ! exists('s:loaded_syntastic_clint_checker')
  au! ClintInit BufRead *.c call <SID>TheSetup()
  fun! <SID>TheSetup()
    call g:SyntasticRegistry.CreateAndRegisterChecker({
          \ 'filetype': 'c',
          \ 'name': 'clint',
          \ 'exec': '~/playground-6/neovim/src/clint.py' })
  endfun
endif

" this clint.vim thing I grabbed from the internets
let s:loaded_syntastic_clint_checker = 1

function! SyntaxCheckers_c_clint_GetLocList() dict
  let makeprg = self.makeprgBuild({
              \ 'args': '',
              \ 'args_after': '' })
  let errorformat = '%f:%l:  %m'
  return SyntasticMake({ 'makeprg': makeprg, 'errorformat': errorformat })
endfunction


nnoremap <F5> :Shell ag -ws <C-R><C-W>
nnoremap <F6> :Shell ag -s <C-R><C-W>
