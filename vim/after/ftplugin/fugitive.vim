exec 'nnoremap <buffer> dv ' . maparg('dv', 'n') . '20<C-W>+gg:exe diff_hlID(1, 0) ? "" : "norm ]c"<CR>'

" we want 'cc' mapping to commit _without_ hooks because the visual feedback
" isn't great and they are too slow on some projects
nnoremap <buffer> cc :<C-U>Git commit --no-verify<CR>
