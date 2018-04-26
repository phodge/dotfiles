" :-(
"
" The SASS syntax comment region starts at newline, while SCSS comment region matches right at the
" '/' in '/*'. This means that scssComment region will never get a chance to match, and block
" comments won't be highlighted correctly.
"
" To fix this, we need to destroy the sassCssComment region altogether when viewing .scss syntax
syn clear sassCssComment
