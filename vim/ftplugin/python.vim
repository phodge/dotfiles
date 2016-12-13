if ! &l:diff
  setlocal foldmethod=indent foldcolumn=1
endif
setlocal formatoptions=croqlj
setlocal list listchars=tab:^_,trail:.,extends:>,precedes:\<,nbsp:.

" these two options are now set using the SetLineLength() function below
"setlocal tw=79 " just for comments
"setlocal colorcolumn=+2

" use :Isort to fix imports in the current buffer
" Note that vim plugin 'fisadev/vim-isort' is supposed to do this, but when I
" use that plugin it doesn't respect the config in my ~/.isort.cfg file
com! -range=% Isort call <SID>DoSort('<line1>', '<line2>')
fun! <SID>DoSort(line1, line2)
  let l:pos = exists('*getcurpos') ? getcurpos() : getpos('.')
  try
    exe printf('%s,%s!isort -', a:line1, a:line2)
  finally
    call setpos('.', l:pos)
  endtry
endfun
nnoremap <buffer> <space>i :Isort<CR>
augroup IsortAuto
augroup end
au! IsortAuto InsertLeave <buffer> if getline('.') =~ '^\%(from\|import\)\s\+' | exe 'Isort' | exe 'undojoin' | endif

" set up \\c mapping to toggle the line length
nnoremap <buffer> \c :call <SID>ToggleLineLength()<CR>

if ! exists('s:lengths')
  let s:lengths = {}
endif
if ! exists('s:length_options')
  let s:length_options = [79, 99]
endif

function! <SID>SetGlobalLineLength(new_len)
  if a:new_len > 0
    let g:syntastic_python_flake8_post_args = "--max-line-length=" . a:new_len
  else
    let g:syntastic_python_flake8_post_args = "--max-line-length=99999"
  endif
endfunction

function! <SID>SetLineLength(new_length)
  let l:bufnr = bufnr('')
  if type(a:new_length) == type('') && a:new_length == '__AUTO__'
    let l:idx = 0
    let l:choice = s:length_options[l:idx]
    " use 79 unless there is a longer line
    for l:linenr in range(1, line('$'))
      while col([l:linenr, '$']) >= l:choice
        let l:idx += 1
        if l:idx >= len(s:length_options)
          let l:choice = -1
          break
        endif
        let l:choice = s:length_options[l:idx]
      endwhile
      if l:choice == -1
        let l:new_length = l:choice
        break
      endif
      let l:new_length = l:choice
    endfor
  else
    let l:new_length = a:new_length
  endif
  let s:lengths[l:bufnr] = l:new_length
  let &l:textwidth = l:new_length
  let &l:colorcolumn = l:new_length ? '+2' : ''
  call <SID>SetGlobalLineLength(s:lengths[l:bufnr])
endfunction

function! <SID>ToggleLineLength()
  let l:bufnr = bufnr('')
  let l:current_length = get(s:lengths, l:bufnr, 0)
  if ! l:current_length
    call <SID>SetLineLength(79)
  elseif l:current_length == 79
    call <SID>SetLineLength(99)
  else
    call <SID>SetLineLength(0)
  endif
endfunction


" Because syntastic is dumb and uses a global variable for its settings, we
" must use an autocmd to set the line length for each individual buffer
augroup PySyntasticLineLength
autocmd! WinEnter <buffer> call <SID>SetGlobalLineLength(get(s:lengths, bufnr(''), 0))
augroup end

" set the line length accordingly
call <SID>SetLineLength(get(s:lengths, bufnr(''), '__AUTO__'))

" add a TODO exception quickly
if exists('g:vim_peter')
  inoremap <buffer> ,T raise Exception("TODO: finish this")  # noqa<ESC>F"hvFfo
else
  silent! iunmap <buffer> ,T
endif

