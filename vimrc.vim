if filereadable(expand('~/.vim/settings.vim'))
  source ~/.vim/settings.vim
endif

if ! exists('g:vim_peter')
  let g:vim_peter = 1
endif

if ! exists('g:want_fast')
  let g:want_fast = 0
endif

if ! exists('g:hackymappings')
  let g:hackymappings = 0
endif

let s:ts_lsp = has('nvim') && strlen($NVIM_TS_LSP)
let s:require_plenary = 0

" sensible defaults to start with
if &compatible
  setglobal nocompatible
endif

let s:dotfiles_root = expand('<sfile>:p:h')

set confirm

" when to use LSP and YCM
" TODO: probably get rid of these in favour of s:ts_lsp above
let s:use_lsp = has('nvim') && get(g:, 'peter_use_lsp', 0)

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


fun! <SID>VendoredPlug(path)
  let l:parts = split(a:path, '/')
  let l:name = l:parts[1]
  let l:newpath = s:dotfiles_root . '/vim-packages/' . l:name . '.git'

  if g:allow_rtp_modify
    let &runtimepath = l:newpath . ',' . &runtimepath . ',' . l:newpath . '/after'
  endif
endfun


" per-project config
call <SID>VendoredPlug('phodge/vim-project-config')
let s:config_dirs = get(g:, 'mydots_additional_project_config_paths', {})
let s:config_dirs.Personal = s:dotfiles_root . '/vimproject'
call vimprojectconfig#initialise({
      \ 'project_config_dirs': s:config_dirs,
      \ })
unlet s:config_dirs

if has('nvim') && g:want_copilot
  call <SID>VendoredPlug('github/copilot.vim')

  " the default mapping for Copilot is <tab>, to change it see
  " :help copilot-maps

  aug PeterCopilot
  au! BufReadPost,BufNewFile *.txt,*.md,*.csv let b:copilot_enabled = 0
  aug end
endif


if has('nvim') && g:want_neovim_treesitter " {{{ tree-sitter

  call <SID>VendoredPlug('nvim-treesitter/nvim-treesitter')
  call <SID>VendoredPlug('nvim-treesitter/nvim-treesitter-playground')

  let g:peter_ts_disable = []
  if ! g:want_neovim_treesitter_python
    call add(g:peter_ts_disable, 'python')
  endif

  lua <<EOF
    require'nvim-treesitter.configs'.setup {
      highlight = {
        enable = true,
        custom_captures = {
        },
        disable = vim.g.peter_ts_disable,
        additional_vim_regex_highlighting = false,
      },
      playground = {
        enable = true,
        updatetime = 25,
        persist_queries = false,
        keybindings = {
        },
      },
      ensure_installed={
        "typescript",
        "tsx",
        "javascript",
        "python",
        "vim",
        "vimdoc",
        "lua",
      },
    }
EOF

  " NOTE: so if you want treesitter to work you also need to run ...
  " :TSInstall typescript
  " :TSInstall tsx
  " :TSInstall javascript
  " :TSInstall python
  " use e.g. "TSInstall typescript" to install a specific parser

  " also set up ts-node-action while we're here
  call <SID>VendoredPlug('CKolkey/ts-node-action')

  lua vim.keymap.set({"n"}, "\\x", require("ts-node-action").node_action, { desc = "Trigger Node Action" })

  lua <<EOF
    local actions = require 'ts-node-action.actions'
    require'ts-node-action'.setup {
    }
EOF
endif " }}}


