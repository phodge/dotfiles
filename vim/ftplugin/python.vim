if ! &l:diff
  setlocal foldmethod=indent foldcolumn=1
endif
setlocal formatoptions=croqlj
setlocal list listchars=tab:^_,trail:.,extends:>,precedes:\<,nbsp:.

" tell multipython where to find out python2/python3 binaries
call multipython#setpy3paths(get(g:, 'my_py3_paths', []))
call multipython#setpy2paths(get(g:, 'my_py2_paths', []))

" these two options are now set using the SetLineLength() function below
"setlocal textwidth=79 " just for comments
"setlocal colorcolumn=+2

nnoremap <buffer> \2 :call multipython#togglepy2()<CR>
nnoremap <buffer> \3 :call multipython#togglepy3()<CR>
nnoremap <buffer> <space>2 :call multipython#printversions()<CR>
nnoremap <buffer> <space>3 :call multipython#printversions()<CR>
nnoremap <buffer> <space>f :call <SID>FormatFile()<CR>

" This is the default flake8 ignore list. See
let s:flake8_default_ignore = split('E121 E123 E126 E226 E24 E704')

" Always ignore E265 (no space between '#' and comment text) and E116
" (unexpected indent (comment)) since my comment-adding mappings always
" produce these errors
let b:flake8_ignore = ['E265', 'E116']

" create the dict for adding isort flags
if !exists('b:isort_flags')
  let b:isort_flags = {}
endif

fun! <SID>PyVersionChanged()
  let l:want2 = multipython#wantpy2()
  let l:want3 = multipython#wantpy3()

  let l:flakes = []

  " grab whichever version of yapf is available
  if l:want3
    call add(l:flakes, 3)
  endif

  if l:want2
    call add(l:flakes, 2)
  endif

  " tell syntastic to use our multiflake8 for the current buffer
  let b:syntastic_checkers = ['flake8']
  let b:syntastic_flake8_exec = 'multiflake8'
  " configure Ale the same way
  let b:ale_linters = {"python": ['flake8', 'mypy']}
  let b:ale_python_flake8_executable = 'multiflake8'

  " desired line length?
  let l:maxlen = get(s:lengths, bufnr(''), 0)
  if l:maxlen <= 0
    let l:maxlen = 99999
  endif

  " work out the arguments needed for multiflake8
  let l:args = ['--filename=*', '--max-line-length='.l:maxlen]

  " combine the default ignore list with this buffer's ignore list
  let l:ignore = get(b:, 'flake8_ignore', []) + s:flake8_default_ignore
  call add(l:args, '--ignore='.join(l:ignore, ','))

  for l:major in l:flakes
    " Tell multiflake8 exactly where to find the flake8 for this python version.
    let l:flake = multipython#getpythoncmd(l:major, 'flake8', 1, 1)
    call add(l:args, '--use-this-checker='.l:flake)
  endfor

  " put the finalised args where ale/syntastic will find them
  let b:ale_python_flake8_options = join(map(l:args, 'shellescape(v:val)'), ' ')
  let b:syntastic_python_flake8_post_args = b:ale_python_flake8_options

  " toggle python2/3 syntax compatibility
  let b:python_py2_compat = l:want2 ? 1 : 0
  let b:python_py3_compat = l:want3 ? 1 : 0
  syn clear
  set syntax=python
endfun

fun! <SID>FormatFile()
  let l:oldpos = getpos('.')
  let l:prog = multipython#getpythoncmd(0, 'yapf', 1, 0)
  try
    exe printf("1,$!%s --style=/Users/phodge7/.style.yapf", l:prog)
  finally
    call setpos('.', l:oldpos)
  endtry
endfun

" use :Isort to fix imports in the current buffer
" Note that vim plugin 'fisadev/vim-isort' is supposed to do this, but when I
" use that plugin it doesn't respect the config in my ~/.isort.cfg file
com! -range=% Isort call <SID>DoSort('<line1>', '<line2>')
fun! <SID>DoSort(line1, line2)
  if exists('b:isort_disabled') && b:isort_disabled
    return
  endif

  " ask multipython where to find isort for the current python version
  let l:isort = multipython#getpythoncmd(0, 'isort', 1, 1)

  " do we have any options CLI options for isort?
  let l:options = get(b:, 'isort_flags', {})
  for [l:name, l:value] in items(l:options)
    if l:value == v:true && type(l:value) == type(v:true)
      let l:isort .= printf(' --%s', shellescape(l:name))
    else
      let l:isort .= printf(' --%s %s', shellescape(l:name), shellescape(l:value))
    endif
  endfor

  let l:pos = exists('*getcurpos') ? getcurpos() : getpos('.')
  try
    exe printf('%s,%s!%s -', a:line1, a:line2, l:isort)
    if v:shell_error != 0
      let b:isort_disabled = 1
      echoerr 'Isort failed - setting b:isort_disabled'
    endif
  finally
    call setpos('.', l:pos)
    " modifying the buffer like this usually screws up the diff
    diffup
  endtry
endfun
augroup IsortAuto
augroup end
au! IsortAuto InsertLeave <buffer> call <SID>AutoIsort()

fun! <SID>AutoIsort()
  if exists('g:isort_automatic') && !g:isort_automatic
    return
  endif

  if exists('b:isort_disabled') && b:isort_disabled
    return
  endif

  if getline('.') =~ '^\%(from\|import\)\s\+'
    Isort
    undojoin
  endif
