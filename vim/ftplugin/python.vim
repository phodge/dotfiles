setlocal formatoptions=croqlj
setlocal list listchars=tab:^_,trail:.,extends:>,precedes:\<,nbsp:.

if has('nvim') && g:want_neovim_treesitter_python
  setlocal foldmethod=expr
  setlocal foldexpr=nvim_treesitter#foldexpr()
endif

" set a nice 'foldlevel' so that everything isn't collapsed when we open a
" file
setlocal foldlevel=1

" Ninja mapping for visual 'gq' that temporarily sets tw=79 while it is working.
" Set b:peter_formatting_use_textwidth = 1 to disable it
vnoremap gq <ESC>:exe (get(b:, 'peter_formatting_use_textwidth', 1) ? 'normal! gvgq' : 'call <SID>GQ(1)')<CR>

function! <SID>GQ(isvisual)
  let l:old_tw = &l:textwidth
  let l:old_fex = &l:formatexpr
  try
    setlocal tw=79
    " also reset formatexpr so that formatting isn't delegated to the language
    " server (it won't respect our 'textwidth' setting)
    setlocal formatexpr=
    if a:isvisual
      normal! gvgq
    else
      normal! gq
    endif
  finally
    let &l:textwidth = l:old_tw
    let &l:formatexpr = l:old_fex
  endtry
endfun


" these two options are now set using the SetLineLength() function below
"setlocal textwidth=79 " just for comments
"setlocal colorcolumn=+2

command! -bang -nargs=+ -bar -buffer Flake8Ignore call <SID>Ignore('<bang>' == '!', <f-args>)

" This is the default flake8 ignore list. See
let s:flake8_default_ignore = ['E704']

function! <SID>Ignore(reset, ...)
  if a:reset
    " reset ignore list
    let b:flake8_ignore = []
  else
    " make sure variable is set
    let b:flake8_ignore = get(b:, 'flake8_ignore', [])
  endif

  " items to be added/removed
  for l:item in a:000
    if l:item =~ '^-'
      let l:name = strpart(l:item, 1)
      " remove item as many times as it appears
      for i in range(100)
        let l:idx = index(b:flake8_ignore, l:name)
        if l:idx == -1
          break
        endif
        call remove(b:flake8_ignore, l:idx)
      endfor
    elseif strlen(l:item)
      " add the item if it isn't already there
      if -1 == index(b:flake8_ignore, l:item)
        call add(b:flake8_ignore, l:item)
      endif
    endif
  endfor

  call <SID>PyVersionChanged()
endfun

" create the dict for adding isort flags
if !exists('b:isort_flags')
  let b:isort_flags = {}
endif

fun! <SID>PyVersionChanged()
  " desired line length?
  let l:maxlen = &l:textwidth
  if l:maxlen <= 0
    let l:maxlen = 99999
  endif

  " work out the arguments needed for flake8
  " TODO: I'm not sure why we have to manually set --filename and
  " --stdin-display-name in our plugin here
  let l:args = ['--filename=*', '--max-line-length='.l:maxlen]

  " let flake8 know what the name of the file from stdin is so that it can
  " respect the "per-file-ignores" options
  call add(l:args, '--stdin-display-name='.bufname(''))

  " combine the default ignore list with this buffer's ignore list
  let l:ignore = get(b:, 'flake8_ignore', []) + s:flake8_default_ignore
  call add(l:args, '--extend-ignore='.join(l:ignore, ','))

  " put the finalised args where ale will find them
  let b:ale_python_flake8_options = join(map(l:args, 'shellescape(v:val)'), ' ')

  " toggle python2/3 syntax compatibility
  " TODO: are these needed for my syntax file?
  let b:python_py2_compat = 0
  let b:python_py3_compat = 1
  syn clear
  set syntax=python

  " redo ALE errors if necessary
  if exists(':ALELint')
    ALELint
  endif
endfun

" use :Isort to fix imports in the current buffer
" Note that vim plugin 'fisadev/vim-isort' is supposed to do this, but when I
" use that plugin it doesn't respect the config in my ~/.isort.cfg file
com! -range=% Isort call <SID>DoSort('<line1>', '<line2>')
fun! <SID>DoSort(line1, line2)
  if exists('b:isort_disabled') && b:isort_disabled
    echohl WarningMsg
    echo 'isort is disabled for this buffer via b:isort_disabled'
    echohl None
    return
  endif

  let l:isort = 'isort'

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
  if l:line =~ '^\s*\%(from\|import\)\>'
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
      while col([l:linenr, '$']) > (l:choice + 1)
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
  let &l:textwidth = l:new_length
  let &l:colorcolumn = l:new_length ? '+2' : ''

  if exists('+winhighlight')
    let l:parts = split(&l:winhighlight, ',', 0)
    if l:new_length == s:length_options[1]
      " map highlight to highlight #2
      call add(l:parts, 'ColorColumn:ColorColumn2')
    else
      " remove custom highlight
      let l:parts = filter(l:parts, 'v:val !~ "^ColorColumn:"')
    endif
    let &l:winhighlight = join(l:parts, ',')
  endif

  call <SID>PyVersionChanged()
