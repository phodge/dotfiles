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


usepowerline = yesnooption('use_powerline', 'Use powerline for tmux/vim?', default=full_install)
if usepowerline:
    powerline_file = check_output(['python3',
                                    '-c',
                                    'import powerline; print(powerline.__file__)'])
    powerline_path = os.path.dirname(powerline_file.strip().decode('utf-8'))
    @section
    def powerline():
        mkdir('~/.config')
        mkdir('~/.config/powerline')
        paths = [
            "%s/config_files" % powerline_path,
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
                with open("%s/config_files/colors.json" % powerline_path) as f:
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


# configure tmux
if yesnooption('install_tmux', 'Install tmux?', default=full_install):
    tmux_plugins = yesnooption('install_tmux_plugins', 'Install TPM and use tmux plugins?', default=full_install)

    @section
    def configure_tmux():
        # needed for tmux
        if usepowerline:
            pipinstall('powerline-status', [3], user=True)

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
        if usepowerline:
            wildcards["POWERLINE"] = powerline_path
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
