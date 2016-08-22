augroup AlwaysCD
augroup end

autocmd! AlwaysCD BufReadPost * if strlen(getcwd()) | exe 'cd '.getcwd() | endif