endfunction

function! <SID>GetLengthOptions()
  " what lengths are available for this buffer?
  let l:lengths = get(b:, 'python_line_length_options', 0)
  if type(l:lengths) != type([]) || !len(l:lengths)
    return [0, 79, 99]
  endif
  return l:lengths
endfun

function! <SID>GetInitialLineLength()
  " use current 'textwidth' value if its set
  if &l:textwidth
    return &l:textwidth
  endif

  for l:value in <SID>GetLengthOptions()
    if l:value > 0
      return l:value
    endif
  endfor

  return l:lengths[0]
endfun

function! <SID>ToggleLineLength()
  " what lengths are available for this buffer?
  let l:lengths = <SID>GetLengthOptions()

  " what length are we currently using?
  let l:current = index(l:lengths, &l:textwidth)

  if l:current == -1
    " not found - just using the first option from the list
    call <SID>SetLineLength(l:lengths[0])
  elseif l:current == (len(l:lengths) - 1)
    " we're using the last option - go back to the start
    call <SID>SetLineLength(l:lengths[0])
  else
    " use the next option in the list
    call <SID>SetLineLength(l:lengths[l:current + 1])
  endif
endfunction

" set the line length automatically for the current buffer
call <SID>SetLineLength(<SID>GetInitialLineLength())

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


vnoremap <buffer> <space>i <ESC>:call <SID>SmartImportUI()<CR>

