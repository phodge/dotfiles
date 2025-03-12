" Project: blog.git
" ProjectID: d160c7458fc034eaf6bf2ebe769f87b8b72aed6a


" TODO: place your project init commands here
function projectconfig.BufEnter() dict
  let b:repo_todo_prefix = 'BLOG'

  if &l:filetype == 'markdown'
    setlocal textwidth=99
    setlocal sw=2 sts=2 ts=2 et
    let b:ale_markdown_markdownlint_executable = 'markdownlint'
    ALELint
  endif
endfun
