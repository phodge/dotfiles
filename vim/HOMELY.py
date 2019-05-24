import os

from homely.general import (WHERE_END, WHERE_TOP, blockinfile, download,
                            lineinfile, mkdir, run, section, symlink,
                            writefile)
from homely.install import InstallFromSource, installpkg
from homely.system import execute, haveexecutable
from homely.ui import allowinteractive, yesno

from HOMELY import (HERE, HOME, allowinstallingthings, install_nvim_via_apt,
                    jerjerrod_addline, mypips, need_installpkg, wantfull,
                    wantjerjerrod, wantnvim, whenmissing)

VIM_TAG = 'v8.1.0264'
NVIM_TAG = 'v0.3.1'


@section
def vim_config():
    # install vim-plug into ~/.vim
    mkdir('~/.vim')
    mkdir('~/.nvim')
    mkdir('~/.config')
    mkdir('~/.config/nvim')
    symlink('~/.vimrc', '~/.config/nvim/init.vim')
    mkdir('~/.vim/autoload')
    download('https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim',
             '~/.vim/autoload/plug.vim')

    def mkdir_r(path):
        assert len(path)
        if os.path.islink(path):
            raise Exception("Cannot mkdir_r(%r): path already exists but is a symlink" % path)

        # if the thing already exists but isn't a dir, then we can't create it
        if os.path.exists(path) and not os.path.isdir(path):
            raise Exception("Cannot mkdir_r(%r): path already exists but is not a dir" % path)

        # create the parent then our target path
        parent = os.path.dirname(path)
        if len(parent) > 5:
            mkdir_r(parent)
        mkdir(path)

    def _static(url, dest):
        dest = HOME + '/.vimstatic/' + dest
        mkdir_r(os.path.dirname(dest))
        download(url, dest)

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
                    '  if filereadable(%r)' % vprefs,
                    '    source %s' % vprefs,
                    '  endif',
                    '  if has(\'nvim\') && filereadable(%r)' % nprefs,
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
        if allowinteractive():
            if yesno(None, 'Use system clipboard in vim? (clipboard=unnamed)', None):
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

    # if we have jerjerrod installed, add an ALWAYSFLAG entry for git repos in ~/src/plugedit
    if False and wantjerjerrod():
        mkdir('~/.config')
        mkdir('~/.config/jerjerrod')
        lineinfile('~/.config/jerjerrod/jerjerrod.conf', 'PROJECT ~/src/plugedit/*.git ALWAYSFLAG')

    # icinga syntax/filetype
    if yesno('want_vim_icinga_stuff', 'Install vim icinga2 syntax/ftplugin?', default=False):
        files = ['syntax/icinga2.vim', 'ftdetect/icinga2.vim']
        for name in files:
            url = 'https://raw.githubusercontent.com/Icinga/icinga2/master/tools/syntax/vim/{}'
            _static(url.format(name), name)

    # <est> utility
    hasphp = haveexecutable('php')
    if yesno('install_est_utility', 'Install <vim-est>?', hasphp):
        est = InstallFromSource('https://github.com/phodge/vim-est.git',
                                '~/src/vim-est.git')
        est.select_branch('master')
        est.symlink('bin/est', '~/bin/est')
        run(est)


@section
def vim_install():
    if not allowinstallingthings():
        return

    # TODO: prompt to install a better version of vim?
    # - yum install vim-enhanced
    if not yesno('compile_vim', 'Compile vim from source?', wantfull()):
        return

    local = HOME + '/src/vim.git'

    mkdir('~/.config')
    flagsfile = HOME + '/.config/vim-configure-flags'
    written = False
    if not os.path.exists(flagsfile):
        written = True
        # pull down git source code right now so that we can see what the configure flags are
        if not os.path.exists(local):
            execute(['git', 'clone', 'https://github.com/vim/vim.git', local])
        out = execute([local + '/configure', '--help'], stdout=True, cwd=local)[1]
        with open(flagsfile, 'w') as f:
            f.write('# put configure flags here\n')
            f.write('--with-features=huge\n')
            f.write('--enable-pythoninterp=yes\n')
            f.write('--enable-python3interp=yes\n')
            f.write('\n')
            f.write('\n')
            for line in out.decode('utf-8').split('\n'):
                f.write('# ')
                f.write(line)
                f.write('\n')
    if yesno(None, 'Edit %s now?' % flagsfile, written, noprompt=False):
        execute(['vim', flagsfile], stdout="TTY")

    # install required libraries first
    need_installpkg(apt=(
        'libtool',
        'libtool-bin',
        'autoconf',
        'automake',
        'cmake',
        'g++',
        'pkg-config',
        'unzip',
        'ncurses-dev',
    ))
    inst = InstallFromSource('https://github.com/vim/vim.git', '~/src/vim.git')
    inst.select_tag(VIM_TAG)
    configure = ['./configure']
    with open(flagsfile) as f:
        for line in f:
            if not line.startswith('#'):
                configure.append(line.rstrip())
    inst.compile_cmd([
        ['make', 'distclean'],
        configure,
        ['make'],
        ['sudo', 'make', 'install'],
    ])
    run(inst)


