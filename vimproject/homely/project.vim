" Project: homely
" ProjectID: 5bb293dcc62041608c876af89d90454708a3c4e3


" TODO: place your project init commands here
function projectconfig.BufEnter() dict
  nnoremap <buffer> <space>t :call InTmuxWindow('./retest.sh', {'name': 'retest.sh'})<CR>
endfun
