import os

from subprocess import check_output, check_call

from homely.ui import yesno, yesnooption, isinteractive
from homely.general import lineinfile, blockinfile, mkdir, symlink, run, WHERE_TOP, WHERE_END
from homely.general import download, writefile
from homely.general import section, haveexecutable
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


full_install = not yesnooption(
    'only_config',
    'Minimal install? (Config files only - nothing extra installed)')


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


if full_install:
    @section
    def sys():
        import subprocess
        if not haveexecutable('pip2'):
            if yesnooption('global_pip2', 'Install pip2 systemwide?'):
                cmd = 'curl https://bootstrap.pypa.io/get-pip.py | sudo python2'
                subprocess.check_call(cmd, shell=True)


# my favourite developer tools
@section
def tools():
    if yesnooption('install_ack', 'Install ack?', full_install):
        installpkg('ack', apt='ack-grep')
    if yesnooption('install_ag', 'Install ag?', full_install):
        installpkg('ag',
                   yum='the_silver_searcher',
                   apt='the_silver_searcher')
    if yesnooption('install_with', 'Install `with` utility?', full_install):
        withutil = InstallFromSource('https://github.com/mchav/with',
                                     '~/src/with.git')
        withutil.symlink('with', '~/bin/with')
        withutil.select_branch('master')
        run(withutil)


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

    download('https://raw.githubusercontent.com/git/git/master/contrib/completion/git-completion.bash',
             '~/src/git-completion.bash')
    lineinfile('~/.bashrc', 'source $HOME/src/git-completion.bash', where=WHERE_END)

    gitwip = InstallFromSource('https://github.com/phodge/git-wip.git',
                               '~/src/git-wip.git')
    gitwip.symlink('bin/git-wip', '~/bin/git-wip')
    gitwip.symlink('bin/git-unwip', '~/bin/git-unwip')
    gitwip.select_branch('master')
    run(gitwip)


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
    # install vim-plug into ~/.vim
    mkdir('~/.vim')
    mkdir('~/.nvim')
    mkdir('~/.vim/autoload')
    download('https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim',
             '~/.vim/autoload/plug.vim')

    # download pathogen to its own special place
    mkdir('~/.vimpathogen')
    mkdir('~/.vimpathogen/autoload')
    download('https://raw.githubusercontent.com/tpope/vim-pathogen/master/autoload/pathogen.vim',
             '~/.vimpathogen/autoload/pathogen.vim')

    vprefs = HOME + '/.vim/prefs.vim'
    nprefs = HOME + '/.nvim/prefs.vim'

    # chuck in a reference to our shiny new vimrc.vim (this will end up below the rtp magic block)
    lineinfile('~/.vimrc', 'source %s/vimrc.vim' % HERE, where=WHERE_TOP)

    # put our magic &rtp block at the top of our vimrc
    blockinfile('~/.vimrc',
                [
                    '  " reset rtp',
                    '  set runtimepath&',
                    '  " let other scripts know they\'re allowed to modify &rtp',
                    '  let g:allow_rtp_modify = 1',
                    '  " grab local preferences',
                    '  if exists(%r)' % vprefs,
                    '    source %s' % vprefs,
                    '  endif',
                    '  if has(\'nvim\') && exists(%r)' % nprefs,
                    '    source %s' % nprefs,
                    '  endif',
                ],
                '" {{{ START OF dotfiles runtimepath magic',
                '" }}} END OF dotfiles runtimepath magic',
                where=WHERE_TOP)

    # if the .vimrc.preferences file doesn't exist, create it now
    if not os.path.exists(vprefs):
        with open(vprefs, 'w') as f:
            f.write('let g:vim_peter = 1\n')

    # make sure we've made a choice about clipboard option in vprefs file
    @whenmissing(vprefs, 'clipboard')
    def addclipboard():
        if isinteractive():
            if yesno('Use system clipboard in vim? (clipboard=unnamed)', None):
                rem = "Use system clipboard"
                val = 'unnamed'
            else:
                rem = "Don't try and use system clipboard"
                val = ''
            with open(vprefs, 'a') as f:
                f.write('" %s\n' % rem)
                f.write("set clipboard=%s\n" % val)

    # put a default value about whether we want the hacky mappings for when the
    # terminal type isn't set correctly
    @whenmissing(vprefs, 'g:hackymappings')
    def sethackymappings():
        with open(vprefs, 'a') as f:
            f.write('" Use hacky mappings for F-keys and keypad?\n')
            f.write('let g:hackymappings = 0\n')

    # in most cases we don't want insight_php_tests
    @whenmissing(vprefs, 'g:insight_php_tests')
    def setinsightphptests():
        with open(vprefs, 'a') as f:
            f.write('" Do we want to use insight to check PHP code?\n')
            f.write('let g:insight_php_tests = []\n')

    # lock down &runtimepath
    lineinfile('~/.vimrc', 'let g:allow_rtp_modify = 0', where=WHERE_END)

    # <est> utility
    hasphp = haveexecutable('php')
    if yesnooption('install_est_utility', 'Install <vim-est>?', default=hasphp):
        est = InstallFromSource('https://github.com/phodge/vim-est.git',
                                '~/src/vim-est.git')
        est.select_branch('master')
        est.symlink('bin/est', '~/bin')
        run(est)


