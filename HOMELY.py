from homely.general import lineinfile

# git ignore
lineinfile('~/.gitignore', '*.swp')
lineinfile('~/.gitignore', '*.swo')
