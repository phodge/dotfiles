" fix colors I don't like:
if has('nvim')
  hi! Normal guibg=#1A1A1A
endif
hi NonText ctermfg=White ctermbg=blue cterm=None guifg=#888888 guibg=#1A1A1A

" XXX: this seemed to be necessary for neovim 0.8.0 because EndOfBuffer had no
" hl information whatsoever
hi! link EndOfBuffer NonText

hi! SpecialChar	ctermfg=Red cterm=None
hi! SpecialChar	guifg=#FFBB00
hi! link Tag SpecialChar

" give ourselves some extra colours
hi! Include ctermfg=Blue cterm=None guifg=#5555BB
hi! Keyword ctermfg=Yellow cterm=None guifg=#FFFF88
hi! Number ctermfg=Green cterm=None guifg=#008800

hi Delimiter ctermfg=DarkMagenta guifg=#DD00DD
hi String ctermfg=Magenta guifg=#AA00AA


highlight Statement guifg=#FFFF00 gui=None
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

" use black bg for floating window to make it stand out a little
hi! NormalFloat guibg=black

" used by Skylight plugin
hi! SkylightBorder guifg=orange guibg=None

hi Title         ctermfg=None    ctermbg=Blue   cterm=Bold           guifg=NONE   guibg=DarkBlue  gui=Bold
hi TabLine       ctermfg=None    ctermbg=Black  cterm=Reverse        guifg=White  guibg=Black     gui=Reverse
hi TabLineSel    ctermfg=White   ctermbg=Blue   cterm=Bold,Reverse   guifg=Yellow guibg=DarkBlue  gui=Bold,Reverse
hi TabLineFill   ctermfg=None

hi LineNr ctermfg=Blue ctermbg=Black cterm=None
hi LineNr guifg=#555555 guibg=#1A1A1A gui=None

hi Folded ctermbg=Black ctermfg=Yellow cterm=Bold
hi Folded guibg=black guifg=yellow gui=Bold
hi FoldColumn guifg=Yellow guibg=#1A1A1A ctermfg=Yellow ctermbg=Black

hi! StatusLineNC                  ctermbg=Black  cterm=Reverse      guifg=Grey  guibg=Black gui=Reverse
hi! StatusLine    ctermfg=White   ctermbg=Blue   cterm=Reverse,Bold guifg=White guibg=DarkBlue gui=Reverse,Bold
" NOTE: added for neovim 0.8.0
hi VertSplit      ctermfg=Grey    ctermbg=Black                     guifg=Grey  guibg=None

" the sign column should have a black bg
hi SignColumn   ctermbg=black guibg=black

hi! IncSearch     ctermfg=White     ctermbg=Magenta cterm=Bold         guifg=Red   guibg=Yellow gui=Bold

" Diff colors need to be more readable
hi DiffAdd	  guibg=#333377
hi DiffChange	guibg=#884488
hi DiffText	  guibg=#440000
hi DiffDelete	guibg=#000022 guifg=#333377

" for the 'colorcolumn' option
hi ColorColumn ctermbg=Blue cterm=none guibg=#440044
hi ColorColumn2 ctermbg=Red cterm=none guibg=#880000

" my own custom colors ...
hi link Urgent Error
hi Priority ctermfg=Blue ctermbg=Cyan cterm=Bold
hi Priority   guifg=Blue   guibg=Cyan cterm=Bold
hi Note ctermfg=Blue ctermbg=Black cterm=Bold
hi Note guifg=White guibg=Black gui=Bold
hi Dodgey ctermfg=Black ctermbg=White cterm=Bold
