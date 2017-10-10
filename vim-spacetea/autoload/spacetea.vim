let s:pyscript = expand('<sfile>:p:h:h').'/python/spacetea/plugin.py'

fun! <SID>GetOpt(name, default)
  return get(b:, a:name, get(g:, a:name, a:default))
endfun

fun! spacetea#RunCommand(args)
  call <SID>CheckJob()

  " RPC call to the job asking it to do something
  if <SID>GetOpt('spacetea_async', 1)
    echoerr 'TODO: do it asynchronously'
  else
    call rpcrequest(s:job_id, 'spacetea_runcommand', a:args)
  endif
endfun


fun! spacetea#Stop()
  if exists('s:job_id')
    call <SID>KillOldJob()
  endif

  " source this file again
endfun

fun! <SID>CheckJob()
  if exists('s:job_id')
    let [l:status] = jobwait([s:job_id], 0)

    " the job is currently running
    if l:status == -1
      return
    endif

    let g:bar = l:status

    " check that it hasn't terminated
    if l:status == -2
      unlet s:job_id
    elseif l:status == -3
      unlet s:job_id
    elseif l:status >= 0
      unlet s:job_id
    endif
  endif

  if ! exists('s:job_id')
    " TODO: start the background job
    let s:job_id = jobstart(['python3', s:pyscript], {"rpc": v:true, "on_stderr": function('<SID>StderrHandler')})
  endif
endfun

fun! <SID>StderrHandler(job_id, data, event)
  " TODO: we can't rely on this file being available
  let l:logfile = expand(get(g:, 'spacetea_logfile', '~/.nvimlog'))
  call writefile([printf('<stderr from job #%s>', a:job_id)], l:logfile, 'a')
  call writefile(a:data, l:logfile, 'a')
endfun
