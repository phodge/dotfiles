import os
import platform
import re

from homely.general import (WHERE_END, WHERE_TOP, blockinfile, download,
                            haveexecutable, include, lineinfile, mkdir, run,
                            section, symlink)
from homely.install import InstallFromSource, installpkg
from homely.pipinstall import pipinstall
from homely.ui import system, yesno

HOME = os.environ['HOME']
HERE = os.path.dirname(__file__)


# decorator to make a function that caches its result temporarily
def cachedfunc(func):
    def wrapper(*args, **kwargs):
        try:
            return func._result
        except AttributeError as err:
            func._result = func(*args, **kwargs)
        return func._result
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper._result = None
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


def jerjerrod_addline(command, path, ignore=[]):
    # track projects in ~/src
    mkdir('~/.config')
    mkdir('~/.config/jerjerrod')
    # some sensible defaults for how I like to do things
    assert command in ("PROJECT", "WORKSPACE", "FORGET")
    flags = []
    flags += ["IGNORE={}".format(p) for p in ignore]
    lineinfile('~/.config/jerjerrod/jerjerrod.conf',
               "{} {} {}".format(command, path, " ".join(flags)).rstrip())


# install a local copy of neovim?
@cachedfunc
def wantnvim():
    return yesno('install_nvim', 'Install neovim?', wantfull())


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
    if yesno('install_ripgrep', 'Install ripgrep?', wantfull()):
        installpkg('ripgrep', apt=False)
    if yesno('install_with', 'Install `with` utility?', wantfull()):
        withutil = InstallFromSource('https://github.com/mchav/with',
                                     '~/src/with.git')
        withutil.symlink('with', '~/bin/with')
        withutil.select_branch('master')
        run(withutil)

    if yesno('install_universal_ctags', 'Install Universal Ctags?', wantfull()):
        mkdir('~/bin')
        if haveexecutable('brew'):
            # install with homebrew
            system(['brew', 'tap', 'universal-ctags/universal-ctags'])
            system(['brew', 'install', '--HEAD', 'universal-ctags'])
        else:
            uc = InstallFromSource('https://github.com/universal-ctags/ctags',
                                   '~/src/universal-ctags.git')
            uc.select_branch('master')
            uc.compile_cmd([
                ['./autogen.sh'],
                ['./configure'],
                ['make'],
            ])
            uc.symlink('ctags', '~/bin/ctags')
            run(uc)
    elif yesno('install_ctags', 'Install `ctags`?', wantfull()):
        installpkg('ctags')
    if yesno('install_patch', 'Install patch?', wantfull()):
        installpkg('patch')
    if yesno('install_fzf', 'Install fzf?', wantfull()):
        installpkg('fzf')

    # TODO: complete the code that installs markdown
    #if yesno('install_markdown', "Install markdown util?", wantfull()):
        #url = 'http://daringfireball.net/projects/downloads/Markdown_1.0.1.zip'
        # TODO: where do you want to put this thing?


@cachedfunc
def getpippaths():
    if platform.system() == "Darwin":
        return {}

    # do we need to out a pip config such that py2/py3 binaries don't clobber each other?
    question = 'Force pip to install into separate py2/py3 bin dirs?'
    if not yesno('force_pip_bin_paths', question, None):
        return {}

    scripts = {}

    for version in (2, 3):
        # TODO: we probably should drop into vim somewhere and make sure g:my_pyX_paths is
        # defined in prefs.vim or else our stuff is gonna be broken
        # TODO: we also want these in our $PATH ... or not?
        pip = "pip%d" % version
        var = "g:my_py%d_paths" % version

        if not haveexecutable(pip):
            continue

        stdout = system([pip, '--version'], stdout=True)[1].decode('utf-8').rstrip()
        assert re.search(r' \(python \d+\.\d+\)$', stdout)
        version = stdout.rsplit(' ', 1)[1][:-1]
        path = '%s/.local/python-%s-bin' % (HOME, version)

        scripts[pip] = path
        lineinfile('~/.vimrc', "let %s = ['%s']" % (var, path), where=WHERE_END)

    return scripts


def mypipinstall(*args, **kwargs):
    return pipinstall(*args, scripts=getpippaths(), **kwargs)


def mypips(venv_pip=None):
    # of course we probably want virtualenv!
    if venv_pip is None:
        pipinstall('virtualenv')

    theworks = wantfull() or venv_pip

    # these packages will be installed using the virtualenv's pip, or pip2+pip3 depending on what's
    # present
    packages = ['simplejson', 'jedi', 'yapf', 'isort']
    if wantnvim():
        # if we want nvim then we always want the neovim python package
        packages.append('neovim')
    if theworks or yesno('install_pytest', 'PIP Install pytest in $HOME?', True):
        packages.append('pytest')
    if theworks or yesno('install_ptpython', 'PIP Install ptpython?', True):
        packages.append('ptpython')
    if theworks or yesno('install_ipython', 'PIP Install iPython?', True):
        packages.append('ipython')
    if theworks or yesno('install_python_q', 'PIP Install `q`?', True):
        packages.append('q')
    for package in packages:
        if venv_pip:
            system([venv_pip, 'install', package])
        else:
            mypipinstall(package, trypips=['pip2', 'pip3'])

    # if it's a virtualenv, always just install flake8. Otherwise, we need to ask the user if
    # they want to install both
    if venv_pip:
        system([venv_pip, 'install', 'flake8'])
    else:
        have_pip3 = haveexecutable('pip3')
        if have_pip3 and yesno('install_flake8_python3', 'Install flake8 for python3?'):
            mypipinstall('flake8', ['pip3'])
        if yesno('install_flake8_python2', 'Install flake8 for python2?'):
            mypipinstall('flake8', ['pip2'])


@section
def pipfavourites():
    # install my favourite pip modules with --user
    mypips()

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

    # because we can't put the absolute path to our dotfiles hg/ignore file in
    # our hg/hgrc file, we have to put the config entry into the main ~/.hgrc
    # using a blockinfile()
    lines = [
        '[ui]',
        'ignore.dotfiles = {}/hg/ignore'.format(HERE),
    ]
    blockinfile('~/.hgrc', lines, WHERE_END)

    # grab a copy of crecord and put it in ~/src
    if haveexecutable('hg'):
        mkdir('~/src')
        localpath = HOME + '/src/crecord'
        if os.path.exists(localpath):
            system(['hg', 'pull', '--insecure'], cwd=localpath)
        else:
            url = 'https://bitbucket.org/edgimar/crecord'
            system(['hg', 'clone', '--insecure', url, localpath])


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


@section
def yapf():
    symlink('.style.yapf')


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


@section
def osx():
    if haveexecutable('defaults'):
        system(['defaults', 'write', 'NSGlobalDomain', 'InitialKeyRepeat', '-int', '15'])
        # KeyRepeat < 1.0 doesn't work :-(
        system(['defaults', 'write', 'NSGlobalDomain', 'KeyRepeat', '-float', '1.0'])


# TODO: https://github.com/clvv/fasd


# note that these need to be carried out in order of dependency
include('jerjerrod/HOMELY.py')
include('powerline/HOMELY.py')
include('tmux/HOMELY.py')
include('vim/HOMELY.py')
include('shell/HOMELY.py')
include('homely_dev/HOMELY.py')
