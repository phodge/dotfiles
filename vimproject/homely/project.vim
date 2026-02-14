" Project: homely
" ProjectID: 5bb293dcc62041608c876af89d90454708a3c4e3


" TODO: place your project init commands here
function projectconfig.BufEnter() dict
  if &l:filetype == 'python'
    let b:ale_linters = ['flake8', 'mypy', 'isort']
    "let b:ale_fix_on_save = 1
    "let b:ale_fixers = ['isort']
    let b:ale_python_mypy_executable = 'mypy'
  endif
  nnoremap <buffer> <space>t :call <SID>DoRetest()<CR>
endfun

fun! <SID>DoRetest() abort
  call InTmuxWindow('./retest.sh', {'name': 'retest.sh'})
endfun
