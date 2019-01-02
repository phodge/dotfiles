nnoremap <F5> :Shell rg -ws <C-R><C-W><CR>
nnoremap <F6> :Shell rg -wis <C-R><C-W><CR>

augroup CustomFileType
augroup end
au! CustomFileType BufRead runtime/doc/**.txt setlocal filetype=help textwidth=78 conceallevel=0 colorcolumn=+2 sts=2 ts=8 sw=2 noet
