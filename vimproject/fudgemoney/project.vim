" Project: fudgemoney
" ProjectID: 310eed2915cdca50d02c20d90f7110fc33b0b61f


" TODO: place your project init commands here
"
function projectconfig.BufEnter() dict
  let b:repo_todo_prefix = 'FM'

  nmap <buffer> <space>t :call InTmuxWindow('./retest.sh', {'name': 'retest.sh', 'copy_env_vars': 'auto'})<CR>
  nmap <buffer> <space>b :call InTmuxWindow('./rebuild.sh', {'name': 'rebuild.sh', 'copy_env_vars': 'auto'})<CR>

  if &l:filetype == 'typescriptreact'
    " XXX: I had to turn off lsp_eslint_d because it doesn't work in mobile/
    " any more with the upgraded eslint added to the mobile/ package.
    call peter#IDEFeaturesJS({'lsp_manage_imports': 1, 'lsp_eslint_d': 0, 'with_vue': 0})
  elseif &l:filetype == 'vue' || &l:filetype == 'typescript'
    call peter#IDEFeaturesJS({'lsp_manage_imports': 1, 'lsp_eslint_d': 1, 'with_vue': 1})
  endif
endfun

fun! projectconfig.api2024.filetypeDetect(bufnr, ext, basename, relname) dict
  if a:relname == 'git/config'
    "return 'gitconfig'
  endif
endfun