# install nudge
@section
def nudge():
    if yesnooption('install_nudge', 'Install nudge?', default=full_install):
        nudge = InstallFromSource('https://github.com/toomuchphp/nudge.git',
                                  '~/src/nudge.git')
        nudge.select_branch('master')
        nudge.symlink('bin/nudge', '~/bin/nudge')
        run(nudge)


@section
def projects():
    mkdir('~/playground-6')
    # TODO: my nvim clone
    # TODO: homely?
    # TODO: nudge?
    # TODO: any vim plugins I wrote?
    names = [
        ('homely', 'ssh://git@github.com/phodge/homely.git'),
    ]


# zsh
@section
def zshconfig():
    if yesnooption('use_zsh', 'Install zsh config?', default=full_install):
        antigen = InstallFromSource('https://github.com/zsh-users/antigen.git',
                                    '~/src/antigen.git')
        antigen.select_branch('master')
        run(antigen)


@section
def legacypl():
    if yesnooption('install_legacypl', 'Create clone of legacy-pl?', default=full_install):
        mkdir('~/playground-6')
        legacy = InstallFromSource('ssh://git@github.com/phodge/legacy-pl.git',
                                   '~/playground-6/legacy-pl.git')
        legacy.select_branch('develop')
        run(legacy)


@section
def ackrc():
    symlink('.ackrc')


# install a local copy of neovim?
install_nvim = yesnooption('install_nvim', 'Install neovim?', default=full_install)
@section
def nvim_install():
    if install_nvim:
        # NOTE: on ubuntu the requirements are:
        # apt-get install libtool libtool-bin autoconf automake cmake g++ pkg-config unzip
        n = InstallFromSource('https://github.com/neovim/neovim.git',
                              '~/src/neovim.git')
        n.select_tag('v0.1.5')
        # TODO: we want to make and make install, but not if we've already build this tag!
        # TODO: run nvim --version to find out if we're already running this version
        #n.compile_cmd([
            #['make'],
            #['make', 'install'],
        #])
        run(n)


@section
def nvim_devel():
    if not install_nvim:
        return

    # my fork of the neovim project
    origin = 'ssh://git@github.com/phodge/neovim.git'
    # the main neovim repo - for pulling
    neovim = 'https://github.com/neovim/neovim.git'
    # where to put the local clone
    dest = HOME + '/playground-6/neovim'

    if os.path.exists(dest):
        return

    if yesnooption('install_nvim_devel', 'Put a dev version of neovim in playground-6?', default=False):
        mkdir('~/playground-6')
        # NOTE: using check_call() means the dest directory isn't tracked by
        # homely ... and this is exactly what I want
        check_call(['git', 'clone', origin, dest])
        check_call(['git', 'remote', 'add', 'neovim', neovim], cwd=dest)
        check_call(['git', 'fetch', 'neovim', '--prune'], cwd=dest)


@cachedfunc
def wantpowerline():
    return yesnooption('use_powerline', 'Use powerline for tmux/vim?', default=full_install)


@cachedfunc
def powerline_path():
    cmd = ['python3', '-c', 'import powerline; print(powerline.__file__)']
    powerline_file = system(cmd, stdout=True)[1]
    return os.path.dirname(powerline_file.strip().decode('utf-8'))


include('powerline/HOMELY.py')
include('tmux/HOMELY.py')
