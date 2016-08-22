" fix up the packaged iskeyword setting
setlocal iskeyword-=$

" better completion options
setlocal complete=.,b,k,w,t,i

" nicer format options
setlocal comments=b:#,b://,s1:/*,mb:*,xe:*/
setlocal formatoptions=croqn2
setlocal textwidth=120

if ! &l:diff
  setlocal foldmethod=indent
  setlocal foldcolumn=1
  setlocal foldlevel=1
endif


" I use these alot
if g:vim_peter
  inoremap <buffer> ,, ->
  inoremap <buffer> ,t $this->
  inoremap <buffer> ,T throw new \Exception(':TODO: finish this');<ESC>hhhvFfo
else
  silent! iunmap <buffer> ,,
  silent! iunmap <buffer> ,t
  silent! iunmap <buffer> ,T
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

" Add ; to end of line by pressing ,.
if g:vim_peter
  nnoremap <buffer> ,. :call <SID>AddSemicolon()<CR>

  function! <SID>AddSemicolon() " {{{
      " set marker at current position
      normal! mt
      " use :s to add the semicolon now
      s,\(\s*\%(//.*\)\=\)$,;\1,
      " restore cursor
      normal! `t
  endfunction " }}}
else
  silent! nunmap <buffer> ,.
endif

" if we set up a buffer mapping for gF, then gsF will work also
if g:vim_peter
  nnoremap <buffer> gF :if <SID>FindFunctionInFile() <BAR> set hlsearch <BAR> endif<CR>
  function! <SID>FindFunctionInFile() " {{{
    let l:word = expand('<cword>')
    let @/ = '\c\<\%(function\|class\)\%(\s*&\s*\|\s\+\)' . l:word . '\>'
    try
      normal! 0nzv
      return &hlsearch
    catch /E486: Pattern not found/
      let l:vimerror = substitute(v:exception, '^Vim(normal):\s*', '', '')
      echohl Error
      echo printf("Function %s() not found: %s", l:word, l:vimerror)
      echohl None
      return 0
    endtry
  endfunction " }}}
else
  silent! nunmap <buffer> gF
endif


" Ninja mappings {{{
if g:vim_peter
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
      if synIDattr(l:synID, "name") == 'phpComment'
        " if we are inside a comment, we need to get rid of the // or '*' that
        " may have been joined
        normal! mt
        undojoin
        s,\s*\%#\s*\%(//\|\*/\@!\)\s*, ,e
        normal `t
      endif
    endwhile
  endfunction " }}}
else
  silent! nunmap <buffer> J
endif
" }}}

" On writing a PHP buffer, do a lint test, as well as insight tests
augroup ExcaliburPHPCheck
autocmd! BufWritePost <buffer> call <SID>PHPCheck()
augroup end

function! <SID>PHPCheck() " {{{
  let l:cmd  = 'php -l '.shellescape(bufname(""))
  let l:result = system(l:cmd)
  if v:shell_error != 0
    " trim whitespace off start and end
    let l:result = substitute(l:result, '^\_s\+\|\_s\+$', '', 'g')

    " remove the redundant 'Errors parsing [file]' from the returned output
    " (unless that's all PHP gave us)
    let l:shorter = substitute(l:result, '\_s*Errors parsing '.bufname("").'$', '', '')
    if strlen(l:shorter)
      let l:result = l:shorter
    endif

    " display the error message on screen
    redraw
    echohl Error
    echo l:result
    echohl None
    return
  endif

  if exists('g:insight_path')
    if exists('g:insight_php_tests') && type(g:insight_php_tests) == type([])
      let l:tests = g:insight_php_tests
    else
      " TODO - get var-not-used working as well
      " TODO - lone-var-check doesn't seem to be working either
      let l:tests = [ 'var-not-set' ]
    endif

    " run insight tests on the file as well
    for l:test in l:tests
      let l:cmd = g:insight_path.' '.l:test.' '.shellescape(bufname(""))
      let l:result = system(l:cmd)
      if v:shell_error != 0
        " trim whitespace off start and end
        let l:result = substitute(l:result, '^\_s\+\|\_s\+$', '', 'g')

        " display the error message on screen
        redraw
        echohl Error
        echo l:result
        echohl None
        return
      endif
    endfor
  endif
endfunction " }}}

