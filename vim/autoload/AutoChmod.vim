fun! <SID>Verbose(message)
  if &verbose >= 1
    echomsg 'AutoChmod: ' . a:message
  endif
endfun

fun! AutoChmod#PostWrite()
  " skip rust files as the syntax overlaps
  if &l:filetype == 'rust'
    call <SID>Verbose(printf("Skipped - buftype is '%s'", &l:filetype))
    return
  endif

  " if the first line of the file doesn't start with #! then there's nothing
  " for us to do
  if getline(1) !~ '^#!'
    call <SID>Verbose("Not required - file doesn't start with '#!'")
    return
  endif

  " skip buffers that aren't real files
  if &buftype != ""
    call <SID>Verbose("Not possible - 'buftype' option is set")
    return
  endif

  " skip buffers using special protocols (http://, fugitive:// etc)
  let l:protocol = matchstr(bufname(""), '^\w\+://')
  if l:protocol != ""
    call <SID>Verbose(printf("Skipped - buffer name starts with '%s'", l:protocol))
    return
  endif

  " if the user chose not to chmod the file, or chmod'ing failed for other
  " reasons, abort
  if exists('b:autochmod_skip')
    call <SID>Verbose(printf("Skipping - b:autochmod_skip is '%s'", b:autochmod_skip))
    if type(b:autochmod_skip) == type(1) && b:autochmod_skip != 0
      return
    elseif b:autochmod_skip != ""
      return
    endif
  endif

  " work out what permissions are missing from the file
  try
    let [l:curr, l:want] = AutoChmod#GetMissingPermissions()
  catch
    let b:autochmod_skip = 'AutoChmod not possible: ' . v:exception
    echoerr 'AutoChmod not possible: ' . v:exception
  endtry

  if l:curr == l:want
    call <SID>Verbose(printf("Current permissions '%s' are correct", l:curr))
    return
  endif

  let l:choice = 0
  while l:choice == 0
    echohl Question
    echo 'AutoChmod: Change permissions to '
    for i in range(9)
      let l:new = strpart(l:want, i, 1)
      if strpart(l:curr, i, 1) == l:new
        echohl Search
      else
        echohl IncSearch
      endif
      echon l:new
    endfor
    echohl Question
    echon '? '
    let l:choice = getchar()

    if l:choice == 27
      " if the user hits escape, dont' change permissions, but also don't
      " remember the choice
      return
    endif

    if toupper(nr2char(l:choice)) == 'N'
      " remember the user's choice
      let b:autochmod_skip = 'User chose not to chmod'
      return
    endif
    if toupper(nr2char(l:choice)) == 'Y'
      break
    endif
    " clear screen
    echo
    let l:choice = 0
  endwhile

  call <SID>Verbose(printf("Setting %s permissions to %s", expand("%"), l:want))
  let result = setfperm(bufname(""), l:want)
  echomsg printf("AutoChmod: Set %s permissions to %s", bufname(""), l:want)
endfun

fun! AutoChmod#GetMissingPermissions()
  let currentstr = getfperm(bufname(""))
  if type(currentstr) != type("") || currentstr == ""
    echoerr "Couldn't get permissions for the current buffer"
  endif

  let curr = split(currentstr, '\zs')
  let want = copy(curr)

  if curr[0] == 'r' && curr[2] != 'x'
    let want[2] = 'x'
  endif

  if curr[3] == 'r' && curr[5] != 'x'
    let want[5] = 'x'
  endif

  if curr[6] == 'r' && curr[8] != 'x'
    let want[8] = 'x'
  endif

  return [currentstr, join(want, "")]
endfun