fun! <SID>SmartImportUI() " {{{
  let l:word = expand('<cword>')

  " these names are always imported from these modules
  let l:vocabulary = {
        \ "partial": "functools",
        \ "contextmanager": "contextlib",
        \ "asynccontextmanager": "contextlib",
        \ "ArgumentParser": "argparse",
        \ "check_call": "subprocess",
        \ "check_output": "subprocess",
        \ "Popen": "subprocess",
        \ "PIPE": "subprocess",
        \ "DEVNULL": "subprocess",
        \ "namedtuple": "collections",
        \ "OrderedDict": "collections",
        \ "defaultdict": "collections",
        \ "Collection": "collections.abc",
        \ "Reversible": "collections.abc",
        \ "Decimal": "decimal",
        \ "Any": "typing",
        \ "Callable": "typing",
        \ "Dict": "typing",
        \ "Iterable": "typing",
        \ "Iterator": "typing",
        \ "List": "typing",
        \ "NewType": "typing",
        \ "Optional": "typing",
        \ "Set": "typing",
        \ "Tuple": "typing",
        \ "TYPE_CHECKING": "typing",
        \ "Type": "typing",
        \ "Union": "typing",
        \ "Boolean": "sqlalchemy",
        \ "Column": "sqlalchemy",
        \ "ForeignKey": "sqlalchemy",
        \ "Integer": "sqlalchemy",
        \ "String": "sqlalchemy",
        \ "Text": "sqlalchemy",
        \ "Numeric": "sqlalchemy",
        \ "create_engine": "sqlalchemy",
        \ "relationship": "sqlalchemy.orm",
        \ "sessionmaker": "sqlalchemy.orm",
        \ "desc": "sqlalchemy",
        \ "func": "sqlalchemy.sql",
        \ "declarative_base": "sqlalchemy.ext.declarative",
        \ "TemporaryDirectory": "tempfile",
        \ "Path": "pathlib",
        \ "dedent": "textwrap",
        \ "dataclass": "dataclasses",
        \ "classproperty": "django.utils.functional",
        \ }

  " these words instantly trigger adding an import for a top-level module
  let l:always_modules = split(
        \ 'os sys re collections click simplejson json homely enum pprint itertools functools'
        \ .' tempfile operator glob shutil io argparse subprocess requests base64 pathlib'
        \ .' contextlib tempfile neovim dataclasses typing decimal abc pytest attrs platform'
        \ .' shlex unittest time_machine'
        \ )

  " these names are suggested when the identifiers are encountered
  let l:typical = {
        \ "ContextManager": "typing",
        \ "Enum": "enum",
        \ "Gitlab": "gitlab",
        \ "Href": "werkzeug",
        \ "Literal": "typing",
        \ "Mapped": "sqlalchemy.orm",
        \ "Session": "sqlalchemy.orm",
        \ "b64decode": "base64",
        \ "b64encode": "base64",
        \ "cast": "typing",
        \ "chain": "itertools",
        \ "date": "datetime",
        \ "datetime": "datetime",
        \ "dirname": "os.path",
        \ "exists": "os.path",
        \ "in_": "sqlalchemy",
        \ "make_transient": "sqlalchemy.orm",
        \ "mapped_column": "sqlalchemy.orm",
        \ "mock": "unittest",
        \ "or_": "sqlalchemy",
        \ "realpath": "os.path",
        \ "run": "subprocess",
        \ "select": "sqlalchemy",
        \ "time": "time",
        \ "timedelta": "datetime",
        \ }

  let l:exactimport = get(b:, 'peter_auto_import_exact_imports', {})->get(l:word, '')
  if strlen(l:exactimport)
    call <SID>AddImportLineNow(l:exactimport)
    return
  endif

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
    let l:modules[l:module] = "stdlib"
  endif

  " make a list of imports already in the module
  call extend(l:modules, <SID>GetCurrentImports())

  let l:projectmarkers = ['.hg', '.git', 'pyproject.toml', 'setup.py']

  " also look through tags to see if there is an importable match in another
  " file
  for l:tag in taglist(l:word)
    if l:tag.name == l:word && l:tag.filename =~ '\.py$'
      " work out the nearest 'setup.py', 'pyproject.toml' or '.git' dir for
      " the candidate file
      let l:filename = fnamemodify(l:tag.filename, ':p')
      let l:examine = l:filename
      let l:candidateroot = ''
      let l:guard = 0
      while strlen(l:examine) > 2 && l:candidateroot == ''
        let l:guard += 1
        if l:guard >= 100
          continue
        endif

        " strip off the last '/<filename>' part
        let l:examine = substitute(l:examine, '/[^/]*$', '', '')

        " if there is a 
        for l:lookfor in l:projectmarkers
          let l:check = l:examine . '/' . l:lookfor
          if isdirectory(l:check) || filereadable(l:check)
            let l:candidateroot = l:examine
            break
          endif
        endfor
      endwhile

      if strlen(l:candidateroot)
        " get candidate filename relative to candidateroot by stripping the
        " correct number of characters off the front (plus one extra for the '/')
        let l:candidate = strpart(l:filename, strlen(l:candidateroot) + 1)
      else
        " otherwise just get candidate name relative to cwd
        let l:candidate = fnamemodify(l:filename, ':.')
      endif

      if exists('b:python_packages_dir') && type(b:python_packages_dir) == type([])
        for l:dir in b:python_packages_dir
          if stridx(l:candidate, l:dir . '/') == 0
            let l:candidate = strpart(l:candidate, strlen(l:dir) + 1)
            break
          endif
        endfor
      endif

      " remove '.py' extension; convert path separators to '.'
      let l:candidate = substitute(fnamemodify(l:candidate, ':r'), '/', '.', 'g')

      if l:candidate =~ '\.__init__$'
        let l:candidate = strpart(l:candidate, 0, strlen(l:candidate) - 9)
      endif

      " if the name ends with '.__init__', strip it off
      let l:modules[l:candidate] = "tags file"
    endif
  endfor

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
      let l:origin = l:modules[l:module]
      if strlen(l:origin)
        echohl Comment
        echon printf('  # from %s', l:origin)
      endif
      echohl None
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

  let l:in_docblock = ""
  while l:where < line('$')
    if getline(l:where) =~ '^#'
      let l:where += 1
      continue
    endif

    " are we in the middle of a docblock?
    if strlen(l:in_docblock)
      if getline(l:where) == l:in_docblock
        let l:in_docblock = ""
      endif
      let l:where += 1
      continue
    endif

    " is the current line a self-contained docblock?
    if getline(l:where) =~ '^\("""\|''''''\).\{-}\1$'
      let l:where += 1
      continue
    endif

    " is the current line starting/ending a docblock
    if getline(l:where) =~ '^"""' || getline(l:where) =~ "^'''"
      let l:in_docblock = strpart(getline(l:where), 0, 3)
      let l:where += 1
      continue
    endif

    " add a mark we can jump back to
    normal! mi
    call append(l:where -1, a:line)
    if get(b:, 'peter_auto_import_use_ale_fix', 0)
      ALEFix
    else
      Isort
    endif
    normal! `i
    return
  endwhile
endfun " }}}

fun! <SID>GetCurrentImports() " {{{
  let l:imports = {}
  for l:nr in range(1, line('$'))
    let l:match = matchlist(getline(l:nr), '^\s*\(from\|import\)\s\+\([a-zA-Z0-9_.]\+\)')
    if len(l:match)
      let l:imports[l:match[2]] = ''
    elseif getline(l:nr) =~ '^\%(def\|class\)\s'
      " stop searching as soon as we hit a function or class that isn't indented
      break
    endif
  endfor
  return l:imports
endfun " }}}


" Always ignore E265 (no space between '#' and comment text) and E116
" (unexpected indent (comment)) since my comment-adding mappings always
" produce these errors
Flake8Ignore E265 E116
