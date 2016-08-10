from homely.ui import yesnooption
from homely.general import lineinfile, mkdir, symlink, run
from homely.general import section, haveexecutable
from homely.install import InstallFromSource
from homely.pipinstall import pipinstall


full_install = not yesnooption(
    'only_config',
    'Minimal install? (Config files only - nothing extra installed)')

# simple symlinks
symlink('.screenrc')

# create ~/bin and ~/src if they don't exist yet
mkdir('~/src')
mkdir('~/bin')

# TODO: need to ensure ~/bin is in our $PATH


# git ignore
@section
def gitconfig():
    lineinfile('~/.gitignore', '*.swp')
    lineinfile('~/.gitignore', '*.swo')


@section
def pipfavourites():
    versions = [3]
    if haveexecutable('pip2'):
        versions.append(2)
    pipinstall('click', versions, user=True)
    pipinstall('simplejson', versions, user=True)
    if full_install or yesnooption('install_ipython', 'PIP Install iPython?'):
        pipinstall('ipython', versions, user=True)
    if full_install or yesnooption('install_python_q', 'PIP Install `q`?'):
        pipinstall('q', versions, user=True)


@section
def vimconfig():
    # needed for vim also
    #pipinstall('powerline-status', 3, user=True)
    # TODO: add this section
    pass


# install nudge
@section
def nudge():
    # TODO: remove this line
    return
    if yesnooption('install_nudge', 'Install nudge?', default=full_install):
        nudge = InstallFromSource('https://github.com/toomuchphp/nudge.git',
                                  '~/src/nudge.git')
        nudge.select_branch('master')
        nudge.symlink('bin/nudge', '~/bin/nudge')
        run(nudge)


# install tmux
@section
def tmux():
    # TODO: get this working
    return
    if yesnooption('install_tmux', 'Install tmux?', default=full_install):
        # needed for tmux
        pipinstall('powerline-status', 3, user=True)
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
            run(tmux)
        else:
            from homely.general import installpkg
            # install tmux using brew or apt-get ...
            installpkg('tmux')
