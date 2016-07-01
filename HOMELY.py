from homely.ui import yesnooption
from homely.general import lineinfile, mkdir, add, section
from homely.install import InstallFromSource


full_install = not yesnooption(
    'only_config',
    'Minimal install? (Config files only - nothing extra installed)')

# create ~/bin and ~/src if they don't exist yet
mkdir('~/src')
mkdir('~/bin')

# TODO: need to ensure ~/bin is in our $PATH

# git ignore
with section('gitconfig'):
    lineinfile('~/.gitignore', '*.swp')
    lineinfile('~/.gitignore', '*.swo')


# install nudge
with section('nudge'):
    if yesnooption('install_nudge', 'Install nudge?', default=full_install):
    nudge = InstallFromSource('https://github.com/toomuchphp/nudge.git',
                              '~/src/nudge.git')
    nudge.select_branch('master')
    nudge.symlink('bin/nudge', '~/bin/nudge')
    add(nudge)


# install tmux
with section('tmux'):
    if yesnooption('install_tmux', 'Install tmux?', default=full_install):
    if yesnooption('own_tmux', 'Compile tmux from source?'):
            # FIXME: compiling tmux from source like this requires libevent ...
            # how do we make sure that that library has been installed?
        tmux = InstallFromSource('https://github.com/tmux/tmux.git',
                                 '~/src/tmux.git')
        tmux.select_tag('2.2')
        tmux.compile_cmd([
            ['sh', 'autogen.sh'],
            ['./configure'],
            ['make'],
        ])
        tmux.symlink('tmux', '~/bin/tmux')
        add(tmux)
    else:
        from homely.general import installpkg
        # install tmux using brew or apt-get ...
        installpkg('tmux')
