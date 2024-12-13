syn clear

syn match mypyTestHeading /^\[case .*\]$/
hi! link mypyTestHeading Statement

syn match mypyTestComment /^--.*$/
hi! link mypyTestComment Comment

"syn region mypyTestFileContent matchgroup=mypyTestFileHeader start=/\[file .*\]/ matchgroup=NONE end=/\n\ze\[/
syn match mypyTestFileHeader /^\[file .*\]$/ nextgroup=mypyTestFileContent skipnl skipempty
syn match mypyTestFileContent /^[^[].*$/ contained nextgroup=mypyTestFileContent skipnl skipempty
hi! link mypyTestFileHeader Keyword
hi! link mypyTestFileContent Function

syn region mypyTestCommand matchgroup=mypyTestCommandPrefix start=/^\$/ end=/$/ contains=mypyTestCommandPython
syn match mypyTestCommandPython /{python}/ contained
syn region mypyTestCommandResult matchgroup=mypyTestCommandPrefix start=/^== Return code:/ end=/$/
hi! link mypyTestCommandPrefix Operator
hi! link mypyTestCommandPython Identifier
hi! link mypyTestCommandResult String