@section
def nvim_install():
    if not wantnvim():
        return

    if install_nvim_via_apt():
        installpkg('neovim')
        installpkg('python-neovim')
        return

    if (allowinstallingthings() and
            haveexecutable('brew') and
            yesno('install_nvim_package', 'Install nvim from apt/brew?')):
        installpkg('neovim')
        return

    the_hard_way = yesno('compile_nvim',
                         'Compile/install nvim from source?',
                         recommended=allowinstallingthings()
                         )
    if not the_hard_way:
        raise Exception('No way to install neovim')

    need_installpkg(
        apt=(
            'libtool',
            'libtool-bin',
            'autoconf',
            'automake',
            'cmake',
            'g++',
            'pkg-config',
            'unzip',
            'gettext',
        ),
        yum=('cmake', 'gcc-c++', 'unzip'),
        brew=('cmake', 'libtool', 'gettext'),
    )
    n = InstallFromSource('https://github.com/neovim/neovim.git', '~/src/neovim.git')
    n.select_tag(NVIM_TAG)
    n.compile_cmd([
        ['make', 'distclean'],
        ['make'],
        ['sudo', 'make', 'install'],
    ])
    run(n)


@section
def nvim_devel():
    if not wantnvim():
        return

    if not yesno('install_nvim_devel', 'Put a dev version of neovim in playground-6?', False):
        return

    # my fork of the neovim project
    origin = 'ssh://git@github.com/phodge/neovim.git'
    # the main neovim repo - for pulling
    neovim = 'https://github.com/neovim/neovim.git'
    # where to put the local clone
    dest = HOME + '/playground-6/neovim'

    if not os.path.exists(dest):
        # NOTE: using execute() directly means the dest directory isn't tracked by
        # homely ... this is exactly what I want
        execute(['git', 'clone', origin, dest])
        execute(['git', 'remote', 'add', 'neovim', neovim], cwd=dest)
        execute(['git', 'fetch', 'neovim', '--prune'], cwd=dest)

    # create the symlink for the neovim project
    mkdir('~/playground-6')
    symlink(HERE + '/vimproject/neovim', dest + '/.vimproject')


@section
def neovim_python_devel():
    if not wantnvim():
        return

    playground = 'playground-neovim-python'
    venv = HOME + '/' + playground

    msg = 'Put a dev version of neovim-python in %s?' % playground
    if not yesno('install_neovim_python', msg, False):
        return

    # my fork of the neovim project
    origin = 'ssh://git@github.com/phodge/python-client.git'
    # the main neovim repo - for pulling
    neovim = 'https://github.com/neovim/python-client.git'
    # where to put the local clone
    checkout = venv + '/python-client.git'

    # create the symlink for the neovim project
    mkdir(venv)

    if not os.path.exists(checkout):
        # NOTE: using execute() directly means the checkout directory isn't tracked by homely ...
        # this is exactly what I want
        execute(['git', 'clone', origin, checkout])
        execute(['git', 'remote', 'add', 'neovim', neovim], cwd=checkout)
        execute(['git', 'fetch', 'neovim', '--prune'], cwd=checkout)

    if not os.path.exists(os.path.join(venv, 'bin')):
        execute(['virtualenv', '--python=python3', venv], stdout="TTY")

    if not os.path.exists(os.path.join(venv, 'bin')):
        execute(['virtualenv', '--python=python3', venv], stdout="TTY")

    # create a python2 virtualenv as well
    py2venv = os.path.join(venv, 'py2venv')
    if not os.path.exists(os.path.join(py2venv, 'bin')):
        execute(['virtualenv', '--python=python2.7', py2venv], stdout="TTY")

    # create a symlink to the git repo
    symlink(checkout, os.path.join(py2venv, 'python-client.git'))

    for path in [venv, py2venv]:
        pip = os.path.join(path, 'bin', 'pip')
        execute([pip, 'install', '--editable', 'python-client.git'], cwd=path)
        mypips(pip)
        # we will definitely need tests
        execute([pip, 'install', 'nose'])

    if wantjerjerrod():
        # register the playground with jerjerrod
        jerjerrod_addline('WORKSPACE', venv, ignore=["py2venv"])


@section
def vim_plugin_update():
    if allowinteractive():
        execute(['vim', '+PlugClean', '+PlugUpdate'], stdout="TTY")
        if wantnvim():
            execute(['nvim', '+PlugClean', '+PlugUpdate'], stdout="TTY")
        return

    # install the self-updating plugins now
    if True:
        template = '#!/usr/bin/env bash\nvim-update-then-run {} "$@"\n'
        for what in ('vim', 'nvim'):
            exec_ = HOME + '/bin/' + what
            with writefile(exec_) as f:
                f.write(template.format(what))
            os.chmod(exec_, 0o755)
