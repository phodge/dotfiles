exec 'nnoremap <buffer> dv ' . maparg('dv', 'n') . '20<C-W>+gg:exe diff_hlID(1, 0) ? "" : "norm ]c"<CR>'
