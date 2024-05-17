" Project: dotfiles
" ProjectID: 2e64ab62f236579dbde9f7af1cfbd4e00a3fe715


function projectconfig.BufEnter() dict
  let b:repo_todo_prefix = 'DOTFILES'
endfun

fun! projectconfig.api2024.filetypeDetect(bufnr, ext, basename, relname) dict
  if a:relname == 'git/config'
    return 'gitconfig'
  endif
endfun
