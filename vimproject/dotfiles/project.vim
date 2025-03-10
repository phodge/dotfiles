" Project: dotfiles
" ProjectID: 2e64ab62f236579dbde9f7af1cfbd4e00a3fe715

aug DotfilesSaveEffects
aug end

function projectconfig.BufEnter() dict
  let b:repo_todo_prefix = 'DOTFILES'

  if &l:filetype == 'python'
    nnoremap <space>t :call <SID>Retest()<CR>
  endif

  if bufname() =~ 'experiments.py'
    au! DotfilesSaveEffects BufWritePost <buffer> call <SID>RefreshExperiments('on_success')
    nnoremap <buffer> <space>b :call <SID>RefreshExperiments(v:false)<CR>
  endif
endfun

fun! <SID>RefreshExperiments(autoclose)
  return InAlacrittyWindow('homely update ~/dotfiles --nopull -o refresh_experiments', {'autoclose': a:autoclose})
endfun

fun! <SID>Retest()
  call InAlacrittyWindow('./retest.sh', {})
endfun

fun! projectconfig.api2024.filetypeDetect(bufnr, ext, basename, relname) dict
  if a:relname == 'git/config'
    return 'gitconfig'
  elseif a:relname =~ '^tmux/.*\.conf$'
    return 'tmux'
  endif
endfun