" set up Vundle if it's present and not in &rtp yet
let s:plugpath = $HOME.'/.vim/autoload/plug.vim'
if filereadable(s:plugpath)
  " use different path depending on vim/nvim
  let s:plugins = has('nvim') ? '~/.nvim/plugged' : '~/.vim/plugged'

  call plugmaster#begin('~/src/plugedit', '~/src', s:plugins) " {{{

  if g:tmux_session == 'SPACETEA-DEV'
    call <SID>VendoredPlug('phodge/spacetea.vim')
  endif

  " firenvim
  if get(g:, 'peter_want_firenvim', 0)
    " see https://github.com/glacambre/firenvim for instructions on how to
    " configure
    call <SID>VendoredPlug('glacambre/firenvim')
  endif

  if s:ts_lsp
    call <SID>VendoredPlug('neovim/nvim-lspconfig')
    call <SID>VendoredPlug('jose-elias-alvarez/null-ls.nvim')

    " provides :TSLspImportCurrent, TSLspRenameFile, TSLspOrganize
    call <SID>VendoredPlug('jose-elias-alvarez/nvim-lsp-ts-utils')

    " plenary.nvim is required for the nvim-lsp-ts-utils plugin
    let s:require_plenary = 1
  endif

  if ! has('nvim-0.9.0')
    " this is built into neovim from v0.9 onwards
    call <SID>VendoredPlug('editorconfig/editorconfig-vim')
    let g:EditorConfig_exclude_patterns = ['fugitive://.*']
  endif

  " the awesome Jedi library for python
  " XXX: we manage this with vim-plug because vim-plug takes care of
  " initialising jedi's own submodules
  Plug 'davidhalter/jedi-vim'
  let g:jedi#use_splits_not_buffers = "winwidth"
  " NOTE: I'm disabling call signatures because A) it doesn't seem to work and
  " B() vim isfreezing and I don't know why
  let g:jedi#show_call_signatures = 0
  let g:jedi#smart_auto_mappings = 0
  let g:jedi#popup_on_dot = 0

  " ALE setup {{{

    call <SID>VendoredPlug('w0rp/ale')

    if get(g:, 'use_ale_dmypy')
      " tell ale to use dmypy instead of mypy
      " WARNING: see notes in mydots-configure
      let g:ale_python_mypy_use_global = 1
      let g:ale_python_mypy_executable = 'dmypy'
      let g:ale_python_mypy_options = 'run -- '
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
  endif

  " ArgWrap {{{

    " TODO: would be good if we could outsource this to the LS
    call <SID>VendoredPlug('FooSoft/vim-argwrap')
    let g:argwrap_tail_comma = 1
    nnoremap <space>a :ArgWrap<CR>

  " }}}

  if has('macunix') " Kapeli Dash docs viewer for Mac {{{
    Plug 'rizzatti/dash.vim'
    nnoremap <S-F5> :Dash <cword><CR>
  endif " }}}

  " nginx syntax
  call <SID>VendoredPlug('chr4/nginx.vim')

  if ! g:want_fast
    call <SID>VendoredPlug('EinfachToll/DidYouMean')
    call <SID>VendoredPlug('hynek/vim-python-pep8-indent')

    if ! g:want_neovim_treesitter_python
      call <SID>VendoredPlug('tmhedberg/SimpylFold')
    endif
  endif

  call <SID>VendoredPlug('christoomey/vim-tmux-navigator')

  " python imports {{{

    " adds :ImportName and :ImportNameHere commands
    " XXX: I haven't been using this and it has a big startup cost (250ms?) so
    " am disabling for now
    "Plug 'mgedmin/python-imports.vim'

  " }}}

  " python requirements.txt syntax highlighting
  call <SID>VendoredPlug('raimon49/requirements.txt.vim')

  " python code formatting via Black
  " XXX: I've had to uninstall this because it doesn't set up the virtualenv
  " correctly for nvim
  "Plug 'psf/black'
  aug FakeBlack
  au!
  au! BufRead *.py command! -buffer Black !black %:p
  aug end

  " make inactive windows dim slightly
  let g:vimade = get(g:, 'vimade', {})
  let g:vimade.fadelevel = 0.5
  let g:vimade.basebg = '#000000'
  if get(g:, 'want_vimade', 0)
    call <SID>VendoredPlug('TaDaa/vimade')
  endif

  if has('nvim') && get(g:, 'want_neovim_snippy', 0)
    " NOTE: you can find links to more snippets plugins here:
    " https://github.com/honza/vim-snippets

    call <SID>VendoredPlug('dcampos/nvim-snippy')

    imap <expr> <Tab> snippy#can_expand_or_advance() ? '<Plug>(snippy-expand-or-advance)' : '<Tab>'
    imap <expr> <S-Tab> snippy#can_jump(-1) ? '<Plug>(snippy-previous)' : '<S-Tab>'
    smap <expr> <Tab> snippy#can_jump(1) ? '<Plug>(snippy-next)' : '<Tab>'
    smap <expr> <S-Tab> snippy#can_jump(-1) ? '<Plug>(snippy-previous)' : '<S-Tab>'
    xmap <Tab> <Plug>(snippy-cut-text)
  elseif has('nvim') && v:version >= 704
    Plug 'SirVer/ultisnips', v:version >= 704 ? {} : {'on': []}
    " this is CTRL+J by default, which we don't want
    let g:UltiSnipsJumpForwardTrigger = '<space><C-J>'
  else
    " NOTE: we need to use the older SnipMate on vim because UltiSnips keeps
    " producing errors in vim 8.1
    Plug 'MarcWeber/vim-addon-mw-utils'
    Plug 'tomtom/tlib_vim'
    Plug 'garbas/vim-snipmate'

    " required to get rid of the SnipMate-deprecate warning on startup
    " (See :help SnipMate-deprecate)
    let g:snipMate = { 'snippet_version': 1 }
  endif
  Plug 'sjl/Clam.vim'
  Plug 'tmux-plugins/vim-tmux'
  Plug 'easymotion/vim-easymotion'
  " TODO: revisit this and see if we can get some nice mappings up
  Plug 'brooth/far.vim'

  let s:has_fzf = 0
  if has('nvim') && get(g:, 'use_vendored_fzf', 0)
    " use vendored version of FZF since the brew version (0.44.1) is having
    " issues
    let s:has_fzf = 1
    let &rtp .= ',' . s:dotfiles_root . '/vim-packages/fzf.git'
  elseif has('nvim') && isdirectory('/usr/local/opt/fzf')
    " homebrew will install fzf in /opt/homebrew/bin/fzf
    " (or in older versions of homebrew /usr/local/opt/fzf)
    let s:has_fzf = 1
    " use vim plugin provided by fzf homebrew package
    set rtp+=/usr/local/opt/fzf
  elseif has('nvim') && executable('fzf')
    let s:has_fzf = 1
    let &rtp .= ',' . expand('/opt/homebrew/Cellar/fzf/*')
  else
    Plug 'ctrlpvim/ctrlp.vim'
    let g:ctrlp_user_command = ['.git', 'cd %s && git ls-files -co --exclude-standard']
  endif

  if s:has_fzf
    nnoremap <C-P> :FZF<CR>
    nnoremap \\ :call fzf#vim#grep('git-branch-status --short --quiet', 0)<CR>
    let g:fzf_layout = {'window': {'width': 0.8, 'height': 0.8}}
    let g:fzf_action = {
                \ 'ctrl-t': 'tab split',
                \ 'ctrl-x': 'split',
                \ 'ctrl-v': 'vsplit',
                \ }
    " I just want to be able to hit enter to open a file in a new split
    let g:fzf_action['enter'] = 'split'
  endif

  " Use `:DiffviewFileHistory %` to get a history of the current buffer
  " See `:h diffview` for other git history commands
  Plug 'sindrets/diffview.nvim'

  " git-gutter
  if has('signs') && v:version >= 704
    Plug 'airblade/vim-gitgutter'

    " make it disabled by default, by toggle-able by space-g
    let g:gitgutter_enabled = 0
    nnoremap <space>g :GitGutterToggle<CR>:echomsg 'Use ]c and [c to move between hunks'<CR>

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
  Plug 'wellle/targets.vim', g:want_fast ? {'on': []} : {}

  " skip gutentags when there is no ctags executable installed
  let g:gutentags_ctags_tagfile = '.tags'
  let g:gutentags_ctags_exclude = [
        \ '.mypy_cache',
        \ '*.min.js',
        \ '*-min.js',
        \ '*.map.js',
        \ '*-map.js',
        \ ]
  let g:gutentags_generate_on_empty_buffer = 1
  " disable file types that add noise to the tag file
  let g:gutentags_ctags_extra_args = [
        \ '--languages=-html,svg,markdown,json,sql,css',
        \ ]
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

  Plug 'majutsushi/tagbar', g:want_fast ? {'on': []} : {}
  nnoremap <space>n :TagbarToggle<CR>

  " go to next ALE error. We use :ALENextWrap instead of :ALEFirst because often I can fix a bug and
  " hit '\a' again before ale has re-linted and removed the current error.
  nnoremap \a :ALENextWrap<CR>

  if get(g:, 'clipchamp_js', 0)
    " just use my own javascript syntax
    PlugMaster 'phodge/vim-javascript-syntax'

    " TODO: this doesn't always take precedence - the builtin filetype
    " detection takes precedence for Skylight windows and the buffer ends up
    " with builtin ft=typescript syntax
    aug TypeScriptTSX
    aug end
    autocmd! TypeScriptTSX BufNewFile,BufRead *.{ts,tsx} set filetype=javascript

    "Plug 'https://github.com/HerringtonDarkholme/yats.vim'

    "hi! link typescriptAssign Operator
    "hi! link typescriptTypeAnnotation Function
    "hi! link typescriptUnaryOp Operator
    "hi! link typescriptBinaryOp Number
    "hi! link typescriptDotNotation Operator
  elseif has('nvim') && g:want_neovim_treesitter
    " don't do anything if we are using treesitter syntax
  elseif 1
    PlugMaster 'phodge/vim-javascript-syntax'

    " TODO: this doesn't always take precedence - the builtin filetype
    " detection takes precedence for Skylight windows and the buffer ends up
    " with builtin ft=typescript syntax
    aug TypeScriptTSX
    aug end
    " XXX: this messes with the language server stuff so we need to scrap it
    if s:ts_lsp
      autocmd! TypeScriptTSX BufNewFile,BufRead *.{ts,tsx} set syntax=javascript
    else
      autocmd! TypeScriptTSX BufNewFile,BufRead *.{ts,tsx} set filetype=javascript
    endif

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

  " javascript/typescript imports {{{

    " TODO finish this

    " adds :SortImport command for .js files
    " TODO: should we use https://github.com/Galooshi/import-js project
    " instead?
    "Plug 'ruanyl/vim-sort-imports'

  " }}}

  call <SID>VendoredPlug('phodge/vim-python-syntax')
  PlugMaster 'phodge/MicroRefactor'
  PlugMaster 'phodge/vim-shell-command'
  PlugMaster 'phodge/vim-syn-info'
  PlugMaster 'phodge/vim-split-search'
  PlugMaster 'phodge/vim-auto-spell'
  PlugMaster 'phodge/vim-vimui'
  PlugMaster 'phodge/vim-myschema'
  PlugMaster 'phodge/vim-vcs'

  Plug 'lumiliet/vim-twig'

  Plug 'tpope/vim-fugitive'
  Plug 'tpope/vim-obsession'
  Plug 'tpope/vim-repeat'
  Plug 'AndrewRadev/linediff.vim'

  if s:require_plenary
    call <SID>VendoredPlug('nvim-lua/plenary.nvim')
  endif

  " Debugger
  if g:peter_give_me_a_debugger
    Plug 'sakhnik/nvim-gdb', {'do': '!./install.sh'}
    "Plug 'puremourning/vimspector'
  endif

  " Google Terraform syntax
  if g:peter_want_terraform_plugins
    Plug 'hashivim/vim-terraform'
  endif

  " Skylight
  if has('nvim')
    Plug 'https://github.com/voldikss/vim-skylight'
    "nnoremap <silent>       go    :SkylightJumpTo<CR>
    nnoremap <silent>       gp    :SkylightPreview<CR>
    nmap <silent><expr> <C-n> skylight#float#has_scroll() ? skylight#float#scroll(1) : "\<C-n>"
    exe 'nmap <silent><expr> <C-p> '
          \ 'skylight#float#has_scroll() ? skylight#float#scroll(0) : '
          \ '"' . (s:has_fzf ? ":FZF\<CR>" : ":CtrlP\<CR>") . '"'
  else
    nnoremap gp :echoerr 'Skylight requires neovim'
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

  if has('conceal') && !g:want_fast
    " show vertical lines to indicate indent level
    call <SID>VendoredPlug('Yggdroot/indentLine')

    " stop making JSON quotes disappear
    let g:indentLine_fileTypeExclude = ['help', 'json', 'markdown']
  endif

  " TODO: also try 'nathanaelkane/vim-indent-guides'

  " cool rust stuff
  if g:peter_want_rust_plugins
    Plug 'rust-lang/rust.vim'
    " let rust automatically reformat my code on save
    let g:rustfmt_autosave = 1
  endif

  " we also need this for the Cargo.toml files
  call <SID>VendoredPlug('cespare/vim-toml')

  let g:dispatch_quickfix_height = 10
  Plug 'tpope/vim-dispatch'

  " FIXME: I should make my own github repos from these
  Plug 'vim-scripts/StringComplete'
  Plug 'vim-scripts/InsertChar'
  Plug 'vim-scripts/AfterColors.vim'

  " php - insert/sort Use statements automatically {{{
  if g:peter_want_php_plugins
    Plug 'arnaud-lb/vim-php-namespace'

    aug PHPStuff
    au!
    au FileType php nnoremap <buffer> <space>i :call PhpInsertUse()<CR>
    au FileType php nnoremap <buffer> <space>e :call PhpExpandClass()<CR>
    au FileType php com! -buffer SortUseStatements call PhpSortUse()<CR>
    aug end
  endif

  " }}}

  " custom PHP syntax - causes problems when g:php_show_semicolon_error is
  " turned on though
  if g:peter_want_php_plugins && ! g:peter_use_builtin_php_syntax
    PlugMaster 'phodge/php-syntax.vim'
    let g:php_show_semicolon_error = 0
    let g:php_alt_construct_parents = 1
    let g:php_alt_arrays = 2
    let g:php_highlight_quotes = 1
    let g:php_alt_properties = 1
    let g:php_smart_members = 1
  endif

  " helps with working on neovim itself
  if g:peter_want_nvimdev_plugin
    call <SID>VendoredPlug('neovim/nvimdev.nvim')
  endif

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

  " use <C-X><C-U> to complete things from other tmux panes/windows
  call <SID>VendoredPlug('wellle/tmux-complete.vim')

  " vim-projectroot is used for Gutentags config below
  call <SID>VendoredPlug('phodge/vim-projectroot')

  " tell vim-projectroot that when a file is part of a git repo that is a
  " submodule of another git repo, the parent git repo should be considerd the
  " project root
  let g:projectroot_nested_git_submodule = 1

  " NOTE: This isn't wasn't as useful as I'd hoped - it only looks at file
  " extensions so is less useful for things like the MySU ORM/YAML files where
  " more powerful manipulation is required
  " Plug 'https://github.com/vim-scripts/a.vim'

  " nvim-colorizer: highlights #RRGGBB hex codes for these file types:
  if has('nvim-0.3.0') && !g:want_fast
    Plug 'https://github.com/norcalli/nvim-colorizer.lua.git', {'for': ['css', 'scss', 'vim', 'html']}
    autocmd! User nvim-colorizer.lua lua require'colorizer'.setup {css = {css = true}; scss = {css = true}, 'vim', 'html'}
  endif

  " vim-gh-line - open the current file/line on github/gitlab etc
  " See also: https://github.com/tyru/open-browser-github.vi
  " Use :GHInteractive to open the current line in github or :GBInteractive to
  " open Blame view
  let g:gh_line_map_default = 0
  let g:gh_line_blame_map_default = 0
  let g:gh_line_repo_map_default = 0
  Plug 'https://github.com/ruanyl/vim-gh-line'

  " TODO: have a crack at some of these plugins
  " Plug 'chrisbra/NrrwRgn'
  " https://github.com/prettier/prettier
  " https://github.com/tpope/vim-projectionist
  " https://github.com/danro/rename.vim
  " https://github.com/shougo/deoplete.nvim
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
  " https://github.com/galooshi/vim-import-js
  " https://github.com/ruanyl/vim-sort-imports
  " https://github.com/skywind3000/vim-quickui
  " https://github.com/mg979/vim-visual-multi
  " https://github.com/nvim-treesitter/completion-treesitter
  " https://github.com/wellle/context.vim
  " https://github.com/romgrk/nvim-treesitter-context
  " https://github.com/romgrk/searchReplace.vim
  " https://github.com/romgrk/barbar.nvim
  call plug#end() " }}}
