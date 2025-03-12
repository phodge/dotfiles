" Project: sharpen
" ProjectID: 516039f35cc4321ea8ee880d3ab2b71b7f9af5e4


function projectconfig.BufEnter() dict
  nmap <buffer> <space>t :call InTmuxWindow('./retest.sh', {'name': 'retest.sh', 'copy_env_vars': 'auto'})<CR>
  let b:isort_command = 'poetry run isort'
  let b:repo_todo_prefix = 'TODOS'
endfun