endfun


nnoremap <buffer> <space>i :Isort<CR>
nnoremap <buffer> <space>i :call <SID>SmartIsortTrigger()<CR>
fun! <SID>SmartIsortTrigger() " {{{
  " if the character under the cursor is alphanumeric, work out what the word is
  " if the current line is an import statement, 
  let l:line = getline('.')
  if l:line =~ '^\s*\%(from\|import\)'
    Isort
    return
  endif

  let l:char = strpart(l:line, col('.') - 1, 1)
  if l:char !~ '\w'
    Isort
    return
  endif

  call <SID>SmartImportUI()
endfun " }}}


" set up \\c mapping to toggle the line length
nnoremap <buffer> \c :call <SID>ToggleLineLength()<CR>

if ! exists('s:lengths')
  let s:lengths = {}
endif
if ! exists('s:length_options')
  let s:length_options = [79, 99]
endif

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
  call <SID>PyVersionChanged()
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


" set the line length automatically for the current buffer
call <SID>SetLineLength(get(s:lengths, bufnr(''), '__AUTO__'))

" tell multipython to call our callback whenever the python version changes in
" the current buffer
call multipython#addcallback(function("<SID>PyVersionChanged"))

" if detect current python versions if it hasn't been done yet
if ! multipython#versionsdetected()
  " HOMELY.py scripts always get python3 and nothing else
  if expand('%:t') == 'HOMELY.py'
    call multipython#setpy3(1, "HOMELY.py is always py3")
  elseif ! multipython#detectversions()
    " if automatic detection doesn't work, fall back to 3.4/2.7 combo
    call multipython#setpy3(1, "phodge's default", 0)
    call multipython#setpy2(1, "phodge's default")
  endif
endif

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


vnoremap <space>i <ESC>:call <SID>SmartImportUI()<CR>

fun! <SID>SmartImportUI() " {{{
  let l:word = expand('<cword>')

  " these words instantly trigger adding an import for a top-level module
  let l:always_modules = split(
        \ 'os sys re collections click simplejson homely enum pprint itertools functools'
        \ .' tempfile operator glob shutil io argparse subprocess requests base64 pathlib'
        \ .' contextlib'
        \ )

  " these names are always imported from these modules
  let l:vocabulary = {
        \ "partial": "functools",
        \ "contextmanager": "contextlib",
        \ "ArgumentParser": "argparse",
        \ "check_call": "subprocess",
        \ "check_output": "subprocess",
        \ "Popen": "subprocess",
        \ "Enum": "enum",
        \ }

  let l:typical = {
        \ "Path": "pathlib",
        \ "b64encode": "base64",
        \ "b64decode": "base64",
        \ "Href": "werkzeug",
        \ }

  let l:module = get(l:vocabulary, l:word, "")
  if strlen(l:module)
    call <SID>AddImportLineNow('from '.l:module.' import '.l:word)
    return
  endif

  if index(l:always_modules, l:word) > -1
    call <SID>AddImportLineNow('import '.l:word)
    return
  end

  " start compiling a list of suggestions
  let l:modules = {}
  let l:module = get(l:typical, l:word, "")
  if strlen(l:module)
    let l:modules[l:module] = ""
  endif

  " make a list of imports already in the module
  call extend(l:modules, <SID>GetCurrentImports())

  if len(l:modules)
    let l:options = []
    " ask the user if they'd like to import it from one of the existing modules?
    for l:module in sort(keys(l:modules))
      call add(l:options, printf('from %s import %s', l:module, l:word))
      echohl Question
      echon len(l:options).'. '
      echohl pyImport
      echon 'from '
      echohl None
      echon l:module
      echohl pyImport
      echon ' import '
      echohl None
      echon l:word
      echo ''
    endfor
    let l:choice = input("Enter the number of the import you would like to add, or press ESC to abort\n")
    redraw
    if l:choice =~ '^\_s*$'
      " user cancelled
      return
    elseif l:choice =~ '^\d\+$'
      let l:line = get(l:options, l:choice - 1)
      if ! (type(l:line) == type(0) && l:line == 0)
        call <SID>AddImportLineNow(l:line)
        return
      endif
    endif

    echohl Error
    echo 'Invalid choice'
    echohl None
    return
  endif

  echohl Error
  echo "Couldn't add import for ".l:word
  echohl None
endfun " }}}

fun! <SID>AddImportLineNow(line) " {{{
  let l:where = 1

  while l:where < line('$')
    if getline(l:where) =~ '^#'
      let l:where += 1
      continue
    endif
    " add a mark we can jump back to
    normal! mi
    call append(l:where, a:line)
    Isort
    normal! `i
    return
  endwhile
endfun " }}}

fun! <SID>GetCurrentImports() " {{{
  let l:imports = {}
  for l:nr in range(1, line('$'))
    let l:match = matchlist(getline(l:nr), '^\s*\(from\|import\)\s\+\([a-zA-Z0-9_.]\+\)')
    if len(l:match)
      let l:imports[l:match[2]] = l:match[1]
    elseif getline(l:nr) =~ '^\%(def\|class\)\s'
      " stop searching as soon as we hit a function or class that isn't indented
      break
    endif
  endfor
  return l:imports
endfun " }}}
