function! editrealpath#EditRealPath()
  let l:filename = expand('%:p')
  let l:realpath = resolve(l:filename)

  " if the current buffer has been modified, then we can't re-edit
  if &l:modified
    return
  endif

  " if we are editing the real file, don't try and open it up
  if l:realpath == l:filename
    return
  endif

  " if the realpath file doesn't exist, don't try and edit it
  if ! filereadable(l:realpath)
    return
  endif

  " remember local options/settings?
  let l:oldbufnr = bufnr("")
  " edit a new empty file (this will copy options/cwd etc from the buffer)
  " TODO: not entirely sure it is desirable to copy options - why not just
  " :edit the new buffer directly then :bwipeout the old one?
  if g:editrealpath#strategy == 'enew'
    enew
    " wipe out the old buffer
    execute 'bwipeout' l:oldbufnr
    " re-edit the old file again but with the real path
    " NOTE: because we use :edit with the new empty buffer opened, we get all
    " our local options back
    execute 'edit' l:realpath
  else
    execute 'edit' l:realpath
    " wipe out the old buffer
    execute 'bwipeout' l:oldbufnr
  endif
endfunction
