if ! exists('g:vim_peter')
  let g:vim_peter = 1
endif

if ! exists('g:peter_use_builtin_php_syntax')
  let g:peter_use_builtin_php_syntax = 0
endif

if ! exists('g:hackymappings')
  let g:hackymappings = 0
endif

" sensible defaults to start with
if &compatible
  setglobal nocompatible
endif

set confirm

" when to use LSP and YCM
let s:use_lsp = has('nvim') && get(g:, 'peter_use_lsp', 0)
let s:use_ycm = has('nvim') && get(g:, 'peter_use_ycm', 0) && !s:use_lsp

" 256-color mode for vim8/neovim
if exists('&termguicolors')
  " NOTE: this needs to be set at startup
  set termguicolors

  " NOTE: I had to manually set these options to get truecolor to work in vim8
  " in iTerm2/tmux, but I think I actually prefer sticking with 256-color mode
  " in regular vim because it helps me figure out which one I'm using ...
  if ! has('nvim')
    let &t_8f = "\<Esc>[38;2;%lu;%lu;%lum"
    let &t_8b = "\<Esc>[48;2;%lu;%lu;%lum"
  endif

  " vim8 needs explicit terminal codes if we want cursor shape changing to
  " work
  if ! has('nvim')
    let &t_SI = "\<Esc>[6 q"
    let &t_SR = "\<Esc>[4 q"
    let &t_EI = "\<Esc>[2 q"
  endif

elseif has('nvim') && &term == 'screen'
  " TODO: what was this for?
  "set term=screen-256color
endif

" we need to work out what tmux session we're running under
let g:tmux_session = ''
if executable('tmux') && exists('*systemlist')
  " NOTE: I experienced a bug where vim 8.0.007's systemlist() would return an
  " empty list, but only during startup
  let s:result = systemlist('tmux display-message -p "#S"')
  if type(s:result) == type([]) && len(s:result)
    let g:tmux_session = s:result[0]
  endif
endif

" runtimepath modifications {{{

  if g:allow_rtp_modify

    " if we are using neovim, we have to manually add ~/.vim to rtp
    if has('nvim')
      let &runtimepath = '~/.vim,' . &runtimepath . ',~/.vim/after'
    endif

    " add our own vim/ and vim-multi-python/ folders to runtimepath
    let s:specials = ['vim', 'vim-multi-python', 'vim-git-magic']
    for s:name in s:specials
      let s:local = expand('<sfile>:h').'/'.s:name
      let &runtimepath = printf('%s,%s,%s/after', s:local, &runtimepath, s:local)
    endfor
    unlet s:specials
    unlet s:name
    unlet s:local

    " add the <vim-est> thing if it is present
    if isdirectory(expand('~/src/vim-est.git'))
      let &runtimepath = &runtimepath . ','.expand('~/src/vim-est.git')
    endif

    " vimstatic area for things we may download manually
    let &runtimepath = '~/.vimstatic,' . &runtimepath
  endif

" }}}


