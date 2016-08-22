" fix colors I don't like:
hi NonText ctermfg=White ctermbg=Blue cterm=None guifg=White guibg=#000022

hi! SpecialChar	ctermfg=Red                cterm=None
hi! SpecialChar	guifg=Red
hi! link Tag SpecialChar

" give ourselves some extra colours
hi! Include ctermfg=Blue cterm=None
hi! Keyword ctermfg=Yellow cterm=None
hi! Number ctermfg=Green cterm=None


highlight Statement guifg=LightYellow
highlight Normal guifg=#888888

highlight PreProc  guifg=#5555FF

hi Pmenu         ctermfg=Cyan    ctermbg=Blue   cterm=None
hi PmenuSel      ctermfg=White   ctermbg=Blue   cterm=Bold
hi PmenuSbar                     ctermbg=Cyan
hi PmenuThumb    ctermfg=White
hi Pmenu         guifg=Cyan    guibg=Blue
hi PmenuSel      guifg=White   guibg=Blue   gui=Bold
hi PmenuSbar                   guibg=Cyan
hi PmenuThumb    guifg=White

hi Title         ctermfg=None    ctermbg=Blue   cterm=Bold           guifg=NONE   guibg=DarkBlue  gui=Bold
hi TabLine       ctermfg=None    ctermbg=Black  cterm=Reverse        guifg=White  guibg=Black     gui=Reverse
hi TabLineSel    ctermfg=White   ctermbg=Blue   cterm=Bold,Reverse   guifg=Yellow guibg=DarkBlue  gui=Bold,Reverse
hi TabLineFill   ctermfg=None

hi LineNr ctermfg=Blue ctermbg=Black cterm=None
hi LineNr guifg=Blue guibg=#000022 gui=None

hi Folded ctermbg=Black ctermfg=Yellow cterm=Bold
hi Folded guibg=black guifg=LightYellow gui=Bold
hi clear FoldColumn
hi link FoldColumn Folded

hi! StatusLineNC                  ctermbg=Black  cterm=Reverse		            guibg=Black gui=Reverse
hi! StatusLine    ctermfg=White   ctermbg=Blue   cterm=Reverse,Bold	guifg=White guibg=DarkBlue gui=Reverse,Bold

" the sign column should have a black bg
hi SignColumn   ctermbg=black

hi! IncSearch     ctermfg=White     ctermbg=Magenta cterm=Bold         guifg=Red   guibg=Yellow gui=Bold

" Diff colors need to be more readable
hi DiffAdd	guibg=#333377
hi DiffChange	guibg=#884488
hi DiffText	guibg=#440000
hi DiffDelete	guibg=#000022 guifg=#333377

" for the 'colorcolumn' option
hi ColorColumn ctermbg=Blue cterm=none

" my own custom colors ...
hi link Urgent Error
hi Priority ctermfg=Blue ctermbg=Cyan cterm=Bold
hi Priority   guifg=Blue   guibg=Cyan cterm=Bold
hi Note ctermfg=Blue ctermbg=Black cterm=Bold
hi Note guifg=White guibg=Black gui=Bold
hi Dodgey ctermfg=Black ctermbg=White cterm=Bold
