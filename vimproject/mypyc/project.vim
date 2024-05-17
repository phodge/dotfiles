" Project: mypy
" ProjectID: 5088f037c2b35a69a093bd41907d1c30bff85d5e+6f0826a9c169c4f05bb8938347ac0416f8154d91+8888d3ab0c94abd2af96c1c5c59697e94053e7b8+f86a2707a4cd81e827a1cb9a90f9892aaf3f2169

fun! projectconfig.BufRead() dict
    if &filetype == 'python'
        let b:ale_linters = ['mypy', 'flake8']
    endif
endfun

" TODO: place your project init commands here