endif

" configure diagnostics globally
if has('nvim')
  lua vim.diagnostic.config({
        \ virtual_text=false,
        \ })
endif

fun! <SID>InitLSPBuffer()
  " turn off ALE
  ALEDisableBuffer

  " hide diagnostics by default
  lua vim.diagnostic.hide()

  " XXX: I'm using vim.lsp.buf.code_action() here instead of
  " :TSLspImportCurrent because sometimes there are multiple sources to import
  " from
  " XXX: I wanted this to do the code_action _and_ then format the buffer;
  " however code_action() seems to actually be async and so the prompt ends up
  " appearing _after_ the buffer has been formatted :facepalm:
  nnoremap <buffer> <space>i :lua vim.lsp.buf.code_action()<CR>
  if &l:filetype == 'typescript' || &l:filetype == 'typescriptreact'
    nnoremap <buffer> <space>I :TSLspOrganize<CR>
  else
    nnoremap <buffer> <space>I :echoerr 'No "\<space>I" import organizer is defined for this filetype'
  endif
  nnoremap <buffer> <F7>     :sp <BAR> lua vim.lsp.buf.references()<CR>
  nnoremap <buffer> <space>d :sp <BAR> lua vim.lsp.buf.definition()<CR>
  nnoremap <buffer> <space>h :lua vim.lsp.buf.hover()<CR>
  nnoremap <buffer> <space>f :lua vim.lsp.buf.incoming_calls()<CR>
  nnoremap <buffer> \a       :lua vim.diagnostic.goto_next()<CR>
  nnoremap <buffer> \A       :call <SID>ToggleDiagnostic()<CR>

  " XXX: if formatting doesn't seem to do anything it probably means you need
  " to install 'prettier' into your project. The guide I based this on
  " recommended using 'npm install -g prettier' however I'm keen to avoid
  " having a global version that gets stale / differs between machines
  nnoremap <buffer> \f       :lua vim.lsp.buf.format()<CR>
  nnoremap <buffer> \F       :call <SID>ToggleAutoFormatting()<CR>
  command! -nargs=0 -buffer Format lua vim.lsp.buf.format()

  " TODO: tidy this up so we're *not* using ALE namespace vars
  let b:ale_fix_on_save = 0
  aug PeterLSPAutoFormat
  au! BufWritePre <buffer> exe b:ale_fix_on_save ? 'lua vim.lsp.buf.format()' : ''
  aug end