" set up Vundle if it's present and not in &rtp yet
let s:plugpath = $HOME.'/.vim/autoload/plug.vim'
if filereadable(s:plugpath)
  " use different path depending on vim/nvim
  let s:plugins = has('nvim') ? '~/.nvim/plugged' : '~/.vim/plugged'

  call plugmaster#begin('~/src/plugedit', '~/src', s:plugins) " {{{

  if g:tmux_session == 'SPACETEA-DEV'
    Plug 'phodge/spacetea.vim'
  endif

  " why not
  Plug 'editorconfig/editorconfig-vim'
  let g:EditorConfig_exclude_patterns = ['fugitive://.*']

  " the awesome Jedi library for python
  Plug 'davidhalter/jedi-vim'
  let g:jedi#use_splits_not_buffers = "winwidth"
  " NOTE: I'm disabling call signatures because A) it doesn't seem to work and
  " B() vim isfreezing and I don't know why
  let g:jedi#show_call_signatures = 0
  let g:jedi#smart_auto_mappings = 0
  let g:jedi#popup_on_dot = 0

  " ALE setup {{{

    Plug 'w0rp/ale'

    let g:ale_linters = get(g:, 'ale_linters', {})
    let g:ale_linters.php = ['php', 'phan', 'phpcs', 'psalm']

    let g:ale_php_cs_fixer_use_global = 1
    let g:ale_php_cs_fixer_executable = $HOME.'/.config/composer/vendor/bin/php-cs-fixer'
    let g:ale_fixers = get(g:, 'ale_fixers', {})
    let g:ale_fixers.php = ['php_cs_fixer']

    " XXX: Workaround for: https://github.com/dense-analysis/ale/issues/2704
    " Because mypy since 0.710 outputs reveal_type() at "note" level, Ale
    " ignores it. The executable script here uses regex to replace the "note"
    " with "error" so that Ale will show the output from reveal_type()
    let g:ale_python_mypy_executable = 'mypy-escalated-reveal-type'
    let g:ale_python_mypy_use_global = 1

    if ! s:use_lsp
      " when not using LSP plugin, allow Ale to talk to the language server
      "let g:ale_php_langserver_use_global = 1
      "let g:ale_php_langserver_executable = $HOME.'/.config/composer/vendor/felixfbecker/language-server/bin/php-language-server.php'
      "call add(g:ale_linters.php, 'langserver')

      if ! s:use_ycm
        " when neither LSP or YCM is enabled, ALE will perform these things:
        nnoremap <space>d :ALEGoToDefinition<CR>
      endif
    endif

  " }}}

  if s:use_lsp
    " language servers
    Plug 'autozimu/LanguageClient-neovim', {
          \ 'branch': 'next',
          \ 'do': 'bash install.sh',
          \ }
    let g:LanguageClient_serverCommands = {'php': ['tcp://127.0.0.1:12346']}

    " don't use language server for linting - Ale does a better job of this already
    let g:LanguageClient_diagnosticsEnable = 0

    " \ 'rust': ['~/.cargo/bin/rustup', 'run', 'stable', 'rls'],
    " \ 'javascript': ['/usr/local/bin/javascript-typescript-stdio'],
    " \ 'javascript.jsx': ['tcp://127.0.0.1:2089'],
    " \ 'python': ['/usr/local/bin/pyls'],
    " \ }

    Plug 'Shougo/deoplete.nvim', {'do': 'UpdateRemotePlugins'}

    "Plug 'roxma/LanguageServer-php-neovim', {'do': 'composer install && composer run-script parse-stubs'}

    aug PeterLSP
    au!
    au FileType php nnoremap <buffer> <space>d :sp <BAR> call LanguageClient_textDocument_definition()<CR>
    au FileType php nnoremap <buffer> <space>u :sp <BAR> call LanguageClient_textDocument_references()<CR>
    au FileType php nnoremap <buffer> <space>r :sp <BAR> call LanguageClient_textDocument_rename()<CR>
    aug end
  elseif s:use_ycm
    " when in neovim land, use YouCompleteMe
    Plug 'Valloric/YouCompleteMe'

    " when jumping to definitions, do so in a new split
    let g:ycm_goto_buffer_command = 'horizontal-split'

    " don't map <tab> key, it interferes with UltiSnips
    let g:ycm_key_list_select_completion = []

    let g:ycm_min_num_of_chars_for_completion = 99
    let g:ycm_min_num_identifier_candidate_chars = 99

    nnoremap gd :split<CR>:YcmCompleter GoTo<CR>
    nnoremap <space>r :YcmCompleter RefactorRename <C-R><C-W>
    nnoremap <space>t :YcmCompleter GetType<CR>

    " don't use jedi completions if we have YCM enabled
    let g:jedi#completions_enabled = 0
  endif

  " ArgWrap {{{ 

    Plug 'FooSoft/vim-argwrap'
    let g:argwrap_tail_comma = 1
    nnoremap <space>a :ArgWrap<CR>

  " }}}

  if has('macunix') " Kapeli Dash docs viewer for Mac {{{
    Plug 'rizzatti/dash.vim'
    nnoremap <S-F5> :Dash <cword><CR>
  endif " }}}


  Plug 'EinfachToll/DidYouMean'
  Plug 'christoomey/vim-tmux-navigator'
  Plug 'hynek/vim-python-pep8-indent'

  Plug 'tmhedberg/SimpylFold'

  " python imports {{{

    " adds :ImportName and :ImportNameHere commands
    Plug 'mgedmin/python-imports.vim'

  " }}}

  " python code formatting via Black
  " TODO: I've had to uninstall this because it keeps complaining about
  " needing Vim7+ with Python3.6
  Plug 'psf/black'

  " make inactive windows dim slightly
  let g:vimade = get(g:, 'vimade', {})
  let g:vimade.fadelevel = 0.5
  let g:vimade.basebg = '#000000'
  Plug 'TaDaa/vimade', get(g:, 'want_vimade', 0) ? {} : {'on': []}

  if has('nvim') && v:version >= 704
    Plug 'SirVer/ultisnips', v:version >= 704 ? {} : {'on': []}
  else
    " NOTE: we need to use the older SnipMate on vim because UltiSnips keeps
    " producing errors in vim 8.1
    Plug 'MarcWeber/vim-addon-mw-utils'
    Plug 'tomtom/tlib_vim'
    Plug 'garbas/vim-snipmate'
  endif
  Plug 'sjl/Clam.vim'
  Plug 'tmux-plugins/vim-tmux'
  Plug 'easymotion/vim-easymotion'
  " TODO: revisit this and see if we can get some nice mappings up
  Plug 'brooth/far.vim'

  if has('nvim') && get(g:, 'want_fzf', 0)
    Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all'}
    Plug 'junegunn/fzf.vim'
    nnoremap <C-P> :FZF<CR>
    nnoremap \\ :call fzf#vim#grep('git-branch-status --short --quiet', 0)<CR>
    let g:fzf_action = {
                \ 'ctrl-t': 'tab split',
                \ 'ctrl-x': 'split',
                \ 'ctrl-v': 'vsplit',
                \ }
    " I just want to be able to hit enter to open a file in a new split
    let g:fzf_action['enter'] = 'split'
  else
    Plug 'ctrlpvim/ctrlp.vim'
  endif

  " git-gutter
  if has('signs') && v:version >= 704
    Plug 'airblade/vim-gitgutter'

    " make it disabled by default, by toggle-able by space-g
    let g:gitgutter_enabled = 0
    nnoremap <space>g :GitGutterToggle<CR>

    " NOTE: you can also use ]c and [c to move to next/previous hunks

    " reduce CursorHold time from 4s to .25s for faster gutter response
    set updatetime=250
  else
    nnoremap <space>g :echoerr 'vim-gitgutter is not installed'<CR>
  endif

  " Cython
  Plug 'lambdalisue/vim-cython-syntax'

  Plug 'vim-scripts/sudo.vim'

  "Plug 'justinmk/vim-sneak'

  if has('nvim')
    " TODO: figure out how to replace flake8 with neomake + something else
    Plug 'neomake/neomake'
  endif

  " for ansible
  Plug 'pearofducks/ansible-vim'

  " additional motions/targets:
  " "quote": '"`
  " "separator": , . ; : + - = ~ _ * # / | \ & $
  " "pair": one of the following: b() B{} [] <> t <quote> <separator>
  "         If you use n<pair>, cursor will seek forward to the next pair,
  "         l<pair> seeks to the last pair. Otherwise, cursor searches for a
  "         pair on the current line.
  "         The quote pairs try to be smarter than vim's.
  " "in pair": i<pair>
  "            select everything inside the pair:
  " "Inside pair": I<pair>
  "                like "in pair" but excludes whitespace
  " "a pair": a<pair>
  "           Select everything including the pair. Noteably, the quote pairs
  "           don't include surrounding whitespace by default any more.
  " "Around pair": A<pair>
  "                like "a pair" but also selects either trailing/leading
  "                whitespace.
  " "arguments":
  "   ia    select a func argument without the comma
  "   Ia    select a func argument without the comma or whitespace
  "   aa    select a func argument and its comma
  "   Aa    select a func argument and delimiters on both ends?
  Plug 'wellle/targets.vim'

  " skip gutentags when there is no ctags executable installed
  let g:gutentags_ctags_tagfile = '.tags'
  let g:gutentags_ctags_exclude = ['.mypy_cache']
  let g:gutentags_generate_on_empty_buffer = 1
  Plug 'ludovicchabant/vim-gutentags', executable('ctags') && v:version >= 704 ? {} : {'on': []}

  " configure gutenttags to use git ls-files to find files ... I don't know why this isn't the
  " default
  let g:gutentags_file_list_command = {
        \ 'markers': {
        \   '.git': 'git ls-files --cached --others --exclude-standard',
        \   },
        \ }

  " use vim-projectroot to figure out the project root
  let g:gutentags_project_root_finder = 'projectroot#get'

  Plug 'majutsushi/tagbar'
  nnoremap <space>n :TagbarToggle<CR>

  " go to next ALE error. We use :ALENextWrap instead of :ALEFirst because often I can fix a bug and
  " hit '\a' again before ale has re-linted and removed the current error.
  nnoremap \a :ALENextWrap<CR>

  if 1
    PlugMaster 'phodge/vim-javascript-syntax'

    aug TypeScriptTSX
    aug end
    autocmd! TypeScriptTSX BufNewFile,BufRead *.{ts,tsx} set filetype=javascript

    " typescript support
    Plug 'leafgarland/typescript-vim', {'on': []}

    " tsx syntax as well
    Plug 'peitalin/vim-jsx-typescript', {'on': []}

    " Vue support
    Plug 'posva/vim-vue'
  else
    Plug 'pangloss/vim-javascript'
    Plug 'othree/javascript-libraries-syntax.vim'

    let g:used_javascript_libs = 'jquery,angularjs'

    " typescript support
    Plug 'leafgarland/typescript-vim'
  endif

  PlugMaster 'phodge/vim-python-syntax'
  PlugMaster 'phodge/vim-jsx'
  PlugMaster 'phodge/MicroRefactor'
  PlugMaster 'phodge/vim-shell-command'
  PlugMaster 'phodge/vim-syn-info'
  PlugMaster 'phodge/vim-split-search'
  PlugMaster 'phodge/vim-auto-spell'
  PlugMaster 'phodge/vim-vimui'
  PlugMaster 'phodge/vim-myschema'
  PlugMaster 'phodge/vim-vcs'

  Plug 'lumiliet/vim-twig'

  "Plug 'python-rope/ropevim'
  "Plug 'ternjs/tern_for_vim'
  Plug 'tpope/vim-fugitive'
  Plug 'tpope/vim-obsession'
  Plug 'tpope/vim-repeat'
  Plug 'AndrewRadev/linediff.vim'

  " Google Terraform syntax
  " TODO: make this conditional
  if get(g:, 'want_terraform_plugins', 0)
    Plug 'hashivim/vim-terraform'
  endif

  " CSV plugin
  " :WhatColumn
  "   what column number is the cursor in, or the heading if "!" is included
  " :SearchInColumn <nr> /pat/
  "   Search for a value in a particular column
  " :HiColumn[!] [<nr>]
  "   Highlight column <nr> or the current column. "!" removes highlighting
  " :DeleteColumn [<nr>]
  "   Remove column <nr> or the current column.
  " :Header <count>
  "   Add a split window that shows the first <count> lines of the file.
  " :ArrangeColumn
  "   Rewrite the entire file to be vertically aligned
  " :NewDelimiter <char>
  "   Set the delimiter to <char>
  " HLKJ
  "   Move left/right between cells or up/down staying within the same column
  " See also https://github.com/chrisbra/csv.vim#commands
  Plug 'chrisbra/csv.vim'

  " Minimap!
  " TODO: make a faster version of this?
  "Plug 'severin-lemaignan/vim-minimap'

  " we don't necessarily want automatic stripping, but the highlighting will
  " be helpful
  Plug 'tweekmonster/wstrip.vim'
  " :HelpfulVersion PATTERN for version info about features matching PATTERN
  Plug 'tweekmonster/helpful.vim'

  " show vertical lines to indicate indent level
  Plug 'Yggdroot/indentLine'
  " stop making JSON quotes disappear
  let g:indentLine_fileTypeExclude = ['help', 'json', 'markdown']

  " TODO: also try 'nathanaelkane/vim-indent-guides'

  " cool rust stuff
  Plug 'rust-lang/rust.vim'
  " let rust automatically reformat my code on save
  let g:rustfmt_autosave = 1
  " we also need this for the Cargo.toml files
  Plug 'cespare/vim-toml'

  let g:dispatch_quickfix_height = 10
  Plug 'tpope/vim-dispatch'

  " FIXME: I should make my own github repos from these
  Plug 'vim-scripts/StringComplete'
  Plug 'vim-scripts/InsertChar'
  Plug 'vim-scripts/AfterColors.vim'

  " php - insert/sort Use statements automatically {{{

    Plug 'arnaud-lb/vim-php-namespace'

    aug PHPStuff
    au!
    au FileType php nnoremap <buffer> <space>i :call PhpInsertUse()<CR>
    au FileType php nnoremap <buffer> <space>e :call PhpExpandClass()<CR>
    au FileType php com! -buffer SortUseStatements call PhpSortUse()<CR>
    aug end

  " }}}

  " custom PHP syntax - causes problems when g:php_show_semicolon_error is
  " turned on though
  if ! g:peter_use_builtin_php_syntax
    PlugMaster 'phodge/php-syntax.vim'
    let g:php_show_semicolon_error = 0
    let g:php_alt_construct_parents = 1
    let g:php_alt_arrays = 2
    let g:php_highlight_quotes = 1
    let g:php_alt_properties = 1
    let g:php_smart_members = 1
  endif

  " helps with working on neovim itself
  Plug 'neovim/nvimdev.nvim'
  " I don't need the auto-ctags feature because gutentags does this for me
  let g:nvimdev_auto_ctags = 0

  " to all the time
  Plug 'vim-scripts/Align', {'frozen': 0}

  if g:tmux_session == 'NEOSITTER'
    PlugMaster 'phodge/neovim-tree-sitter'
  endif

  " fast/live grep {{{

    Plug 'dyng/ctrlsf.vim'

    " Press ENTER to open a fiel in results window, CTRL+C to cancel

    com! -nargs=+ S CtrlSF <args>

  " }}}

  PlugMaster 'phodge/vim-projectroot'

  " tell vim-projectroot that when a file is part of a git repo that is a
  " submodule of another git repo, the parent git repo should be considerd the
  " project root
  let g:projectroot_nested_git_submodule = 1

  " NOTE: This isn't wasn't as useful as I'd hoped - it only looks at file
  " extensions so is less useful for things like the MySU ORM/YAML files where
  " more powerful manipulation is required
  " Plug 'https://github.com/vim-scripts/a.vim'

  " TODO: have a crack at some of these plugins
  " Plug 'chrisbra/NrrwRgn'
  " https://github.com/prettier/prettier
  " https://github.com/tpope/vim-projectionist
  " https://github.com/danro/rename.vim
  " https://github.com/shougo/deoplete.nvim
  " https://github.com/myusuf3/numbers.vim
  " https://github.com/xolox/vim-session
  " https://github.com/vim-scripts/grep.vim
  " https://github.com/michaeljsmith/vim-indent-object
  " https://github.com/andrewradev/splitjoin.vim
  " https://github.com/vim-airline/vim-airline
  " https://vimawesome.com/plugin/ack-vim
  " https://vimawesome.com/plugin/commentary-vim
  " https://vimawesome.com/plugin/jedi-vim
  " https://vimawesome.com/plugin/vim-easy-align
  " https://github.com/numirias/semshi
  " https://github.com/erikfercak/php-search-doc
  " https://github.com/beanworks/vim-phpfmt
  " https://github.com/wellle/tmux-complete.vim
  " https://github.com/norcalli/nvim-colorizer.lua
  " https://github.com/galooshi/vim-import-js
  " https://github.com/ruanyl/vim-sort-imports
  " https://github.com/skywind3000/vim-quickui
  call plug#end() " }}}
endif


" vim/tmux navigator keybindings {{{

  let g:tmux_navigator_no_mappings = 1
  if g:vim_peter
    if has('nvim')
      tnoremap <silent> <M-h> <C-\><C-n>:TmuxNavigateLeft<cr>
      tnoremap <silent> <M-j> <C-\><C-n>:TmuxNavigateDown<cr>
      tnoremap <silent> <M-k> <C-\><C-n>:TmuxNavigateUp<cr>
      tnoremap <silent> <M-l> <C-\><C-n>:TmuxNavigateRight<cr>
      nnoremap <silent> <M-h> :TmuxNavigateLeft<cr>
      nnoremap <silent> <M-j> :TmuxNavigateDown<cr>
      nnoremap <silent> <M-k> :TmuxNavigateUp<cr>
      nnoremap <silent> <M-l> :TmuxNavigateRight<cr>
      "nnoremap <silent> <M-w> :TmuxNavigatePrevious<cr>
    else
      nnoremap <silent> <ESC>h :TmuxNavigateLeft<cr>
      nnoremap <silent> <ESC>j :TmuxNavigateDown<cr>
      nnoremap <silent> <ESC>k :TmuxNavigateUp<cr>
      nnoremap <silent> <ESC>l :TmuxNavigateRight<cr>
      " these don't seem to work :-(
      "nnoremap <silent> <ESC>w :TmuxNavigatePrevious<cr>
    endif
  else
    if has('nvim')
      tunmap <M-h>
      tunmap <M-h>
      tunmap <M-h>
      tunmap <M-h>
      tunmap <M-h>
    endif
    silent! nunmap <ESC>h
    silent! nunmap <ESC>j
    silent! nunmap <ESC>k
    silent! nunmap <ESC>l
    silent! nunmap <ESC>w
    silent! nunmap <M-h>
    silent! nunmap <M-j>
    silent! nunmap <M-k>
    silent! nunmap <M-l>
    silent! nunmap <M-w>
  endif

" }}}

" the most important change to my vimrc in a long long time
if has('mouse')
  set mouse=a
  " the netrw mouse mappings are annoying and not something I want
  let g:netrw_mousemaps = 0

  " mouse support in massive windows
  if has('mouse_sgr')
      set ttymouse=sgr
  endif
endif

colors elflord
set autoindent
set completeopt=menu,menuone,preview

set modeline modelines=2000
set sessionoptions+=globals,localoptions
" pretend that windows / OS X care about file name case
if exists('&fileignorecase')
  set nofileignorecase
endif

set hlsearch incsearch

" added from the VimTools wiki page
if ! exists('s:vim_entered')
  set encoding=utf-8
endif

set fileencoding=utf-8

" ESC key times out much quicker to prevent accidentally sending escape
" sequences manually
set ttimeoutlen=40

set timeoutlen=500 " give me time to enter multi-key mappings

" don't jump to the start of the line when moving around or re-indenting
set nostartofline

set fileformats=unix,dos,mac


" use \\ as mapleader
let g:mapleader = '\\'

" use <F5> and <F6> to run ack searches
if executable('rg')
  " NOTE: I'm not defaulting to rg yet because it doesn't include line numbers
  " in the output
  nnoremap <F5> :Shell rg -wn <C-R><C-W><CR>
  nnoremap <F6> :Shell rg -wni <C-R><C-W><CR>
else
  nnoremap <F5> :Shell ag -ws <C-R><C-W><CR>
  nnoremap <F6> :Shell ag -wsi <C-R><C-W><CR>
endif

" use F12 for reloading :Shell windows
let g:shell_command_reload_map = '<F12>'

" use F12 in any other buffer to reload ALL shell windows
nnoremap <F12> :ShellRerun<CR>


filetype plugin indent on
syntax on

" fix markdown filetype
augroup CustomFiletype
autocmd! BufNewFile,BufReadPost *.md set filetype=markdown
augroup end

if version >= 703
  if has('nvim')
    set undodir=~/.nvim/.undo
  else
    set undodir=~/.vim/.undo
  endif
  set undofile
endif


if g:vim_peter && version >= 700
  if ! exists('g:_matches')
    let g:_matches = []
  endif

  nnoremap gM :call <SID>AddMatch()<CR>
  function! <SID>AddMatch() " {{{
    call add(g:_matches, expand('<cword>'))
    execute 'match Error' '/' . join(g:_matches, '\|') . '/'
  endfunction " }}}
  nnoremap [33~ :let g:_matches = [] <BAR> match<CR>
  nnoremap <S-F9> :let g:_matches = [] <BAR> match<CR>
endif


nnoremap gm :let @/ = expand('<cword>')<CR>:set hls<CR>

function! ExcaliburQuitWindow() " {{{
  " what is the current buffer number?
  let l:current_bufnr = bufnr("")

  " is this the last buffer?
  let l:is_last = bufnr("$") == l:current_bufnr

  " use bwipeout to get rid of the current buffer
  bwipeout

  " if we are still on the same buffer, it means there was nothing else to
  " load (only other buffers are help buffers)
  if bufnr("") == l:current_bufnr
    " in this case, we just want to quit vim altogether
    echohl WarningMsg
    echo 'Exiting ...'
    echohl None
    quit
  endif

  " if a new buffer was created for us, it means we should have quit
  if l:is_last && bufnr("") > l:current_bufnr
    echohl WarningMsg
    echo 'Exiting ...'
    echohl None
    quit
  endif
endfunction " }}}

nnoremap <F8> :syn sync fromstart<CR>:exe 'setlocal foldmethod=' . &l:foldmethod<CR>
nnoremap <F9> :nohls<CR>

if exists('&inccommand')
  set inccommand=split
endif

if version >= 700
  " StringComplete plugin
  inoremap <C-J> <C-O>:set completefunc=StringComplete#GetList<CR><C-X><C-U>
endif

nnoremap <space>m :<C-R>=(exists(':Make')==2?'Make':'make')<CR><CR>

if version >= 700 && g:vim_peter
  nnoremap gss :call MySchema#GetSchema(expand('<cword>'))<CR>
endif

" use <ENTER> to activate CleverEdit in visual mode
if g:vim_peter
  if version >= 700
    vnoremap <CR> y:call CleverEdit#go()<CR>
  endif
  vnoremap <SPACE>v y:call MicroRefactor#LocalVariable()<CR>
else
  silent! vunmap <CR>
endif

" InsertChar plugin {{{

  if g:vim_peter
    if version >= 700
      nnoremap <TAB> :<C-U>call InsertChar#insert(v:count1)<CR>
    else
      nnoremap <TAB> iX<ESC>r
    endif
    " g<TAB> can be used to get the normal behaviour of <TAB>
    nnoremap g<TAB> <TAB>
  elseif strlen(maparg("\<TAB>", 'n'))
    silent! nunmap <TAB>
    silent! nunmap g<TAB>
  endif

" }}}

aug StatusLineHelpers
aug end
au! StatusLineHelpers User ALELint call <SID>UpdateAleStatus()
fun! <SID>UpdateAleStatus()
  let l:counts = ale#statusline#Count(bufnr(''))

  let l:all_errors = l:counts.error + l:counts.style_error
  let l:all_warnings = l:counts.total - l:all_errors

  let b:__ale_error_flag = l:all_errors ? ('E'.l:all_errors) : ''
  let b:__ale_warning_flag = l:all_warnings ? ('W'.l:all_warnings) : ''
endfun

" nicer statusline
if g:vim_peter && version >= 700
  set statusline=
  set statusline+=%n\ \ %f
  set statusline+=\ %{(&l:ff=='dos')?':dos:\ ':''}%m%<%r%h%w

  " ALE status
  if exists('*get')
    set statusline+=%#Error#
    set statusline+=%{get(b:,'__ale_error_flag','')}
    set statusline+=%#Search#
    set statusline+=%{get(b:,'__ale_warning_flag','')}
  endif

  set statusline+=%*
  set statusline+=%=
  " gutentags
  set statusline+=%{exists('*gutentags#statusline')?gutentags#statusline('[T]\ '):''}
  " ruler
  set statusline+=Line\ %l\ \ \ %v/%{col('$')-1}\ \ \ 
  " character under cursor
  set statusline+=0x%B
  set statusline+=\ %p%%
endif

" favourite options
set autoindent
set ruler
set showcmd
set laststatus=2
set wildmenu
set wildmode=longest,list,full
set backspace=indent,eol,start
set hlsearch
nohlsearch
set incsearch
set history=10000
set splitbelow splitright noequalalways winwidth=126 winminwidth=15
set number
set shiftround
set nolist
"set listchars=tab:\|_,trail:@,precedes:<,extends:>
set listchars=tab:\|_,trail:@
set showbreak=...

" don't add an EOL if one wasn't present
if exists("&fixeol")
  set nofixeol
endif

set scrolloff=2
set sidescroll=20
set sidescrolloff=20


" ninja mappings {{{

    " fix for :! not being interactive in neovim
    if has('nvim')
      "set shell=tmux\ split-window\ -h
      "cnoremap <expr> ! strlen(getcmdline())?'!':('!tmux split-window -c '.getcwd().' ')
    endif

    " n for next search always searches downwards.
    if g:vim_peter
      if exists('v:searchforward')
        " n and N _always_ search forward/backward respectively
        nnoremap <silent> <expr> n (v:searchforward ? 'n' : 'N') . 'zv'
        nnoremap <silent> <expr> N (v:searchforward ? 'N' : 'n') . 'zv'
      else
        nnoremap n /<C-R>/<CR>
        nnoremap N ?<C-R>/<CR>
      endif
    else
      silent! nunmap n
      silent! nunmap N
    endif


    " backspace hides the popup menu
    if exists('*pumvisible')
      inoremap <expr> <BS> pumvisible() ? " \<BS>\<BS>" : "\<BS>"
    endif

    " use the slightly better gF instead of gf
    nnoremap gf gF

    " when using i{ in line-wise Visual mode, don't revert to character-wise
    " mode
    vnoremap i{ i{V
    vnoremap i} i}V
    vnoremap a{ a}V
    vnoremap a} a}V

    " make CTRL+E and CTRL+Y scroll twice as fast
    nnoremap <C-E> 2<C-E>
    nnoremap <C-Y> 2<C-Y>

    " yank and paste keeps cursor in the same column
    nnoremap <silent> yyp mtyyp`tj

    if g:vim_peter
      nnoremap <silent> $ g$
      nnoremap <silent> ^ g^
      nnoremap <silent> 0 g0
      nnoremap <silent> g$ $
      nnoremap <silent> g^ ^
      nnoremap <silent> g0 0
      nnoremap <silent> j gj
      nnoremap <silent> k gk
      nnoremap <silent> gj j
      nnoremap <silent> gk k
    else
      silent! nunmap $
      silent! nunmap ^
      silent! nunmap g$
      silent! nunmap g^
      silent! nunmap j
      silent! nunmap k
      silent! nunmap gj
      silent! nunmap gk
    endif

    if g:vim_peter
      nnoremap zl 20zl
      nnoremap zh 20zh
    else
      silent! nunmap zl
      silent! nunmap zh
    endif

    if version >= 700
      " use \u to toggle between normal and regular undo
      nnoremap <silent> \u :call <SID>ToggleUndo()<CR>
      function! <SID>ToggleUndo() " {{{
        if exists('s:undo_advanced')
          " turn super undo OFF
          unlet s:undo_advanced
          nunmap u
          nunmap <C-R>
          let l:type = 'Basic'
        else
          " turn super undo ON
          " change u and C-R to use full undo history instead
          nnoremap u g-
          nnoremap <C-R> g+
          let l:type = 'Full History'
          let s:undo_advanced = 1
        endif
        echohl Question
        echo 'Undo:' l:type
        echohl None
      endfunction " }}}
    endif

    if g:vim_peter
      " dp and do automatically jump to the next change
      nnoremap <silent> dp dp]c
      nnoremap <silent> do do]c
    else
      silent! nunmap dp
      silent! nunmap do
    endif

    " r(, r[, and r{ will replace BOTH brackets
    if g:vim_peter
      nnoremap r( :call <SID>ReplaceBrackets('()')<CR>
      nnoremap r[ :call <SID>ReplaceBrackets('[]')<CR>
      nnoremap r{ :call <SID>ReplaceBrackets('{}')<CR>
    elseif strlen(maparg("r(", 'n'))
      nunmap r(
      nunmap r[
      nunmap r{
    endif

    function! <SID>ReplaceBrackets(newbrackets) " {{{
      " if the letter under the cursor is an opening bracket, replace both at once
      let l:line = line('.')
      let l:col = col('.')
      let l:replace = strpart(getline(l:line), l:col - 1, 1)
      if l:replace =~ '[([{]'
        " can we find the matching bracket?
        normal! %

        " if the line number or column number has changed, then we found it!
        if (line('.') != l:line) || (col('.') != l:col) && (line('.') <= (l:line + 10))
          " replace this character and then go back
          execute 'normal! r' . a:newbrackets[1]
          call cursor(l:line, l:col)
        endif
      endif

      " do the original replace as requested
      execute 'normal! r' . a:newbrackets[0]
    endfunction " }}}


" }}}


" dirty hacks to make F-keys and keypad work when term type is wrong {{{

  if g:hackymappings " {{{
    map 0k +
    map 0m -
    map g0k g+
    map g0m g-

    " TODO: add F-keys
  endif

" }}}


" mappings {{{

  " toggle options quickly
  nnoremap \c :exe 'setlocal colorcolumn='.((&l:colorcolumn=='') ? '+2' : '').' colorcolumn?'<CR>
  nnoremap \d :exe 'setlocal diffopt' . ((&g:diffopt =~ 'iwhite') ? '-' : '+') . '=iwhite diffopt?'<CR>
  nnoremap \e :Sexplore<CR>:diffoff<CR>
  nnoremap \l :set list! list?<CR>
  nnoremap \n :set number! number?<CR>
  nnoremap \p :set paste! paste?<CR>
  nnoremap \w :set wrap! wrap?<CR>
  nnoremap \q :call ExcaliburQuitWindow()<CR>
  " essentially :tabclose but also works when there is only one tab
  nnoremap \t :windo quit<CR>

  " this is about the only mapping that's safe for others
  nnoremap gt :execute 'tj' expand('<cword>')<CR>zv
  nnoremap gst :execute 'stj' expand('<cword>')<CR>zv

  " fugitive
  nnoremap \g :tab sp<CR>:exe (exists(':Gstatus') =~ '[12]' ? 'Gstatus' : 'Shell hg st')<CR><C-W>w:close<CR>:tabmove<CR>
 "nnoremap \g :tab sp<CR>:exe (exists(':Gstatus') =~ '[12]' ? 'Gstatus' : 'Shell hg st')<CR>1<C-W>w:close<CR>1<C-W>w:tabmove<CR>

  if g:vim_peter
    nnoremap <silent> go :call <SID>NewlineNoFO('o')<CR>xa
    nnoremap <silent> gO :call <SID>NewlineNoFO('O')<CR>xa
    function! <SID>NewlineNoFO(command) " {{{
      let l:foldopt = &l:formatoptions
      try
        setlocal formatoptions-=o
        execute 'normal! ' . a:command . 'x'
      finally
        " restore format options
        let &l:formatoptions = l:foldopt
      endtry
    endfunction " }}}

    nnoremap gh :tabprev<CR>
    nnoremap gl :tabnext<CR>

    nnoremap gsf :call <SID>GSF()<CR>zv
    function! <SID>GSF() " {{{
        try
            sp
            normal! gF
        catch
            close
            redraw!
            echohl Error
            echo v:exception
            echohl None
        endtry
    endfunction " }}}

    nnoremap + 4<C-W>+
    nnoremap - 4<C-W>-
    nnoremap g+ <C-W>_

    inoremap <C-L> <C-X><C-F>

    " <F8> should backspace word chunks
    inoremap <F8> _<SPACE><ESC>:call <SID>SuperBackspace()<CR>s
    function! <SID>SuperBackspace() " {{{
      normal! d?\%(_\+\zs\|\l\zs\u\|\<\zs\w\|\w\zs\>\)
    endfunction " }}}

    " map F2 to align code to '=', F3 is '=>' and F4 is ':'
    vnoremap <F1> mt:Align! p0 ,<CR>gv:s/\(\s\+\),/,\1/g<CR>gv:s/,\s\+$/,/g<CR>`t
    vnoremap <F2> mt:Align! p0P0 \s=\s<CR>`t
    vnoremap <F3> mt:Align =><CR>`t
    vnoremap <F4> mt:Align! p0 :<CR>gv:s/\(\s\+\):/:\1/g<CR>`t

    " use c" to swap quote types {{{

      nnoremap <silent> c" :call <SID>SwapQuotes()<CR>

      function! <SID>SwapQuotes() " {{{
          " we'll use the default register, but we want to save its contents first ...
          let l:tempZ = @z

          let l:pos = getpos('.')

          try
              " NOTE: we do a few :normal commands in here and it's probably safer if we
              " turn off the autocommands while we're doing this ...
              let l:old_ei = &eventignore
              set eventignore=all

              let l:old_paste = &paste

              " we need to work out what kind of quote we're in?
              if ! search('[^\\]\zs[''"]', 'bcW', line('.'))
                  echoerr "Quotes not found!"
                  return
              endif

              " grab the character under the cusor (should be ' or ")
              normal! "zyl
              if (@z == '"') || (@z == "'")
                  let l:quote = @z
              else
                  echoerr "No quote???"
                  return
              endif

              " now we delete the inside of the quoted region ...
              execute 'normal! "zdi' . l:quote
              " ... and store it somewhere
              let l:newQuote = (l:quote == '"') ? "'" : '"'
              let l:insert = l:newQuote . @z . l:newQuote

              " now we must delete the quotes (again, using @z register) and insert
              " everything back in.
              " NOTE: we use the 'paste' option to prevent formatting changes
              set paste
              execute 'normal! h"z2s' . l:insert

          " cleanup here
          finally
              " 1: restore our 'z' register
              if exists('l:tempZ') | let @z = l:tempZ | endif
              " 2: put the cursor back
              if exists('l:pos') | call setpos('.', l:pos) | endif
              " 3: restore 'paste' option
              if exists('l:old_paste') | let &paste = l:old_paste | endif
              " 4: restore autocommands
              if exists('l:old_ei') | let &eventignore = l:old_ei | endif
          endtry
      endfunction " }}}


    " }}}

    " use g/ in visual mode to search only in that line range
    vnoremap <expr> g/ "\<ESC>" . <SID>GetVisualSearch()

    function! <SID>GetVisualSearch() " {{{
      return printf('/\%%>%dl\&\%%<%dl\&', line("'<") - 1, line("'>") + 1)
    endfunction " }}}

  elseif strlen(maparg('go', 'n'))
    nunmap go
    nunmap gO
    nunmap gh
    nunmap gl
    nunmap gsf
    nunmap +
    nunmap -
    nunmap g+
    nunmap <UP>
    nunmap <DOWN>
    nunmap <LEFT>
    nunmap <RIGHT>
    nunmap c"
    vunmap g/
  endif

  nnoremap gF :call <SID>GFNotSetup('gF')<CR>
  nnoremap gsF :call <SID>SplitGF()<CR>
  function! <SID>GFNotSetup(cmd) " {{{
    echohl Error
    echo a:cmd . ' is not defined for filetype=' . &l:filetype
    echohl None
  endfunction " }}}
  function! <SID>SplitGF() " {{{
    let l:split = 0
    split
    let l:split = 1
    setlocal noscrollbind
    try
      normal gF
    catch
      " close the new window if the command didn't work
      if l:split
        close
      endif
      redraw!
      echohl Error
      echo 'gsF: ' . v:exception
      echohl None
    endtry
  endfunction " }}}

" }}}



" commands for navigating file history (git-only I believe)
command! -nargs=0 GitOlder call VCS#GitNavigateHistory(1)
command! -nargs=0 GitNewer call VCS#GitNavigateHistory(0)

" command for starting an SQL window
command! -nargs=0 SQLWindow call MySchema#SQLWindow()

" don't like this plugin
let g:loaded_matchparen = 1

augroup ExcaliburVCS
autocmd! BufReadPost,BufNewFile * let b:excalibur_vcs = VCS#DetermineVCS()
augroup end

if g:vim_peter
  nnoremap gD :call <SID>ShowDiff()<CR>
  function! <SID>ShowDiff()
    if exists('b:excalibur_vcs') && b:excalibur_vcs == 'hg'
      call VCS#SplitHGDiff()
    else
      call VCS#GitDiff('HEAD')
    endif
  endfunction
else
  nunmap gD
endif

if has('osx')
  " if we're running under OS X, yank into the main clipboard by default
  " NOTE: this is different in vim vs neovim
  set clipboard=unnamed
endif


command! -nargs=+ Man ConqueTermVSplit man <q-args>


function! EditRealPath()
  let l:filename = expand('%:p')
  let l:realpath = resolve(l:filename)

  " if we are editing the real file, don't try and open it up
  if l:realpath == l:filename
    return
  endif

  " if the realpath file doesn't exist, don't try and edit it
  if ! filereadable(l:realpath)
    return
  endif

  " remember local options/settings?
  let l:oldbufnr = bufnr("")
  " edit a new empty file (this will copy options/cwd etc from the buffer)
  enew
  " wipe out the old buffer
  execute 'bwipeout' l:oldbufnr
  " re-edit the old file again but with the real path
  " NOTE: because we use :edit with the new empty buffer opened, we get all
  " our local options back
  execute 'edit' l:realpath
endfunction

augroup EditRealPath
augroup end
autocmd! EditRealPath BufReadPost * nested if exists('g:edit_real_path') && g:edit_real_path | call EditRealPath() | endif

" open python wheels like zip files
au BufReadCmd *.whl call zip#Browse(expand("<amatch>"))

augroup PowerlineCFG
augroup end
autocmd! PowerlineCFG BufRead powerline/**/*.json setlocal sts=2 sw=2 ts=2 et


" TODO: move this into a plugin once I have a good system for doing so
augroup Jerjerrod
augroup end
au! Jerjerrod BufWritePost * call <SID>JerjerrodInit()

fun! <SID>JerjerrodInit()
  " replace or remove the autocommand
  au! Jerjerrod
  if executable('jerjerrod')
    au! Jerjerrod BufWritePost * call <SID>JerjerrodClearCache()
    call <SID>JerjerrodClearCache()
  endif
endfunction

fun! <SID>JerjerrodClearCache()
  if has('*jobstart')
    call jobstart(['jerjerrod', 'clearcache', '--local', expand('%')])
  else
    silent exe '!jerjerrod clearcache --local '.shellescape(expand('%'))
    redraw!
  endif
endfunction


let s:skeletons_dir = expand('<sfile>:h:p').'/vim/skeletons'
aug Skeletons
au!
au BufNewFile *.tsx call <SID>NamedSkeleton('component.tsx', expand('<afile>'))
au BufNewFile retest.sh call <SID>NamedSkeleton('retest.sh', expand('<afile>'))
aug end

if ! exists('s:next_group_number')
  let s:next_group_number = 1
endif

function! <SID>NamedSkeleton(template_name, buffer_name)
  " paste in the template file
  let l:template_path = printf('%s/%s', s:skeletons_dir, a:template_name)
  exe 'read' l:template_path
  normal! ggdd
  setlocal modified

  " set up a self-destructing autocmd that will put the correct permissions on the file on write
  let l:perms = getfperm(l:template_path)
  if l:perms != ''
    let l:group_number = s:next_group_number
    let s:next_group_number += 1

    let l:au_group = 'SkeletonPerms_' . l:group_number
    exe 'augroup' l:au_group
    exe printf('au BufWritePost <buffer> call setfperm(bufname(""), "%s") | au! %s | aug! %s',
          \ l:perms, l:au_group, l:au_group)
    augroup END
  endif
endfun


" XXX: languageClient-neovim turns on this option, but shortmess=F stops DidYouMean from working
set shortmess-=F


let s:vim_entered = 1
