from homely.ui import isinteractive, yesno, yesnooption
from homely.general import section
from HOMELY import HOME, HERE, whenmissing, cachedfunc, full_install


# install a local copy of neovim?
@cachedfunc
def _wantnvim():
    from homely.ui import yesnooption
    return yesnooption('install_nvim', 'Install neovim?', default=full_install)


@section
def vim_config():
    import os
    from homely.general import (
        mkdir, symlink, download, lineinfile, blockinfile, WHERE_TOP, WHERE_END,
        haveexecutable, run)
    from homely.install import InstallFromSource

    # install vim-plug into ~/.vim
    mkdir('~/.vim')
    mkdir('~/.nvim')
    mkdir('~/.config')
    mkdir('~/.config/nvim')
    symlink('~/.vimrc', '~/.config/nvim/init.vim')
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
        est.symlink('bin/est', '~/bin/est')
        run(est)


@section
def vim_install():
    import os
    from homely.ui import system
    from homely.general import run, mkdir
    from homely.install import InstallFromSource
    if not yesnooption('compile_vim', 'Compile vim from source?', full_install):
        return

    local = HOME + '/src/vim.git'

    mkdir('~/.config')
    flagsfile = HOME + '/.config/vim-configure-flags'
    if not os.path.exists(flagsfile):
        # pull down git source code right now so that we can see what the configure flags are
        if not os.path.exists(local):
            system(['git', 'clone', 'https://github.com/vim/vim.git', local])
        out = system([local + '/configure', '--help'], stdout=True, cwd=local)[1]
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
    if isinteractive() and yesno('Edit %s now?' % flagsfile, True):
        system(['vim', flagsfile], stdout="TTY")

    # NOTE: on ubuntu the requirements are:
    # apt-get install libtool libtool-bin autoconf automake cmake g++ pkg-config unzip
    inst = InstallFromSource('https://github.com/vim/vim.git', '~/src/vim.git')
    inst.select_tag('v8.0.0007')
    configure = ['./configure']
    with open(flagsfile) as f:
        for line in f:
            if not line.startswith('#'):
                configure.append(line.rstrip())
    inst.compile_cmd([
        configure,
        ['make'],
        ['sudo', 'make', 'install'],
    ])
    run(inst)


@section
def nvim_install():
    from homely.general import haveexecutable, run
    from homely.pipinstall import pipinstall
    from homely.install import InstallFromSource
    versions = [3]
    if haveexecutable('pip2'):
        versions.append(2)
    pipinstall('neovim', versions, user=True)
    if _wantnvim():
        # NOTE: on ubuntu the requirements are:
        # apt-get install libtool libtool-bin autoconf automake cmake g++ pkg-config unzip
        n = InstallFromSource('https://github.com/neovim/neovim.git', '~/src/neovim.git')
        n.select_tag('v0.1.5')
        n.compile_cmd([
            ['make'],
            ['sudo', 'make', 'install'],
        ])
        run(n)


@section
def nvim_devel():
    import os
    from homely.ui import yesnooption, system
    from homely.general import mkdir, symlink
    if not _wantnvim():
        return

    # my fork of the neovim project
    origin = 'ssh://git@github.com/phodge/neovim.git'
    # the main neovim repo - for pulling
    neovim = 'https://github.com/neovim/neovim.git'
    # where to put the local clone
    dest = HOME + '/playground-6/neovim'

    # create the symlink for the neovim project
    symlink(HERE + '/vimproject/neovim', dest + '/.vimproject')

    if os.path.exists(dest):
        return

    want_devel = yesnooption('install_nvim_devel',
                             'Put a dev version of neovim in playground-6?',
                             default=False)
    if want_devel:
        mkdir('~/playground-6')
        # NOTE: using system() directly means the dest directory isn't tracked by homely ... this
        # is exactly what I want
        system(['git', 'clone', origin, dest])
        system(['git', 'remote', 'add', 'neovim', neovim], cwd=dest)
        system(['git', 'fetch', 'neovim', '--prune'], cwd=dest)