endfun

fun! <SID>ToggleAutoFormatting()
  if get(b:, 'ale_fix_on_save', 0)
    let b:ale_fix_on_save = 0
  else
    let b:ale_fix_on_save = 1
  endif
  echohl WarningMsg
  echo printf('b:ale_fix_on_save = %s', b:ale_fix_on_save)
  echohl None
endfun

fun! <SID>ToggleDiagnostic()
  if get(b:, 'peter_show_diagnostic', 0)
    lua vim.diagnostic.show()
    let b:peter_show_diagnostic = 0
  else
    lua vim.diagnostic.hide()
    let b:peter_show_diagnostic = 1
  endif
endfun

if s:ts_lsp
  aug PeterLSPInit
  au!
  au FileType typescript,typescriptreact,javascript call <SID>InitLSPBuffer()
  aug end

  exe printf('source %s/vim_lsp_config.lua', s:dotfiles_root)
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

" I keep getting errors from options.txt helpfile, and I don't think I'm using
" this anyway
set nomodeline " modelines=2000

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
" have the quickfix window open below the current window instead of hijacking
" another open window
set switchbuf=split

if has('nvim-0.9.0')
  " supposedly this improves the quality of diffs
  set diffopt+=linematch:60
endif

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

    " make sure CTRL+A to go to start of line works in :command mode, too
    cnoremap <C-A> <Home>

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
  nnoremap \g :tab sp<CR>:exe (exists(':Git') =~ '[12]' ? 'Git' : 'Shell hg st')<CR><C-W>w:close<CR>:tabmove<CR>
 "nnoremap \g :tab sp<CR>:exe (exists(':Git') =~ '[12]' ? 'Git' : 'Shell hg st')<CR>1<C-W>w:close<CR>1<C-W>w:tabmove<CR>

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
if g:jerjerrod_cache_clearing
  au! Jerjerrod BufWritePost * call <SID>JerjerrodInit()
