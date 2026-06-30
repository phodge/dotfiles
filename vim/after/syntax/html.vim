" higher-priority syntax match to prevent ur?foo=bar&{{...} activating
" a javascript region at "&{"
syn cluster htmlPreProc add=djangoStringAmpersand
syn match djangoStringAmpersand /&\ze{{/ contained
hi! link djangoStringAmpersand Error
