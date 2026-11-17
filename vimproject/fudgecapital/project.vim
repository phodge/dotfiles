" Project: fudgecapital
" ProjectID: c4a1c1d1c97be6986f6d1d8486dcd45a840268e4


" TODO: place your project init commands here
function projectconfig.BufEnter() dict
  let b:repo_todo_prefix = 'FCTODO'
  let g:MySchema_engine = 'sqlite'
  let b:MySchema_sqlite_databases = ['.local/fudgecapital.sqlite3']
endfun
