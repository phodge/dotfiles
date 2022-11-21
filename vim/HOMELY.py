import os
from pathlib import Path

from homely.general import (WHERE_END, WHERE_TOP, blockinfile, download,
                            lineinfile, mkdir, run, section, symlink,
                            writefile)
from homely.install import InstallFromSource, installpkg
from homely.system import execute, haveexecutable
from homely.ui import allowinteractive, yesno

import HOMELY
from HOMELY import (HERE, HOME, allow_installing_stuff, install_nvim_via_apt,
                    jerjerrod_addline, memoize, mypips, need_installpkg,
                    want_full, wantjerjerrod, whenmissing)

VIM_TAG = 'v8.1.0264'

NVIM_TAG = 'v0.4.4'
# one of the nightly tags
NVIM_TAG = 'ca7449db4'


@memoize
def want_nvim_devel() -> bool:
    return HOMELY.wantnvim() and yesno(
        'install_nvim_devel',
        'Put a dev version of neovim in playground-6?',
        False,
    )


@memoize
def get_vim_options() -> dict[str, bool]:
    ret = {}

    # vim
    ret['g:peter_give_me_a_debugger'] = yesno(
        'vim_install_debugger_plugin',
        'Vim: install a debugger plugin?',
    )

    ret['g:peter_use_builtin_php_syntax'] = (not HOMELY.want_php_anything) or yesno(
        'vim_use_builtin_php_syntax',
        'Vim: use builtin php syntax?',
    )

    ret['g:jerjerrod_cache_clearing'] = HOMELY.wantjerjerrod() and yesno(
        'jerjerrod_clear_cache_in_vim',
        'Jerjerrod: automatic cache clearing in Vim using BufWritePost?',
        recommended=True,
    )

    # neovim
    ret['g:peter_want_nvimdev_plugin'] = want_nvim_devel() and yesno(
        'neovim_want_nvimdev_plugin',
        'Neovim: install nvimdev.nvim plugin for neovim development?',
    )

    use_treesitter = HOMELY.wantnvim() and yesno(
        'neovim_use_treesitter',
        'Neovim: use treesitter for syntax highlighting?',
    )
    ret['g:peter_want_treesitter'] = use_treesitter
    ret['g:peter_want_treesitter_python'] = use_treesitter and yesno(
        'neovim_use_treesitter_for_python',
        'Neovim: use treesitter for PYTHON syntax highlighting?',
    )

    # other technologies
    ret['g:peter_want_terraform_plugins'] = HOMELY.want_terraform_anything
    ret['g:peter_want_rust_plugins'] = HOMELY.want_rust_anything
    ret['g:peter_want_php_plugins'] = HOMELY.want_php_anything

    return ret


@section(quick=True)
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

    # do we want a debugger plugin in vim?
    for varname, varval in get_vim_options().items():
        lineinfile(
            '~/.vim/prefs.vim',
            f'let {varname} = {"1" if varval else "0"}  " set by phodge\'s dotfiles'.format(
                varname,
                '1' if varval else '0'
            ),
            where=WHERE_END,
        )

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


@section(enabled=allow_installing_stuff)
def vim_install():
    # TODO: prompt to install a better version of vim?
    # - yum install vim-enhanced
    if not yesno('compile_vim', 'Compile vim from source?', want_full):
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
            'ncurses-dev',
        ),
        brew=(
            'cmake',
            'libtool',
        ),
    )
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


@section(enabled=HOMELY.wantnvim())
def nvim_install():
    if install_nvim_via_apt():
        installpkg('neovim')
        installpkg('python-neovim')
        return

    if (allow_installing_stuff and
            haveexecutable('brew') and
            yesno('install_nvim_package', 'Install nvim from apt/brew?')):
        installpkg('neovim')
        return

    the_hard_way = yesno('compile_nvim',
                         'Compile/install nvim from source?',
                         recommended=allow_installing_stuff
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


@section(enabled=want_nvim_devel())
def nvim_devel():
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


@section(enabled=want_nvim_devel())
def neovim_python_devel():
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


@section(enabled=HOMELY.wantnvim())
def nvim_ls_ts():
    execute(['npm', 'install'], cwd=HERE + '/nvim_ts')
    # We need these two to be available globally as they probably won't exist in project packages.
    # The language server will also need 'prettier', 'typescript' and 'eslint'
    # packages, however those are more likely to be added to the project directly.
    symlink('nvim_ts/node_modules/.bin/typescript-language-server', '~/bin/typescript-language-server')
    symlink('nvim_ts/node_modules/.bin/eslint_d', '~/bin/eslint_d')


def _install_vim_selfupdater() -> None:
    template = '#!/usr/bin/env bash\nvim-update-then-run {} "$@"\n'
    for what in ('vim', 'nvim'):
        exec_ = HOME + '/bin/' + what
        with writefile(exec_) as f:
            f.write(template.format(what))
        os.chmod(exec_, 0o755)


@section(interval='2w')
def vim_plugin_update():
    triggerfile = Path(os.path.expanduser('~/.vim-self-update-plugins'))
    if allowinteractive():
        execute(['vim', '+PlugClean', '+PlugUpdate'], stdout="TTY")
        if HOMELY.wantnvim():
            execute(['nvim', '+PlugClean', '+PlugUpdate'], stdout="TTY")
        # remove trigger file so wrappers don't try to run plugin updates
        triggerfile.unlink(missing_ok=True)
        return

    # install the self-update wrappers now
    triggerfile.touch()
    _install_vim_selfupdater()


@section(interval=None if allowinteractive() else '2w', quick=False)
def vim_submodule_update():
    from HOMELY import pull_submodules

    pull_submodules('vim-packages')

    # now we need to run 'helptags' for each of these submodules
    commands = []
    for subdir in (Path(HERE) / 'vim-packages').iterdir():
        docsdir = subdir / 'doc'
        if docsdir.is_dir():
            commands.append(f'+helptags {docsdir}')
    if commands:
        execute(['vim'] + commands, stdout="TTY")
