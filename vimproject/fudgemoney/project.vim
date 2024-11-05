" Project: fudgemoney
" ProjectID: 310eed2915cdca50d02c20d90f7110fc33b0b61f


" TODO: place your project init commands here
"
function projectconfig.BufEnter() dict
  let b:repo_todo_prefix = 'FM'

  nmap <buffer> <space>t :call InTmuxWindow('./retest.sh', {'name': 'retest.sh', 'copy_env_vars': 'auto'})<CR>
endfun

fun! projectconfig.api2024.filetypeDetect(bufnr, ext, basename, relname) dict
  if a:relname == 'git/config'
    "return 'gitconfig'
  endif
endfun
