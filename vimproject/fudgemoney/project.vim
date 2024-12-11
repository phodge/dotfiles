" Project: fudgemoney
" ProjectID: 310eed2915cdca50d02c20d90f7110fc33b0b61f


" TODO: place your project init commands here
"
function projectconfig.BufEnter() dict
  let b:repo_todo_prefix = 'FM'

  nmap <buffer> <space>t :call InTmuxWindow('./retest.sh', {'name': 'retest.sh', 'copy_env_vars': 'auto'})<CR>
  nmap <buffer> <space>b :call InTmuxWindow('./rebuild.sh', {'name': 'rebuild.sh', 'copy_env_vars': 'auto'})<CR>

  if &l:filetype == 'vue' || &l:filetype == 'typescript'
    let b:ale_enabled = 0
    " XXX: b:lsp_init_done is required due to a bug in vim-project-config
    " where it keeps executing the BufEnter function every time we switch
    " windows
    if ! get(b:, 'lsp_init_done', 0)
      lua require('PeteLSP').init_ts_ls({vue = true})
      lua require('PeteLSP').init_null_ls()
      LspStart
      let b:lsp_init_done = 1
    endif
    call PeteLSPKeymaps()
  endif
endfun

fun! projectconfig.api2024.filetypeDetect(bufnr, ext, basename, relname) dict
  if a:relname == 'git/config'
    "return 'gitconfig'
  endif
endfun
