" Project: tradebot
" ProjectID: 783340b029fa9697a11927f243ea3f17ad8b65a1


" TODO: place your project init commands here
function projectconfig.BufEnter() dict
  let b:repo_todo_prefix = 'TBTODO'
  let b:isort_command = 'uv run isort'
endfun
