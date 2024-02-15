" Project: vim-project-config
" ProjectID: f2254f8c23eb85469fa64d50b4f3cb2250d75200

function projectconfig.BufEnter() dict
  let b:repo_todo_prefix = 'PC'
  nmap <buffer> <space>t :call InTmuxWindow('./retest.sh', {'saveto': 'retest.out', 'name': 'retest.sh'})<CR>
endfun