" jedi mappings
if exists('g:vim_peter')
  " go to original definition of whatever is under the cursor
  nnoremap <buffer> <SPACE>d :call jedi#goto()<CR>
  " replace/rename whatever is under the cursor
  nnoremap <buffer> <SPACE>r :call jedi#replace()<CR>
  " find uses of the thing under the cursor
  nnoremap <buffer> <SPACE>u :call jedi#usages()<CR>
  " show documentation (help) for the thing under the cursor
  nnoremap <buffer> <SPACE>h :call jedi#show_documentation()<CR>
  " rename the thing under the cursor
  nnoremap <buffer> <SPACE>r :call jedi#rename()<CR>
else
  silent! nunmap <buffer> <SPACE>d
  silent! nunmap <buffer> <SPACE>r
  silent! nunmap <buffer> <SPACE>u
  silent! nunmap <buffer> <SPACE>h
  silent! nunmap <buffer> <SPACE>r
endif

" gF mapping
if exists('g:vim_peter')
  nnoremap <buffer> gF :if <SID>FindFunctionInFile() <BAR> set hlsearch <BAR> endif<CR>
  function! <SID>FindFunctionInFile() " {{{
    let l:word = expand('<cword>')
    let l:prefixes = []
    call add(l:prefixes, '\%(class\|def\)\s\+')
    call add(l:prefixes, 'import\s\+')
    call add(l:prefixes, 'from [a-zA-Z0-9.]\+\_s\+import\%(\_s\|(\)\+\%(\w\+\_s*,\_s*\)*')
    let @/ = '\%('.join(l:prefixes, '\|').'\)\zs\<'.l:word.'\>'
    try
      normal! 0nzv
      return &hlsearch
    catch /E486: Pattern not found/
      let l:vimerror = substitute(v:exception, '^Vim(normal):\s*', '', '')
      echohl Error
      echo printf("Class/function/import %s() not found: %s", l:word, l:vimerror)
      echohl None
      return 0
    endtry
  endfunction " }}}
else
  silent! nunmap <buffer> gF
endif

" use K and CTRL+K for comment/uncomment
if exists('g:vim_peter')
  noremap <buffer> <silent>     K :call <SID>AddComment()<CR>j
  noremap <buffer> <silent> <C-K> :call <SID>DelComment()<CR>j
else
  silent! nunmap <buffer>     K
  silent! nunmap <buffer> <C-K>
endif

" ignore warning about no space after # ... this causes all our commented code
" to get flagged.
if ! exists('g:syntastic_python_flake8_quiet_messages')
  let g:syntastic_python_flake8_quiet_messages = {}
endif
let g:syntastic_python_flake8_quiet_messages['regex'] = '\[E265\]$'



function! <SID>AddComment() " {{{
  s,^\(\s*\)\@>\([^#]\),\1#\2,e
endfunction " }}}
function! <SID>DelComment() " {{{
  " try not to move the cursor
  let l:pos = getpos('.')
  s,^\(\s*\)\@>#\%(\s\|TODO:\)\@!,\1,e
  " if cursor is on the same line, move it back to where it was
  if getpos('.')[0] == l:pos[0]
    call setpos('.', l:pos)
  endif
endfunction " }}}


" Ninja mappings {{{
if exists('g:vim_peter')
  " Using J to join lines automatically removes a comment leader
  noremap <buffer> J :call <SID>JoinLines()<CR>
  function! <SID>JoinLines() range " {{{
    let i = a:firstline

    " need to operate on at least one line
    if a:firstline == a:lastline
      let i -= 1
    endif

    while i < a:lastline
      let i += 1

      " first, join the lines
      normal! J

      let l:synID = synID(line('.'), col('.'), 1)
      if synIDattr(l:synID, "name") == 'pythonComment'
        " if we are inside a comment, we need to get rid of the # that may
        " have been joined
        normal! mt
        undojoin
        s,\s*\%#\s*#\s*, ,e
        normal `t
      endif
    endwhile
  endfunction " }}}
else
  silent! nunmap <buffer> J
endif
" }}}
