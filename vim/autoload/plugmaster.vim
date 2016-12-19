fun! plugmaster#begin(localdir, storagedir, ...)
  let s:localdir = expand(a:localdir)
  let s:storagedir = expand(a:storagedir)
  call call('plug#begin', a:000)
  call <SID>DefineCommands()
endfun

fun! <SID>DefineCommands()
  com! -nargs=1 -complete=custom,PlugMasterGetNames PlugEdit call <SID>PlugEdit(<q-args>)
  com! -nargs=+ PlugMaster call <SID>PlugMaster(<args>)
endfun

let s:editable = []

fun! <SID>PlugMaster(repo, ...)
  let l:repo = a:repo
  if l:repo =~ '^phodge/'
    call add(s:editable, l:repo)
    let l:name = split(l:repo, '/')[1] . '.git'
    
    " are we currently editing this repo?
    let l:local = s:localdir . '/' . l:name
    if isdirectory(l:local)
      let l:repo = l:local
    endif
  endif

  " register the plugin with regular :Plug
  let l:args = [l:repo]
  call extend(l:args, a:000)
  call call('plug#', l:args)
endfun

fun! PlugMasterGetNames(A,L,P)
  return join(s:editable, "\n")
endfun


fun! <SID>PlugEdit(fullname)
  " make sure the storage dir exists
  if ! isdirectory(s:storagedir)
    silent exe '!mkdir -p '.s:storagedir
  endif

  " make sure the edit dir exists
  if ! isdirectory(s:localdir)
    silent exe '!mkdir -p '.s:localdir
  endif

  " if the plugin doesn't exist in the storage area, ask if the user wants to
  " clone it
  let [l:user, l:repo] = split(a:fullname, '/')
  let l:gitpath = printf('git@github.com:%s/%s.git', l:user, l:repo)
  let l:store = s:storagedir . '/' . l:repo . '.git'
  if ! isdirectory(l:store) && confirm('Git clone '.l:repo.'?')
    " create the clone now
    let l:cmd = 'git clone '.l:gitpath.' '.l:store
    if has('nvim')
      enew
      call termopen(l:cmd)
    else
      exe '!'.l:cmd
    endif
  endif

  if ! isdirectory(l:store)
    echoerr 'Local clone '.l:store.' does not exist'
    return
  endif

  " is there a symlink in s:localdir?
  let l:link = s:localdir . '/' . l:repo . '.git'
  if getftype(l:link) == ""
    " the link needs to be created
    exe printf('!ln -s %s %s', l:store, l:link)
  elseif getftype(l:link) != "link"
    echoerr printf("%s already exists but is not a symlink", l:link)
    return
  endif

  exe 'split' l:link
endfun
