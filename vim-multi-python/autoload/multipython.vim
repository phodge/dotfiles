let s:versions = {2: ["2.7", "2.4"], 3: []}
for s:i in range(20)
  call add(s:versions[3], printf("3.%d", s:i))
endfor
unlet s:i

fun! multipython#setpy3(version, ...) " {{{
  let l:reason = a:0 ? a:1 : "setpy3() called directly"
  let l:printversions = a:0 > 1 ? a:2 : 1
  call <SID>SetPyVersion(3, a:version, l:reason, l:printversions)
endfun " }}}

fun! multipython#setpy2(version, ...) " {{{
  let l:reason = a:0 ? a:1 : "setpy2() called directly"
  let l:printversions = a:0 > 1 ? a:2 : 1
  call <SID>SetPyVersion(2, a:version, l:reason, l:printversions)
endfun " }}}

fun! multipython#togglepy2() " {{{
  call <SID>CyclePy(2, -1, "Toggled by user")
endfun " }}}

fun! multipython#togglepy3() " {{{
  call <SID>CyclePy(3, -1, "Toggled by user")
endfun " }}}

fun! multipython#setpy2paths(paths) " {{{
  call <SID>SetMajorPaths(2, a:paths)
endfun " }}}

fun! multipython#setpy3paths(paths) " {{{
  call <SID>SetMajorPaths(3, a:paths)
endfun " }}}

fun! <SID>SetMajorPaths(major, paths) " {{{
  let l:dict = <SID>GetMajorDict(a:major)
  let l:dict["bin_paths"] = []
  for l:path in a:paths
    call add(l:dict["bin_paths"], expand(l:path))
  endfor
endfun " }}}

fun! multipython#wantpy2() " {{{
  return get(<SID>GetMajorDict(2), "min_version", "") != ""
endfun " }}}

fun! multipython#wantpy3() " {{{
  return get(<SID>GetMajorDict(3), "min_version", "") != ""
endfun " }}}

fun! <SID>CyclePy(major, current, reason) " {{{
  let l:options = [""] + s:versions[a:major]

  if a:current == -1
    let l:current = get(<SID>GetMajorDict(a:major), "min_version", "")
  else
    let l:current = a:current
  endif

  " what's our current idx in the list?
  let l:pos = index(l:options, l:current)
  if l:pos != -1
    " remove the current item from the list
    call remove(l:options, l:pos)
    " build a new list of things to try that first includes everything *after*
    " l:pos and then wraps around from the start
    let l:trysequence = l:options[l:pos:]
    if l:pos > 0
      let l:trysequence += l:options[0:(l:pos-1)]
    endif
  else
    let l:trysequence = l:options
  endif

  " try to switch to each of the versions in l:trysequence ... whichever one
  " is available first
  for l:try in l:trysequence
    " if the next thing to try is "", then we try and disable that major python support
    if l:try == ""
      call <SID>SetPyVersion(a:major, "", a:reason, 1)
      return
    endif

    " can we switch to this python version?
    if executable('python'.l:try)
      call <SID>SetPyVersion(a:major, l:try, a:reason, 1)
      return
    endif
  endfor

  " couldn't switch python version, so just disable it
  call <SID>SetPyVersion(a:major, "", a:reason, 0)
  " print the current status
  echohl WarningMsg
  echon printf("Py%d disabled - no python%d.x executables. ", a:major, a:major)
  echohl None
  call multipython#printversions()
endfun " }}}

" returns the dict of settings for the current major python version. A new
" dict is added to b:__multipython[major] if there isn't one there yet
fun! <SID>GetMajorDict(major) " {{{
  if ! exists('b:__multipython')
    let b:__multipython = {}
  endif
  let l:dict = get(b:__multipython, a:major, {})
  let b:__multipython[a:major] = l:dict
  return l:dict
endfun " }}}

fun! <SID>SetPyVersion(major, exact, reason, printversions) " {{{
  " create a dict for the current python version if it doesn't already exist
  let l:majordict = <SID>GetMajorDict(a:major)

  " disable support quickly if that's what's wanted
  if a:exact == ""
    let l:majordict["min_version"] = ""
    let l:majordict["reason"] = a:reason
    if a:printversions
      call multipython#printversions()
    endif
    " call callbacks
    for l:Funcref in get(b:__multipython, "all_callbacks", [])
      call l:Funcref()
    endfor
    return
  endif

  if a:exact == 1
    " the user wants to switch to the first available version
    call <SID>CyclePy(a:major, "", a:reason)
    return
  endif

  if a:major == 3 && a:exact =~ '^3.\d\+$'
    " ok
  elseif a:major == 2 && a:exact =~ '^2.[47]$'
    " ok
  else
    echoerr printf("Invalid py%d version %s", a:major, a:exact)
  endif

  " do we have the appropriate executable?
  let l:python = 'python'.a:exact
  if ! executable(l:python)
    echoerr printf("Can't set py%d to %s: No %s exectuable found", a:major, a:exact, l:python)
  endif

  " set the current python version now
  let l:majordict["min_version"] = a:exact
  let l:majordict["reason"] = a:reason
  if a:printversions
    call multipython#printversions()
  endif
  " call callbacks
  for l:Funcref in get(b:__multipython, "all_callbacks", [])
    call l:Funcref()
  endfor
