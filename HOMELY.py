import os

from subprocess import check_output

from homely.ui import yesnooption
from homely.general import lineinfile, blockinfile, mkdir, symlink, run, WHERE_TOP, WHERE_END
from homely.general import download
from homely.general import section, haveexecutable
from homely.install import InstallFromSource, installpkg
from homely.pipinstall import pipinstall


HERE = os.path.dirname(__file__)


full_install = not yesnooption(
    'only_config',
    'Minimal install? (Config files only - nothing extra installed)')

# simple symlinks
symlink('.screenrc')

# create ~/bin and ~/src if they don't exist yet
mkdir('~/src')
mkdir('~/bin')

# TODO: need to ensure ~/bin is in our $PATH


if full_install:
    @section
    def sys():
        import subprocess
        if not haveexecutable('pip2'):
            if yesnooption('global_pip2', 'Install pip2 systemwide?'):
                cmd = 'curl https://bootstrap.pypa.io/get-pip.py | sudo python2'
                subprocess.check_call(cmd, shell=True)


@section
def pipfavourites():
    versions = [3]
    if haveexecutable('pip2'):
        versions.append(2)
    pipinstall('pytest', versions, user=True)
    pipinstall('click', versions, user=True)
    pipinstall('simplejson', versions, user=True)
    if full_install or yesnooption('install_ptpython', 'PIP Install ptpython?'):
        pipinstall('ptpython', versions, user=True)
    if full_install or yesnooption('install_ipython', 'PIP Install iPython?'):
        pipinstall('ipython', versions, user=True)
    if full_install or yesnooption('install_python_q', 'PIP Install `q`?'):
        pipinstall('q', versions, user=True)
    if full_install or yesnooption('install_flake8', 'PIP Install flake8?'):
        pipinstall('flake8', versions, user=True)


@section
def git():
    # include our dotfiles git config from ~/.gitconfig
    lineinfile('~/.gitconfig', "[include] path = %s/git/config" % HERE, where=WHERE_TOP)

    # put our standard ignore stuff into ~/.gitignore
    with open('%s/git/ignore' % HERE, 'r') as f:
        lines = [l.rstrip('\r\n') for l in f.readlines()]
        blockinfile('~/.gitignore',
                    lines,
                    "# exclude items from phodge/dotfiles",
                    "# end of items from phodge/dotfiles",
                    where=WHERE_TOP)

    download('https://github.com/git/git/blob/master/contrib/completion/git-completion.bash',
             '~/src/git-completion.bash')
    lineinfile('~/.bashrc', 'source $HOME/src/git-completion.bash', where=WHERE_END)


@section
def hg():
    versions = []
    if haveexecutable('pip2'):
        versions.append(2)
    if haveexecutable('pip3'):
        versions.append(3)
    pipinstall('mercurial_keyring', versions, user=True)
    # include our hg config from ~/.hgrc
    lineinfile('~/.hgrc', '%%include %s/hg/hgrc' % HERE, where=WHERE_TOP)

    # make a block in ~/.hgignore using hg/ignore
    with open('%s/hg/ignore' % HERE, 'r') as f:
        lines = [l.rstrip('\r\n') for l in f.readlines()]
        blockinfile('~/.hgignore',
                    lines,
                    "# exclude items from phodge/dotfiles",
                    "# end of items from phodge/dotfiles",
                    where=WHERE_TOP)




@section
def vimconfig():
    # needed for vim also
    #pipinstall('powerline-status', 3, user=True)
    # TODO: add this section
    pass


# install nudge
@section
def nudge():
    if yesnooption('install_nudge', 'Install nudge?', default=full_install):
        nudge = InstallFromSource('https://github.com/toomuchphp/nudge.git',
                                  '~/src/nudge.git')
        nudge.select_branch('master')
        nudge.symlink('bin/nudge', '~/bin/nudge')
        run(nudge)


# configure tmux
if yesnooption('install_tmux', 'Install tmux?', default=full_install):
    tmux_plugins = yesnooption('install_tmux_plugins', 'Install TPM and use tmux plugins?', default=full_install)

    @section
    def configure_tmux():
        # needed for tmux
        pipinstall('powerline-status', [3], user=True)

        if tmux_plugins:
            mkdir('~/.tmux')
            mkdir('~/.tmux/plugins')
            tpm = InstallFromSource('https://github.com/tmux-plugins/tpm',
                                    '~/.tmux/plugins/tpm')
            tpm.select_branch('master')
            run(tpm)

        # what to put in tmux config?
        powerline = check_output(['python3',
                                  '-c',
                                  'import powerline; print(powerline.__file__)'])
        wildcards = {
            "POWERLINE": os.path.dirname(powerline.strip().decode('utf-8')),
            "DOTFILES": HERE,
        }
        lines = [
            'run-shell "powerline-daemon -q"',
            'source "%(POWERLINE)s/bindings/tmux/powerline.conf"',
            'source "%(DOTFILES)s/tmux/tmux.conf"'
        ]
        if tmux_plugins:
            lines.append('source "%(DOTFILES)s/tmux/plugins.conf"')
            # FIXME: the only way to determine if TPM installed correctly is to
            # press `[PREFIX]`, `I` to do a plugin install
        lines = [l % wildcards for l in lines]
        blockinfile('~/.tmux.conf',
                    lines,
                    '# start of automated tmux config',
                    '# end of automated tmux config',
                    where=WHERE_TOP)

    @section
    def install_tmux():
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
            try:
                # install tmux using brew or apt-get ...
                installpkg('tmux')
            except:
                print("-" * 50)
                print("Compiling `tmux` failed - do you need to install automake or gcc?")
                print("-" * 50)
                raise
