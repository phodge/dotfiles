import os

from homely.ui import yesno, system
from homely.general import lineinfile, blockinfile, mkdir, symlink, run, WHERE_TOP, WHERE_END
from homely.general import download
from homely.general import include, section, haveexecutable
from homely.install import InstallFromSource, installpkg
from homely.pipinstall import pipinstall


HOME = os.environ['HOME']
HERE = os.path.dirname(__file__)


# decorator to make a function that caches its result temporarily
def cachedfunc(func):
    haveresult = False
    result = None

    def wrapper(*args, **kwargs):
        nonlocal haveresult, result
        if not haveresult:
            haveresult = True
            result = func(*args, **kwargs)
        return result
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


@cachedfunc
def wantfull():
    return not yesno('only_config',
                     'Minimal install? (Config files only - nothing extra installed)',
                     None)


@cachedfunc
def wantjerjerrod():
    if not wantfull():
        return False
    return yesno('want_jerjerrod', 'Use jerjerrod for project monitoring?', True)


def whenmissing(filename, substr):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            for line in f:
                if substr in line:
                    # if the thing is already in the file, we don't need a
                    # proper decorator
                    return lambda fn: None

    # since we know the substr isn't in the file, we return a decorator that
    # will immediately call the decorated function
    return lambda fn: fn()


@section
def gnuscreen():
    symlink('.screenrc')


# create ~/bin and ~/src if they don't exist yet
mkdir('~/src')
mkdir('~/bin')
mkdir('~/man')
mkdir('~/man/man1')

# TODO: need to ensure ~/man is in our $MANPATH

# TODO: need to ensure ~/bin is in our $PATH


@section
def install_pip():
    if not wantfull():
        return
    import subprocess
    if not haveexecutable('pip2'):
        if yesno('global_pip2', 'Install pip2 systemwide?', None):
            cmd = 'curl https://bootstrap.pypa.io/get-pip.py | sudo python2'
            subprocess.check_call(cmd, shell=True)


# my favourite developer tools
@section
def tools():
    if yesno('install_ack', 'Install ack?', wantfull()):
        installpkg('ack', apt='ack-grep')
    if yesno('install_ag', 'Install ag?', wantfull()):
        installpkg('ag',
                   yum='the_silver_searcher',
                   apt='the_silver_searcher')
    if yesno('install_with', 'Install `with` utility?', wantfull()):
        withutil = InstallFromSource('https://github.com/mchav/with',
                                     '~/src/with.git')
        withutil.symlink('with', '~/bin/with')
        withutil.select_branch('master')
        run(withutil)

    if yesno('install_ctags', 'Install `ctags`?', wantfull()):
        installpkg('ctags')
    if yesno('install_patch', 'Install patch?', wantfull()):
        installpkg('patch')

    # TODO: complete the code that installs markdown
    #if yesno('install_markdown', "Install markdown util?", wantfull()):
        #url = 'http://daringfireball.net/projects/downloads/Markdown_1.0.1.zip'
        # TODO: where do you want to put this thing?


@section
def pipfavourites():
    packages = ['pytest', 'click', 'simplejson', 'jedi']
    if wantfull() or yesno('install_ptpython', 'PIP Install ptpython?', True):
        packages.append('ptpython')
    if wantfull() or yesno('install_ipython', 'PIP Install iPython?', True):
        packages.append('ipython')
    if wantfull() or yesno('install_python_q', 'PIP Install `q`?', True):
        packages.append('q')
    for package in packages:
        pipinstall(package, trypips=['pip2', 'pip3'])
    if wantfull() or yesno('install_flake8', 'PIP Install flake8?', True):
        # ask if we want to install flake8 using pip2, because some OS's use the same bin path and
        # python2's flake8 will overwrite python3's flake8
        pipinstall('flake8', ['pip3'])
        if yesno('install_flake8_python2', 'Install flake8 for python2?'):
            packages.append('flake8')
    # TODO: set up PYTHONPATH with our ~/dotfiles/python in it so we get todonext in our powerline


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

    url = 'https://raw.githubusercontent.com/git/git/master/contrib/completion/git-completion.bash'
    download(url, '~/src/git-completion.bash')
    lineinfile('~/.bashrc', 'source $HOME/src/git-completion.bash', where=WHERE_END)

    gitwip = InstallFromSource('https://github.com/phodge/git-wip.git',
                               '~/src/git-wip.git')
    gitwip.symlink('bin/git-wip', '~/bin/git-wip')
    gitwip.symlink('bin/git-unwip', '~/bin/git-unwip')
    gitwip.select_branch('master')
    run(gitwip)


@section
def hg():
    if yesno('mercurial_keyring', 'Install mercurial keyring?'):
        # TODO: this things needs python-devel and openssl-devel - should we
        # provide a suggestion to install those on non-OSX OS's?
        pipinstall('mercurial_keyring', trypips=['pip2', 'pip3', 'pip'])
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


# install nudge
@section
def nudge():
    if yesno('install_nudge', 'Install nudge?', wantfull()):
        nudge = InstallFromSource('https://github.com/toomuchphp/nudge.git',
                                  '~/src/nudge.git')
        nudge.select_branch('master')
        nudge.symlink('bin/nudge', '~/bin/nudge')
        run(nudge)


# zsh
@section
def zshconfig():
    if yesno('use_zsh', 'Install zsh config?', wantfull()):
        antigen = InstallFromSource('https://github.com/zsh-users/antigen.git',
                                    '~/src/antigen.git')
        antigen.select_branch('master')
        run(antigen)


@section
def legacypl():
    if yesno('install_legacypl', 'Create clone of legacy-pl?', wantfull()):
        mkdir('~/playground-6')
        legacy = InstallFromSource('ssh://git@github.com/phodge/legacy-pl.git',
                                   '~/playground-6/legacy-pl.git')
        legacy.select_branch('develop')
        run(legacy)


@section
def ackrc():
    symlink('.ackrc')


@cachedfunc
def wantpowerline():
    return yesno('use_powerline', 'Use powerline for tmux/vim?', wantfull())


@cachedfunc
def powerline_path():
    cmd = ['python3', '-c', 'import powerline; print(powerline.__file__)']
    powerline_file = system(cmd, stdout=True)[1]
    return os.path.dirname(powerline_file.strip().decode('utf-8'))


@section
def pypirc():
    rc = HOME + '/.pypirc'
    if not yesno('write_pypirc', 'Write a .pypirc file?', wantfull()):
        return
    if not os.path.exists(rc):
        with open(rc, 'w') as f:
            f.write('[distutils]\n')
            f.write('index-servers=pypi\n')
            f.write('\n')
            f.write('[pypi]\n')
            f.write('repository = https://upload.pypi.org/legacy/\n')
            f.write('# TODO: put your real username here\n')
            f.write('username = USERNAME\n')
            f.write('# TODO: put your real password here\n')
            f.write('password = PASSWORD\n')
    with open(rc) as f:
        if 'TODO' in f.read() and yesno(None, "Edit %s now?" % rc, True, noprompt=False):
                system(['vim', rc], stdout="TTY")
    system(['chmod', '600', rc])


# note that these need to be carried out in order of dependency
include('jerjerrod/HOMELY.py')
include('powerline/HOMELY.py')
include('tmux/HOMELY.py')
include('vim/HOMELY.py')
include('shell/HOMELY.py')
