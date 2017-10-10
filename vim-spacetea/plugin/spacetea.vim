" define the mapping
" TODO: actually this probably should be removed and not be a default
nnoremap <space>t :SpaceTea test<CR>

" define the command
com! -nargs=* SpaceTea call spacetea#RunCommand(<q-args>)

augroup SpaceTea
augroup end
autocmd! SpaceTea BufWritePost * nested SpaceTea test
