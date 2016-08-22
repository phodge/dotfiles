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


def _wantpowerline():
    global _wantpowerline
    result = yesnooption('use_powerline', 'Use powerline for tmux/vim?', default=full_install)
    _wantpowerline = lambda: result
    return result


def _powerline_path():
    global _powerline_path
    powerline_file = check_output(['python3',
                                   '-c',
                                   'import powerline; print(powerline.__file__)'])
    result = os.path.dirname(powerline_file.strip().decode('utf-8'))
    _powerline_path = lambda: result
    return result


@section
def powerline():
    if _wantpowerline():
        mkdir('~/.config')
        mkdir('~/.config/powerline')
        paths = [
            "%s/config_files" % _powerline_path(),
            "%s/powerline" % HERE,
            "%s/.config/powerline" % HOME,
        ]
        lineinfile('~/.bashrc',
                   'export POWERLINE_CONFIG_PATHS=%s' % ":".join(paths),
                   where=WHERE_END)

        # ask the user what colour prefs they would like ... put it in ~/.config/powerline/colors.sh
        colourfile = os.path.join(HOME, '.config', 'powerline', 'colours.sh')
        load = False
        defaults = dict(
            bg="gray1",
            fg1="white",
            fg2="gray6",
        )
        if not os.path.exists(colourfile):
            if isinteractive() and yesno('Select base colours now?', True):
                # load available colours from colors.json
                with open("%s/config_files/colors.json" % _powerline_path()) as f:
                    import simplejson
                    colors = simplejson.load(f)
                with open(colourfile, 'w') as f:
                    f.write("# primary background colour\n")
                    f.write("bg=%(bg)s\n" % defaults)
                    f.write("# foreground colour for highlighted tab\n")
                    f.write("fg1=%(fg1)s\n" % defaults)
                    f.write("# foreground colour for other tabs\n")
                    f.write("fg2=%(fg2)s\n" % defaults)
                    f.write("# possible colours:\n")
                    for name in sorted(colors.get("colors", {})):
                        f.write("#   %s\n" % name)
                check_call(['vim', colourfile])
                load = True
        else:
            load = True
            if isinteractive() and yesno('Select base colours now?', False):
                check_call(['vim', colourfile])

        colourset = defaults
        if load:
            with open(colourfile, 'r') as f:
                for line in [l.rstrip() for l in f]:
                    if len(line) and not line.startswith('#'):
                        import pprint
                        print('line = ' + pprint.pformat(line))  # noqa TODO
                        name, val = line.split('=')
                        colourset[name] = val
        data = {}
        data["groups"] = {
            "window:current":       {"bg": colourset["bg"],  "fg": colourset["fg1"], "attrs": []},
            "window_name":          {"bg": colourset["bg"],  "fg": colourset["fg1"], "attrs": ["bold"]},
            "session:prefix":       {"bg": colourset["bg"],  "fg": "gray90", "attrs": ["bold"]},
            "active_window_status": {"fg": colourset["fg2"], "bg": "gray0", "attrs": []},
            "hostname":             {"bg": colourset["bg"],  "fg": "gray90", "attrs": []},
        }
        # write out a colorscheme override for tmux using our powerline colours
        mkdir('~/.config')
        mkdir('~/.config/powerline')
        mkdir('~/.config/powerline/colorschemes')
        mkdir('~/.config/powerline/colorschemes/tmux')
        import simplejson
        dumped = simplejson.dumps(data)
        with writefile('~/.config/powerline/colorschemes/tmux/default.json') as f:
            f.write(dumped)


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


def _wanttmux():
    global _wanttmux
    result = yesnooption('install_tmux', 'Install tmux?', default=full_install)
    _wanttmux = lambda: result
    return result


@section
def tmux_config():
    if _wanttmux():
        # needed for tmux
        if _wantpowerline():
            pipinstall('powerline-status', [3], user=True)

        tmux_plugins = yesnooption('install_tmux_plugins', 'Install TPM and use tmux plugins?', default=full_install)

        if tmux_plugins:
            mkdir('~/.tmux')
            mkdir('~/.tmux/plugins')
            tpm = InstallFromSource('https://github.com/tmux-plugins/tpm',
                                    '~/.tmux/plugins/tpm')
            tpm.select_branch('master')
            run(tpm)

        # what to put in tmux config?
        wildcards = {"DOTFILES": HERE}
        lines = []
        lines.append('source "%(DOTFILES)s/tmux/tmux.conf"')
        if _wantpowerline():
            wildcards["POWERLINE"] = _powerline_path()
            lines.extend([
                'run-shell "powerline-daemon -q"',
                'source "%(POWERLINE)s/bindings/tmux/powerline.conf"',
                'bind-key C-p source-file "%(POWERLINE)s/bindings/tmux/powerline.conf"',
            ])
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


# install or compile tmux
@section
def install_tmux():
    if _wanttmux():
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


@section
def ackrc():
    lineinfile('~/.ackrc', '--ignore-file=is:.tags')
