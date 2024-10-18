" Project: fudgemoney
" ProjectID: 310eed2915cdca50d02c20d90f7110fc33b0b61f


" TODO: place your project init commands here
"
function projectconfig.BufEnter() dict
  let b:repo_todo_prefix = 'FM'
endfun

fun! projectconfig.api2024.filetypeDetect(bufnr, ext, basename, relname) dict
  if a:relname == 'git/config'
    "return 'gitconfig'
  endif
endfun
