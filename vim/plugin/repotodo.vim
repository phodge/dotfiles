com! -nargs=0 RepoTodoAdd call <SID>OpenNextTODO()

fun! <SID>OpenNextTODO()
  if ! exists('b:repo_todo_prefix')
    throw 'ERROR: Cannot add a TODO: b:repo_todo_prefix is empty'
  endif

  let l:root = projectroot#get()

  if type(l:root) != type('')
    throw 'ERROR: projectroot#get() did not return a string'
  endif

  if ! len(l:root)
    throw 'ERROR: projectroot#get() returned an empty string'
  endif

  let l:todos_dir = l:root . '/TODO'

  if ! isdirectory(l:todos_dir)
    throw printf('ERROR: not a directory: %s', l:todos_dir)
  endif

  for l:check in range(1, 999)
    let l:numwidth = strlen(l:check)
    let l:todoname = b:repo_todo_prefix . repeat('0', 3 - l:numwidth) . l:check
    let l:todo_path = printf('%s/%s.txt', l:todos_dir, l:todoname)
    if bufexists(l:todo_path) || filereadable(l:todo_path)
      continue
    endif

    exe 'split' l:todo_path
    exe 'normal! I' . l:todoname . ' '
    startinsert!
    return
  endwhile

  throw 'ERROR: all TODO numbers are occupied'
endfun

