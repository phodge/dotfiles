" create per-filetype versions of the function so that we remember to wrap
" them in &l:filetype guards
fun! peter#IDEFeaturesPython(flags)
  " currently only one flag is supported (to use pylsp) and it defaults to ON
  " Currently PyLSP is only used for jumping to definitions and showing docs
  return peter#LSPKeymapsFallback({
        \ 'activate_pylsp': a:flags.use_pylsp,
        \ })
endfun
fun! peter#IDEFeaturesJS(flags)
  return peter#LSPKeymapsFallback({
        \ 'lsp_manage_imports': a:flags.lsp_manage_imports,
        \ 'js_lsp_eslint_d': a:flags.lsp_eslint_d,
        \ 'js_vue_support': get(a:flags, 'with_vue', 0),
        \ 'is_js': v:true,
        \ })
endfun

" TODO: rename this thing also
fun! peter#LSPKeymapsFallback(flags = v:null)
  " NOTE: you probably want to use these in conjuction with
  " PeteLSP.init_ts_ls() or PeteLSP.init_null_ls() or some other
  " initialisation of your language server

  if a:flags is v:null
    " bail out if already run
    if exists('b:peter_keymaps_flags')
      return
    endif

    let l:flags = {}
  else
    if type(a:flags) != type({})
      echoerr 'a:flags must be a dict'
      return
    endif

    " if flags is the same as previous execution, bail out
    if a:flags == get(b:, 'peter_keymaps_flags', {'__no_previous_execution__': 1})
      return
    endif

    let l:flags = a:flags
  endif

  " remember flags used so that they don't get initialised again
  let b:peter_keymaps_flags = copy(l:flags)
  let b:peter_keymaps_count = get(b:, 'peter_keymaps_count', 0) + 1

  " set 'blank' keymaps that raise an error if nothing is configured for this
  " filetype
  call <SID>BlankKeymaps()

  " initialise 'default' keymaps for the relevant filetype
  let l:Callable = get(s:vanilla, &filetype, v:null)
  if l:Callable isnot v:null
    call call(l:Callable, [], {})
  endif

  " TODO(DOTFILES048): migrate more keymaps to this module, with relevant non-lsp
  " fallbacks

  let l:lsp_manage_imports = <SID>pop(l:flags, 'lsp_manage_imports', 0)
  let l:js_lsp_eslint_d = <SID>pop(l:flags, 'js_lsp_eslint_d', 0)
  let l:js_vue_support = <SID>pop(l:flags, 'js_vue_support', 0)

  " which keymaps to take over
  let l:lsp_keymaps = 0

  if l:lsp_manage_imports
    " XXX: For typescript I'm still using vim.lsp.buf.code_action() instead of
    " :TSLspImportCurrent because sometimes there are multiple sources to
    " import from.
    "
    " XXX: I wanted this to do the code_action _and_ then format the buffer;
    " however code_action() seems to actually be async and so the prompt ends up
    " appearing _after_ the buffer has been formatted :facepalm:
    nnoremap <buffer> <space>i :lua vim.lsp.buf.code_action()<CR>

    " TODO(DOTFILES051) actually implement an \f mapping in this file
    nnoremap <buffer> <space>I :echoerr 'vim/autoload/peter.vim does not define how to organize imports while lsp_manage_imports is active. You could instead try using \\f to format the whole file.'<CR>

    if &l:filetype == 'typescript' || &l:filetype == 'vue' || &l:filetype == 'typescriptreact'
      " see also https://www.reddit.com/r/neovim/comments/lwz8l7/comment/gpkueno/
      nnoremap <buffer> <space>I :TSLspOrganize<CR>
    endif
  endif

  " do we need to activate any language servers?
  if <SID>pop(l:flags, 'activate_pylsp', 0)
    " XXX: b:lsp_init_done is required due to a bug in vim-project-config
    " where it keeps executing the BufEnter function every time we move
    " between vim windows
    if ! get(b:, 'lsp_init_done', 0)
      lua require('PeteLSP').init_pylsp()
      LspStart
      let b:lsp_init_done = 1
    endif

    let l:lsp_keymaps = 1
  else
    " XXX: find a way to detach the language server from the current buffer
    " (and preferably shut it down if there's no other buffers using it)
  endif

  " TODO: do we always want to disable ALE when js_lsp_eslint_d is active?
  if l:js_lsp_eslint_d
    let b:ale_enabled = 0
  endif

  " do we need to start up any language servers?
  if <SID>pop(l:flags, 'is_js', 0) && (l:lsp_manage_imports || l:js_lsp_eslint_d)
    " XXX: b:lsp_init_done is required due to a bug in vim-project-config
    " where it keeps executing the BufEnter function every time we move
    " between vim windows
    if ! get(b:, 'lsp_init_done', 0)
      exe printf('lua require("PeteLSP").init_ts_ls({vue = %d})', l:js_vue_support)
      exe printf('lua require("PeteLSP").init_null_ls(%d)', l:js_lsp_eslint_d)
      LspStart
      let b:lsp_init_done = 1
    endif

    let l:lsp_keymaps = 1
  endif

  if l:lsp_keymaps
    nnoremap <buffer> <F7>     :sp <BAR> lua vim.lsp.buf.references()<CR>
    nnoremap <buffer> <space>d :sp <BAR> lua vim.lsp.buf.definition()<CR>
    nnoremap <buffer> <space>h :lua vim.lsp.buf.hover()<CR>
  endif

  " warn about unused keys
  for l:key in keys(l:flags)
    throw printf("WARNING: Unused key '%s' in peter#LSPKeymaps*()", l:key)
    break
  endfor
endfun

fun! <SID>pop(some_dict, some_key, some_default)
  return has_key(a:some_dict, a:some_key) ? remove(a:some_dict, a:some_key) : a:some_default
endfun

let s:vanilla = {}

fun! s:vanilla.python() dict
  " provided by Jedi
  nnoremap <buffer> <space>d :call jedi#goto()<CR>
  nnoremap <buffer> <space>h :call jedi#show_documentation()<CR>
  nnoremap <buffer> <space>r :call jedi#rename()<CR>
  nnoremap <buffer> <space>u :call jedi#usages()<CR>

  " use my filetype plugin if nothing special is configured
  nnoremap <buffer> <space>I :Isort<CR>
  nnoremap <buffer> <space>i :SmartIsortTrigger<CR>
endfun

fun! <SID>BlankKeymaps()
  nnoremap <buffer> <F7> :echoerr 'ERROR: No mapping configured for <F7> in vim/autoload/peter.vim'<CR>

  nnoremap <buffer> <space>d :echoerr 'ERROR: No mapping configured for <space>d in vim/autoload/peter.vim'<CR>
  nnoremap <buffer> <space>h :echoerr 'ERROR: No mapping configured for <space>h in vim/autoload/peter.vim'<CR>
  nnoremap <buffer> <space>r :echoerr 'ERROR: No mapping configured for <space>r in vim/autoload/peter.vim'<CR>
  nnoremap <buffer> <space>u :echoerr 'ERROR: No mapping configured for <space>u in vim/autoload/peter.vim'<CR>

  nnoremap <buffer> <space>i :echoerr 'ERROR: No mapping configured for <space>i in vim/autoload/peter.vim'<CR>
  nnoremap <buffer> <space>I :echoerr 'ERROR: No mapping configured for <space>I in vim/autoload/peter.vim'<CR>
endfun