endfun " }}}

fun! multipython#printversions() " {{{
  " what py2 version is supported?
  let l:py2dict = <SID>GetMajorDict(2)
  let l:py3dict = <SID>GetMajorDict(3)

  let l:py2 = get(l:py2dict, "min_version", "")
  let l:py3 = get(l:py3dict, "min_version", "")
  echohl None
  echo "Python compatibility:"
  if l:py2 != ""
    echohl Statement
    echon " ".l:py2."+"
    echohl None
    echon printf(" (%s)", l:py2dict["reason"])
  endif
  if l:py3 != ""
    echohl Question
    echon " ".l:py3."+"
    echohl None
    echon printf(" (%s)", l:py3dict["reason"])
  endif
  if l:py2 == "" && l:py3 == ""
    echohl Operator
    echon " None"
  endif
  echohl None
endfun " }}}

" returns 1 if python versions have been set for the current buffer
fun! multipython#versionsdetected() " {{{
  let l:py2dict = <SID>GetMajorDict(2)
  let l:py3dict = <SID>GetMajorDict(3)
  return has_key(l:py2dict, "min_version") || has_key(l:py3dict, "min_version")
endfun " }}}

" resets python versions for the current buffer
fun! multipython#resetversions() " {{{
  for l:major in [2, 3]
    let l:majordict = <SID>GetMajorDict(l:major)
    if has_key(l:majordict, "min_version")
      call remove(l:majordict, "min_version")
    endif
  endfor
endfun " }}}

fun! <SID>GetVenvInfo()
  " TODO: we could cache this to make it faster
  let l:try = expand('%:p')
  while strlen(l:try) > 2
    let l:try = fnamemodify(l:try, ':h')

    if isdirectory(l:try.'/bin') && filereadable(l:try.'/bin/activate')
      let l:pyexe = l:try.'/bin/python'
      let l:basename = fnamemodify(resolve(l:pyexe), ':t')
      if l:basename =~ '^python[23]\.[0-9]\+$'
        let l:major = str2nr(strpart(l:basename, 6, 1))
        let l:exact = strpart(l:basename, 6)
        return [l:major, l:exact, l:try.'/bin']
      endif
    endif
  endwhile

  return []
endfun

" examines the current file to try and determine which python versions should
" be supported
fun! multipython#detectversions() " {{{
  let l:venv_py = <SID>GetVenvInfo()
  if len(l:venv_py)
    " switch to that python version
    let [l:major, l:exact, l:bin] = l:venv_py
    call <SID>SetPyVersion(l:major, l:exact, "Virtualenv at ".l:bin, 0)
    return 1
  endif
  
  if getline('1') =~ '^#!.*\bpython2'
    " try to enable python2
    call <SID>CyclePy(2, "", "python2 hash-bang")
    " disable py3
    call <SID>SetPyVersion(3, "", "python2 hash-bang", 0)
    return 1
  elseif getline('1') =~ '^#!.*\bpython3'
    " try to enable python3
    call <SID>CyclePy(3, "", "python3 hash-bang")
    " disable python2
    call <SID>SetPyVersion(2, "", "python3 hash-bang", 0)
    return 1
  else
    " we couldn't detect python versions automatically
    return 0
  endif
endfun

fun! multipython#getpythoncmd(major, cmd, mustexist) " {{{
  " if we're in a virtualenv, always try and use that version of the command
  " first
  let l:venv = <SID>GetVenvInfo()
  if len(l:venv) && (a:major == 0 || a:major == l:venv[0])
    " if there is a virtualenv and it has the same major version (or we don't
    " care what majoy python version we use) then look for the cmd in the
    " virtualenv
    let l:venv_cmd = l:venv[2].'/'.a:cmd
    if executable(l:venv_cmd)
      return l:venv_cmd
    endif
  endif

  if a:major == 0
    let l:check = []
    if get(<SID>GetMajorDict(3), "min_version", "") != ""
      call add(l:check, 3)
    endif
    if get(<SID>GetMajorDict(2), "min_version", "") != ""
      call add(l:check, 2)
    endif
  elseif a:major == 3
    let l:check = [3]
  elseif a:major == 2
    let l:check = [2]
  endif

  " if we have a specif version of python to check, look for the executable
  " now
  for l:major in l:check
    for l:path in get(<SID>GetMajorDict(l:major), "bin_paths", [])
      if executable(l:path.'/'.a:cmd)
        return l:path.'/'.a:cmd
      endif
    endfor
  endfor

  " raise an error if we need to
  if a:mustexist
    let l:which = a:major == 0 ? 'py2 or py3' : 'py'.a:major
    echoerr printf("Could not find %s for %s", a:cmd, l:which)
  endif
  return ""
endfun

if ! exists('s:callbacks')
  let s:callbacks = []
endif

fun! multipython#addcallback(funcref)
  if ! exists('b:__multipython')
    let b:__multipython = {}
  endif
  let l:callbacks = get(b:__multipython, "all_callbacks", [])
  " add the callback if it isn't in there yet
  if index(l:callbacks, a:funcref) == -1
    call add(l:callbacks, a:funcref)
    let b:__multipython["all_callbacks"] = l:callbacks
  endif
endfun
