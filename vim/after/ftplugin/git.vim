" strip a/ or b/ off the front of a filename so that we can use 'gf' to open a
" file from a '--- a/some/file' or '+++ b/some/file' line
" NOTE: this is also use in ftplugin/diff.vim
setlocal includeexpr=substitute(v:fname,'^[ab]/','','')