endif

fun! <SID>JerjerrodInit()
  " replace or remove the autocommand
  au! Jerjerrod
  if executable('jerjerrod')
    " reinstall the autocmd here - we don't want to do this when vim starts up
    " because the call to executable() may be expensive
    au! Jerjerrod BufWritePost * call <SID>JerjerrodClearCache()

    " make sure we clear the cache right now, since this init was triggered by
    " a BufWritePost
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


let s:skeletons_dir = s:dotfiles_root.'/vim/skeletons'
aug Skeletons
au!
au BufNewFile *.tsx call <SID>NamedSkeleton('component.tsx', expand('<afile>'))
au BufNewFile retest.sh call <SID>NamedSkeleton('retest.sh', expand('<afile>'))
au BufNewFile rebuild.sh call <SID>NamedSkeleton('rebuild.sh', expand('<afile>'))
aug end

" {{{ retest.sh / rebuild.sh

  fun! <SID>Retest(sockname, filename)
    " open the test file in a buffer if we haven't seen it before
    if bufnr(a:filename) == -1
      execute 'split' a:filename
    elseif ! filereadable(a:sockname)
      echoerr a:sockname . ' does not exist'
    else
      exe '!nudge - ' . a:sockname
      redraw!
    endif
  endfun

  nnoremap <space>t :call <SID>Retest('./.retest', 'retest.sh')<CR>
  nnoremap <space>b :call <SID>Retest('./.rebuild', 'rebuild.sh')<CR>
  nnoremap <space>T :split retest.sh<CR>
  nnoremap <space>B :split rebuild.sh<CR>

" }}}


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

aug TODOTXT
au! BufReadPost TODO.txt setlocal sw=2 sts=2 ts=2 et filetype=est
aug end


com! -nargs=0 NChanged Shell git diff origin/master... --name-status --no-renames; git status --short

" have had to add this as git commit hooks wreak havoc with my open buffers if
" they reformat them
setglobal noautoread

let s:vim_entered = 1
