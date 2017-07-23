" whenever we open a gitcommit, pull up the staged changes
if !&previewwindow
  call gitmagic#ShowIndex()
endif
