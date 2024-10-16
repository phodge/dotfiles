com! -nargs=0 RepoTodoAdd call <SID>OpenNextTODO()
com! -nargs=0 RepoTodoList call <SID>OpenTodosList()

let s:repo_list_buffers = {}

fun! <SID>getRepoRoot() abort
  let l:root = projectroot#get()

  if type(l:root) != type('')
    throw 'ERROR: projectroot#get() did not return a string'
  endif

  if ! len(l:root)
    throw 'ERROR: projectroot#get() returned an empty string'
  endif

  return l:root
endfun

fun! <SID>getTodosDir(root) abort
  let l:todos_dir = a:root . '/TODO'

  if ! isdirectory(l:todos_dir)
    throw printf('ERROR: not a directory: %s', l:todos_dir)
  endif

  return l:todos_dir
endfun

fun! <SID>OpenNextTODO() abort
  if ! exists('b:repo_todo_prefix')
    throw 'ERROR: Cannot add a TODO: b:repo_todo_prefix is empty'
  endif

  let l:root = <SID>getRepoRoot()

  let l:todos_dir = <SID>getTodosDir(l:root)

  let l:stop = 10
  let l:next_todo_path = v:null
  let l:next_todo_name = v:null

  for l:check in range(1, 999)
    let l:numwidth = strlen(l:check)
    let l:todo_name = b:repo_todo_prefix . repeat('0', 3 - l:numwidth) . l:check
    let l:todo_path = printf('%s/%s.txt', l:todos_dir, l:todo_name)
    if bufexists(l:todo_path) || filereadable(l:todo_path)
      let l:stop = l:check + 100
      let l:next_todo_path = v:null
      let l:next_todo_name = v:null
      continue
    endif

    if l:next_todo_path is v:null
      let l:next_todo_path = l:todo_path
      let l:next_todo_name = l:todo_name
    endif

    if l:check > l:stop
      exe 'split' l:next_todo_path
      exe 'normal! I' . l:next_todo_name . ' '
      startinsert!
      return
    endif
  endfor

  throw 'ERROR: all TODO numbers are occupied'
endfun

fun! <SID>OpenTodosList() abort
  if ! exists('b:repo_todo_prefix')
    throw 'ERROR: Cannot list TODOs: b:repo_todo_prefix is empty'
  endif

  let l:root = <SID>getRepoRoot()

  let l:todos_dir = <SID>getTodosDir(l:root)

  let l:pattern = b:repo_todo_prefix . '\d\+\.txt'

  call <SID>OpenRepoListBuffer(l:root, b:repo_todo_prefix)

  " empty the file
  normal! ggdG

  " make a list of the files
  let l:todos = []
  call add(l:todos, '# from ' . l:todos_dir)
  for l:entry in readdir(l:todos_dir)
    let l:filepath = l:todos_dir . '/' . l:entry
    if l:entry =~ l:pattern
      let l:firstline = readfile(l:filepath, '', 1)[0]
      let l:pat = '^' . getcwd() . '/'
      "call add(l:todos, '# pat is ' . l:pat)
      let l:shortpath = substitute(l:filepath, l:pat, '', '')
      call add(l:todos, l:shortpath . ' ' . l:firstline)
    endif
  endfor

  call append(0, l:todos)

  " delete last line from end of file, then jump back to start
  normal! Gddgg

  syn keyword Operator PRIORITY
  syn keyword Typedef EASY
  syn keyword Statement VALUE
endfun

fun! <SID>OpenRepoListBuffer(root, prefix) abort
  let l:repo_list_buffer = get(s:repo_list_buffers, a:root, 0)
  if l:repo_list_buffer > 0 && bufexists(l:repo_list_buffer)
    let l:old_swb = &swb
    try
      let &swb = 'useopen'
      exe 'sbuf' l:repo_list_buffer
    finally
      let &swb = l:old_swb
    endtry
  else
    new
    setlocal buftype=nofile
    let s:repo_list_buffers[a:root] = bufnr('')
  endif

  " DOTFILES006: sometimes this gets clobbered by vim-project-config from
  " another project if global cwd is a different project
  let b:repo_todo_prefix = a:prefix

  exe 'lcd' a:root

  try
    exe 'file Repo TODOs - ' . a:root
  catch
    " TODO: DOTFILES007: don't silently ignore all errors
  endtry
endfun

