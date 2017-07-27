" whenever we open a gitcommit, pull up the staged changes
if !&previewwindow
  try
    let s:pos = getcurpos()
    call gitmagic#ShowIndex()
  finally
    call setpos('.', s:pos)
  endtry
endif
