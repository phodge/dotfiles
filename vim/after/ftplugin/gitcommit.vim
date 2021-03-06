" stop adding linebreaks in my git commit files
setlocal formatoptions-=tl

" whenever we open a gitcommit, pull up the staged changes
if !&previewwindow && gitmagic#loaded
  try
    let s:pos = exists('*getcurpos') ? getcurpos() : getpos('.')
    call gitmagic#ShowIndex()
  finally
    call setpos('.', s:pos)
  endtry
endif

if v:version < 800
  " NOTE: older versions of vim don't support the `python3 << MARKER` syntax
  finish
endif

python3 << ENDOFPYTHON
import vim
import subprocess
import os.path

def FTPluginGitCommitInsertPrefix():
  buf = vim.current.buffer

  # if the starting line already has text, there's nothing we can do
  if buf[0] != '':
    return

  cmd = ['git', 'status', '--porcelain=v1']
  lines = subprocess.check_output(cmd).decode('utf-8').splitlines()
  files = []
  for line in lines:
    index = line[0]
    # ignore unmodified (' ') and untracked ('?') files
    if index in (' ', '?'):
      continue
    filename = line[3:]
    files.append(filename)
  longest = os.path.commonprefix(files).rstrip('/')

  cmd = ['git', 'rev-parse', '--show-toplevel']
  root = subprocess.check_output(cmd).decode('utf-8').strip()

  lookfor = ('setup.py', 'Dockerfile', 'setup.cfg')
  maxexamine = 3

  # start at the deepest level looking for one of our special files
  parts = longest.split('/')

  def _insertprefix(prefix):
    buf[0] = prefix + ': '
    vim.command('setlocal modified')

  def _tryprefix(prefix):
    for special in lookfor:
      what = os.path.join(root, prefix, special)
      if os.path.exists(what):
        _insertprefix(prefix)
        return True
    return False

  for examine in range(3, 0, -1):
    prefix = os.path.join(*parts[:examine])
    if _tryprefix(prefix):
      break
  else:
    _insertprefix(longest)

ENDOFPYTHON

" is the first line of the file blank?
if !&l:modified
  python3 FTPluginGitCommitInsertPrefix()
endif
