" SimpylFold is too slow for large files, revert to indent-based folding for
" very big files
if &l:filetype == 'python' && line("$") > 2000
  setlocal foldmethod=indent
endif
