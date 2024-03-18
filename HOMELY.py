import glob
import json
import os
import os.path
import platform
import re
from pathlib import Path
from typing import List

from homely._ui import allowinteractive
from homely.general import (WHERE_END, WHERE_TOP, blockinfile, download,
                            haveexecutable, include, lineinfile, mkdir, run,
                            section, symlink, writefile)
from homely.install import InstallFromSource, installpkg, setallowinstall
from homely.pipinstall import pipinstall
from homely.system import execute
from homely.ui import yesno

HOME = os.environ['HOME']
HERE = os.path.dirname(__file__)


IS_OSX = platform.system() == "Darwin"
IS_UBUNTU = os.path.exists('/etc/lsb-release')

# folder for virtualenvs
mkdir('~/.venv')
POWERLINE_VENV = HOME + '/.venv/powerline'
NEOVIM_VENV = HOME + '/.venv/neovim'
WINWIN_VENV = HOME + '/.venv/winwin'


def section_macos(*, enabled=True, **kwargs):
    return section(enabled=enabled and IS_OSX, **kwargs)


def section_ubuntu(*, enabled=True, **kwargs):
    return section(enabled=enabled and IS_UBUNTU, **kwargs)


try:
    # try and build a memoize decorator from the one in functools
    from functools import lru_cache

    memoize = lru_cache(maxsize=None, typed=True)
except ImportError:
    # Otherwise, we just pretend. If this memoize() is used, no function caching will occur.
    def memoize(fn):
        return fn


# TODO: build a platform-neutral clipboard system
# - bin/C bin/P for copy/paste which is aliased to / or wraps system clipboard
# - detect when coming via X11 ssh ($DISPLAY is set?) and use xsel for clipboard, even on OSX
# - configure vim/nvim to use bin/C and bin/P and clipboard=unnamedplus
# - provide some mechanism for automatically doing the .ssh config to enable X11-forwarding to
#   specific hosts
# - find a mechanism that allows us to forward pbcopy/pbpaste from OS X
# - configure tmux to use bin/C and bin/P for copy+paste


want_full = not yesno(
    'only_config',
    'Minimal install? (Config files only - nothing extra installed)',
    None,
)

not_work_machine = not yesno(
    'is_work_machine',
    'Work computer?',
    None,
)

github_ssh_hack = yesno(
    'use_github_ssh_key_hack',
    'Use phodge.github.com git URL rewriting hack?',
    recommended=not not_work_machine,
)

allow_installing_stuff = want_full and yesno(
    'allow_install',
    'Allow installing of packages using yum/apt or `sudo make install` etc?',
    None
)

any_ancient_things = not_work_machine and yesno(
    'any_ancient_things',
    'Ask about installing ancient/legacy support tools?',
    None,
)

setallowinstall(allow_installing_stuff)


want_alacritty = allow_installing_stuff and yesno(
    'want_alacritty',
    'Install Alacritty?',
    default=None,
)

install_alacritty_homebrew = want_alacritty and IS_OSX and yesno(
    'install_alacritty_homebrew',
    'Install Alacritty via Homebrew?',
    recommended=True,
)

want_php_anything = any_ancient_things and yesno(
    'want_php_anything',
    'Bother with anything PHP-related?',
    False,
)

want_terraform_anything = yesno(
    'want_terraform_anything',
    'Bother with anything Terraform-related?',
)

want_rust_anything = yesno(
    'want_rust_anything',
    'Bother with anything Rust-related?',
)

want_mercurial = any_ancient_things and yesno(
    'want_mercurial',
    'Bother with anything mercurial-related?',
    False,
)

want_poetry = allow_installing_stuff and yesno(
    'want_python_poetry',
    'Install poetry in $HOME?',
    False,
)

create_homely_venv = want_full and not_work_machine and yesno(
    "create_homely_venv",
    "Create ~/playground-homely virtualenv?",
    False,
)

want_ripgrep = allow_installing_stuff and (IS_UBUNTU or yesno(
    'want_ripgrep',
    'Install ripgrep?',
    default=True,
    recommended=True,
    noprompt=True,
))

pipx_install_fn = None

# figure out our Ubuntu version
if IS_UBUNTU:
    LSB_RELEASE = {
        key: val
        for line in Path('/etc/lsb-release').read_text().splitlines()
        for key, val in [line.split('=')]
    }
    UBUNTU_MAJOR = int(LSB_RELEASE['DISTRIB_RELEASE'].split('.')[0])

if want_full:
    if IS_OSX:
        pipx_install_fn = lambda: installpkg('pipx', brew='pipx')  # noqa: E731
    elif IS_UBUNTU:
        def pipx_install_fn():
            if UBUNTU_MAJOR >= 2023:
                installpkg('pipx', apt='pipx')
                # TODO: not sure if this step from the official docs will be
                # required since I already add ~/.local/bin to $PATH
                # execute(['pipx', 'ensurepath'])
            else:
                execute(['python3', '-m', 'pip', 'install', '--user', 'pipx'])
                # NOTE: the docs ask for this but it seems to be unnecessary
                # for my Ubuntu 22.04 installs
                # execute(['python3', '-m', 'pipx', 'ensurepath'])


@memoize
def need_installpkg(*, apt=None, brew=None, yum=None):
    if not allow_installing_stuff:
        what = apt or brew or yum
        raise Exception("Can't install {} when only doing minimal config".format(what))

    if haveexecutable('apt-get'):
        for name in apt or []:
            installpkg(name,            brew=False, yum=False, port=False)
    if haveexecutable('brew'):
        for name in brew or []:
            installpkg(name, apt=False,             yum=False, port=False)
    if haveexecutable('yum'):
        for name in yum or []:
            installpkg(name, apt=False, brew=False,            port=False)


@memoize
def install_fedora_copr():
    if not allow_installing_stuff:
        return False

    if not haveexecutable('yum'):
        return False

    copr_url = 'https://copr.fedorainfracloud.org/coprs/carlwgeorge/ripgrep/repo/epel-7/carlwgeorge-ripgrep-epel-7.repo'
    if not yesno('allow_fedora_copr',
                 'Add fedora COPR repo on this host?',
                 None):
        return False

    # enable the repo
    installpkg('yum-utils')
    execute(['sudo', 'yum-config-manager', '--add-repo=' + copr_url], stdout="TTY")
    return True


@memoize
def wantjerjerrod():
    if not want_full:
        return False
    return yesno('want_jerjerrod', 'Use jerjerrod for project monitoring?', True)


@memoize
def want_silver_searcher():
    return yesno('install_ag', 'Install ag (required for fzf)?', want_full)


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


# install neovim?
@memoize
def wantnvim():
    return yesno('install_nvim', 'Install neovim?', want_full)


@memoize
def use_neovim_virtualenv():
    return wantnvim() and yesno(
        'use_neovim_virtualenv',
        'Use a dedicated virtualenv for neovim?',
        recommended=True,
    )


@memoize
def install_nvim_via_snap():
    if not wantnvim():
        return False

    if not allow_installing_stuff:
        return False

    if not IS_UBUNTU:
        return False

    return yesno('install_nvim_package', 'Install nvim from snap?')


@memoize
def wantzsh():
    return yesno('use_zsh', 'Install zsh config?', want_full)


@memoize
def want_unicode_fix():
    q = 'Old versions of glibc can cause render issues with GnomeTerminal>ssh>tmux>powerline. Remove Unicode chars in powerline status?'
    return yesno('want_unicode_fix', q)


@section(quick=True)
def run_mydots_configure():
    execute([
        HERE + '/bin/mydots-configure',
        '--automatic',
    ])


def venv_exec(venv_pip, cmd, **kwargs):
    import shlex
    env = kwargs.pop('env', None)
    if env is None:
        env = os.environ
    env.pop('__PYVENV_LAUNCHER__', None)
    activate = os.path.dirname(venv_pip) + '/activate'
    cmd = ['bash', '-c', 'source {} && {}'.format(activate, " ".join(map(shlex.quote, cmd)))]
    return execute(cmd, env=env, **kwargs)


def maintain_virtualenv(path: str, core_packages: List[str]) -> None:
    if not os.path.exists(path):
        # create the virtualenv
        execute(['python3', '-m', 'venv', path])

    # make sure we also upgrade build tools inside the virtualenv
    upgrade_packages = ['setuptools', 'pip']
    pip_exe = path + '/bin/pip'
    venv_exec(pip_exe, [pip_exe, 'install', '--upgrade'] + upgrade_packages)

    # make sure we also install/upgrade core packages in the virtualenv
    if core_packages:
        venv_exec(pip_exe, [pip_exe, 'install', '--upgrade'] + core_packages)


@section_ubuntu(enabled=allow_installing_stuff)
def install_python3_base_packages():
    installpkg('python3-venv')
    installpkg('python3-pip')


@section(enabled=github_ssh_hack)
def ssh_config_hack():
    mkdir('~/.ssh')
    execute(['chmod', '700', HOME + '/.ssh'])
    keyfile = HOME + '/.ssh/id_ed25519_phodge'

    if not os.path.exists(keyfile):
        execute(['ssh-keygen', '-t', 'ed25519', '-f', keyfile], stdout="TTY")
        yesno(None, f'You must now upload {keyfile}.pub to github.com and gitlab.com')

    lines = [
        'Host phodge.github.com',
        '\tHostName github.com',
        '\tIdentityFile ~/.ssh/id_ed25519_phodge',
    ]
    blockinfile('~/.ssh/config', lines, WHERE_TOP)
    execute(['chmod', '600', HOME + '/.ssh/config'])


@section(
    enabled=use_neovim_virtualenv(),
    # if virtualenv already exists, just upgrade it monthly
    interval='4w' if os.path.exists(NEOVIM_VENV) else None,
)
def create_neovim_venv():
    core_packages = [
        'pynvim',
        'GitPython',
    ]
    maintain_virtualenv(NEOVIM_VENV, core_packages)


@section()
def create_powerline_venv():
    core_packages = []
    if not create_homely_venv:
        # need to install homely for powerline from pypi if not developing
        # locally
        core_packages.append('homely')
    maintain_virtualenv(POWERLINE_VENV, core_packages)


@section(
    enabled=allow_installing_stuff,
    interval='4w' if os.path.exists(WINWIN_VENV) else None,
)
def create_winwin_venv():
    maintain_virtualenv(WINWIN_VENV, [])


@section(
    # if virtualenv already exists, just upgrade it monthly
    interval='4w' if os.path.exists(NEOVIM_VENV) else None,
)
def create_neovim_python_tools_venv():
    core_packages = [
        'flake8',
        'mypy',
    ]
    maintain_virtualenv(HOME + '/.venv/vim-python-tools', core_packages)


@section(enabled=allow_installing_stuff)
def create_winwin_config():
    winwincfg = Path(HOME) / '.config/winwin.json'

    try:
        config = json.loads(winwincfg.read_text())
    except FileNotFoundError:
        config = {}

    config['force_platform'] = config.get('force_platform', 'terminal/tmux')

    # if we're on macos, we need to configure winwin to use Alacritty as our
    # terminal
    if IS_OSX and want_alacritty:
        config['terminal_app'] = config.get('terminal_app', 'alacritty')
        if yesno(
            'alacritty_ctrl_h_glitch',
            'Are you experiencing the Alacritty CMD+H glitch when it is launched via terminal launcher?',
        ):
            config['alacritty_path'] = '/Applications/Alacritty.app/Contents/MacOS/alacritty'
        elif install_alacritty_homebrew and os.path.exists('/opt/homebrew/bin'):
            config['alacritty_path'] = config.get('alacritty_path', '/opt/homebrew/bin/alacritty')

    winwincfg.parent.mkdir(exist_ok=True)
    winwincfg.write_text(json.dumps(config, indent=2, sort_keys=True))


@section(enabled=allow_installing_stuff)
def install_winwin_shortcuts():
    if not IS_OSX:
        # FIXME: get this working under Ubuntu as well
        return

    q = 'Install macOS system terminal shortcuts (requires Alacritty)?'
    if not yesno('want_winwin_shortcuts', q):
        return

    # we need to install winwin package or the launcher won't be able to find
    # the libs
    venv_exec(WINWIN_VENV + '/bin/pip', ['pip', 'install', '-e', HERE + '/winwin.git'])

    # XXX: for some reason on later versions of macOS I had to also install
    # winwin into this python/pip as well as this was the only one available to
    # the automation tool
    if False and IS_OSX and haveexecutable('/usr/bin/pip3'):
        execute(['/usr/bin/pip3', 'install', '--user', '-e', '.'], cwd=HERE + '/winwin.git')

    import shutil
    from tempfile import TemporaryDirectory

    def _replace_wildcards_recursive(target, name, command):
        # skip symlinks
        if os.path.islink(target):
            return

        # perform wildcard replacement in ordinary files
        if os.path.isfile(target):
            if target.endswith('.template'):
                dest = target[:-9]
                with open(target, 'rb') as fp_read, open(dest, 'xb') as fp_dest:
                    contents = fp_read.read()
                    contents = contents.replace(b'[[[WORKFLOW_NAME]]]', name.encode('utf-8'))
                    contents = contents.replace(b'[[[WORKFLOW_COMMAND]]]', command.encode('utf-8'))
                    fp_dest.write(contents)
                os.unlink(target)
            return

        for child in os.listdir(target):
            if child.startswith('.'):
                continue

            _replace_wildcards_recursive(target + '/' + child, name, command)

    def _install_macos_workflow_service(name, command):
        with TemporaryDirectory() as tmpdir:
            tmp_workflow = '{}/{}.workflow'.format(tmpdir, name)
            shutil.copytree('{}/macos_automation/Template.workflow'.format(HERE), tmp_workflow)
            _replace_wildcards_recursive(tmp_workflow, name, command)

            # remove existing service
            dest_workflow = '{}/Library/Services/{}.workflow'.format(HOME, name)
            if os.path.exists(dest_workflow):
                shutil.rmtree(dest_workflow)
            shutil.copytree(tmp_workflow, dest_workflow)

    todo_launcher_data = {
        'key_equivalent': '@^$t',
        'presentation_modes': {'ContextMenu': '1', 'ServicesMenu': '1', 'TouchBar': '1'},
    }
    todo_launcher_key = '(null) - TODO Launcher QA - runWorkflowAsService'
    _install_macos_workflow_service(
        'TODO Launcher QA',
        # we use '/bin/bash -i ...' here because otherwise the Quick Action
        # will launch in non-interactive mode, causing it to skip ~/.bashrc and
        # so on, and then tmux won't load correctly because $PATH isn't set up,
        # and other Bad Things
        "/bin/bash -i -c '{}/bin/macos-launch-todos'".format(HERE),
    )

    vanilla_launcher_key = '(null) - Terminal Launcher QA - runWorkflowAsService'
    vanilla_launcher_data = {
        'key_equivalent': '@^t',
        'presentation_modes': {'ContextMenu': '1', 'ServicesMenu': '1', 'TouchBar': '1'},
    }
    _install_macos_workflow_service(
        'Terminal Launcher QA',
        '/Applications/Alacritty.app/Contents/MacOS/alacritty',
    )

    _install_macos_workflow_service(
        'Terminal Selector QA',
        # we use '/bin/bash -i ...' here because otherwise the Quick Action
        # will launch in non-interactive mode, causing it to skip ~/.bashrc and
        # so on, and then tmux won't load correctly because $PATH isn't set up,
        # and other Bad Things
        "/bin/bash -i -c '{}/bin/macos-launch-terminal-selector'".format(HERE),
    )

    all_pbs = execute(['defaults', 'read', 'pbs'], stdout=True)[1]
    if b'NSServicesStatus' not in all_pbs:
        print("NSServicesStatus not found")
        return

    import plistlib
    from subprocess import PIPE, Popen

    raw = execute(['defaults', 'read', 'pbs', 'NSServicesStatus'], stdout=True)[1]

    p = Popen(['plutil', '-convert', 'xml1', '-', '-o', '-'], stdin=PIPE, stdout=PIPE)
    xml, stderr = p.communicate(raw, timeout=5.0)
    assert stderr is None
    assert p.returncode == 0

    # now we can read the xml using plistlib
    data = plistlib.loads(xml)

    needs_writing = False

    for key, value in (
            (todo_launcher_key, todo_launcher_data),
            (vanilla_launcher_key, vanilla_launcher_data),
    ):
        if data.get(key) != value:
            needs_writing = True
            data[key] = value

    if needs_writing:
        new_xml = plistlib.dumps(data)
        if not allowinteractive():
            return

        print("You need to set keyboard shortcuts.")
        print("Go to:")
        print("  -> System Preferences")
        print("  -> Keyboard")
        print("  -> Shortcuts")
        print("  -> Services")
        print("  -> under 'General' set keyboard shortcuts for 'XXX QA' services")
        yesno(None, "Done?")
        if yesno(None, "Attempt automated install of keyboard shortcuts?", default=False):
            # FIXME: this never worked - the keyboard shortcuts don't seem to
            # activate even if the System Preferences UI does show them there
            execute(['defaults', 'write', 'pbs', 'NSServicesStatus', new_xml.decode('utf-8')])

    # XXX: this hack is for macos where the terminal launcher shortcuts launch
    # without a proper $PATH and then don't have access to
    # /opt/homebrew/bin/tmux
    if IS_OSX:
        symlink('/opt/homebrew/bin/tmux', '~/bin/tmux')


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


@section_macos(enabled=want_full)
def brew_install():
    if haveexecutable('brew'):
        return

    if yesno('install_homebrew', 'Install Homebrew?', default=True):
        install_cmd = '/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"'
        execute(['bash', '-c', install_cmd], stdout="TTY")


@section(quick=True)
def gnuscreen():
    symlink('.screenrc')


# create ~/bin and ~/src if they don't exist yet
mkdir('~/src')
mkdir('~/bin')
mkdir('~/man')
mkdir('~/man/man1')

# TODO: need to ensure ~/man is in our $MANPATH

# TODO: need to ensure ~/bin is in our $PATH


@section(quick=True)
def pythonpath():
    """
    Add ~/dotfiles/python/ to our ~/.local/python[2/3]/site-packages dirs
    """
    pypath = "%s/python" % HERE

    # places to look for site-packages
    globs = [
        # centos / ubuntu
        '~/.local/lib/python*/site-packages',
        # OS X
        '~/Library/Python/*/lib/python/site-packages',
        # also the powerline virtualenv needs these modules
        POWERLINE_VENV + '/lib/python3.*/site-packages',
    ]

    # try each of the glob patterns and see if we find any matches
    matches = []
    for pattern in globs:
        matches.extend(glob.glob(os.path.expanduser(pattern)))
    for m in matches:
        lineinfile(os.path.join(m, 'phodge-dotfiles.pth'), pypath)
    if not len(matches):
        raise Exception("Didn't add %s anywhere" % pypath)


@section(enabled=allow_installing_stuff)
def search_tools():
    if want_silver_searcher():
        installpkg('ag',
                   yum='the_silver_searcher',
                   apt='silversearcher-ag')

    if want_ripgrep:
        yum = False
        if haveexecutable('yum') and install_fedora_copr():
            yum = 'ripgrep'
        installpkg('ripgrep', yum=yum)


# more of my favourite developer tools
@section
def tools():
    if yesno('install_universal_ctags', 'Install Universal Ctags?', want_full):
        need_installpkg(apt=('autoconf', 'g++', 'pkg-config'))
        mkdir('~/bin')
        if haveexecutable('brew'):
            # install with homebrew
            execute(['brew', 'tap', 'universal-ctags/universal-ctags'])
            execute(['brew', 'install', '--HEAD', 'universal-ctags'])
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
    elif allow_installing_stuff and yesno('install_ctags', 'Install `ctags`?', want_full):
        installpkg('ctags')
    if allow_installing_stuff and yesno('install_patch', 'Install patch?', want_full):
        installpkg('patch')

    if allow_installing_stuff and yesno('install_tidy', 'Install tidy cli tool?', want_full):
        installpkg('tidy')

    # on OSX we want to install gnu utils (brew install coreutils findutils)
    # and put /usr/local/opt/coreutils/libexec/gnubin in PATH
    if IS_OSX and haveexecutable('brew') and allow_installing_stuff:
        if yesno('brew_install_coreutils', 'Install gnu utils?', default=want_full):
            brew_list = set(execute(['brew', 'list'], stdout=True)[1].decode('utf-8').splitlines())
            install = [
                pkg
                for pkg in ('coreutils', 'findutils')
                if pkg not in brew_list
            ]
            if len(install):
                execute(['brew', 'install'] + install)


@section
def fzf_install():
    if not yesno('install_fzf', 'Install fzf?', want_full):
        return

    if haveexecutable('brew') and allow_installing_stuff:
        installpkg('fzf')
        brewpath = execute(['brew', '--prefix'], stdout=True)[1].decode('utf-8').strip()
        if brewpath == '/opt/homebrew':
            # brew puts the fzf files into versioned folders, so all we can do
            # is glob and sort (which isn't perfect because it would need to be
            # a semver-compatible sort) and pick the first one
            fzf_path = execute(
                ['bash', '-c', f'echo {brewpath}/Cellar/fzf/* | sort -r | head -n 1'],
                stdout=True,
            )[1].decode('utf-8').strip()
        else:
            # this is how it was on my old mac
            fzf_path = brewpath + '/opt/fzf'
    else:
        # do it the long way
        import os.path
        fzf_repo = os.path.expanduser('~/src/fzf.git')
        fzf_install = InstallFromSource('https://github.com/junegunn/fzf.git',
                                        fzf_repo)
        fzf_install.select_tag('0.17.3')
        fzf_install.compile_cmd([
            ['./install', '--bin'],
        ])
        fzf_install.symlink('bin/fzf', '~/bin/fzf')
        run(fzf_install)
        execute(['./install', '--bin'], cwd=fzf_repo, stdout='TTY')
        fzf_path = fzf_repo

    lineinfile('~/.bashrc', 'source {}/shell/completion.bash'.format(fzf_path))
    lineinfile('~/.bashrc', 'source {}/shell/key-bindings.bash'.format(fzf_path))

    lineinfile('~/.zshrc', 'source {}/shell/completion.zsh'.format(fzf_path))
    lineinfile('~/.zshrc', 'source {}/shell/key-bindings.zsh'.format(fzf_path))


@memoize
def want_ptpython():
    return yesno('want_any_ptpython', 'Is PTPython wanted anywhere?', False)


def _get_some_packages(theworks: bool):
    packages = [
        'jedi',
        'yapf',
        'isort',
    ]

    if wantnvim() and not use_neovim_virtualenv():
        # needed for `git rebase -i` commit comparisons in neovim
        packages.append('GitPython')

        if not install_nvim_via_snap():
            # if we want nvim then we probably need the pynvim package
            packages.append('pynvim')

    # a nice python repl
    if theworks and want_ptpython():
        packages.append('ptpython')

    # another nice python repl
    if theworks or yesno('install_ipython', 'PIP Install iPython?', True):
        packages.append('ipython')

    # a few of my macros use `q` for logging
    if theworks or yesno('install_python_q', 'PIP Install `q`?', True):
        packages.append('q')

    return packages


# TODO: PEP 668 doesn't like this, apparently we have to get rid of installing
# to --user
def mypips(venv_pip=None):
    # if we're on macos then we need to tell homely.pipinstall to use 'pip3' instead of 'pip'
    if IS_OSX:
        pips = ['pip3']
    else:
        pips = None

    # of course we probably want virtualenv!
    if venv_pip is None:
        pipinstall('virtualenv', pips=pips)

    # these packages will be installed using the virtualenv's pip, or pip2+pip3 depending on what's
    # present. They're needed for development.
    packages = _get_some_packages(theworks=want_full or venv_pip)

    trypips = ['pip3']

    for package in packages:
        if venv_pip:
            venv_exec(venv_pip, ['pip', 'install', package])
        else:
            pipinstall(package, trypips=trypips)

    # if it's a virtualenv, always just install flake8. Otherwise, we need to ask the user if
    # they want to install both
    if venv_pip:
        # TODO: stop installing flake8 everywhere now that we have
        # ~/.venv/vim-python-tools
        venv_exec(venv_pip, ['pip', 'install', 'flake8'])
    else:
        have_pip3 = haveexecutable('pip3')
        if have_pip3 and yesno('install_flake8_python3', 'Install flake8 for python3?'):
            pipinstall('flake8', ['pip3'])


@section
def pipfavourites():
    # install my favourite pip modules with --user
    if yesno('install_python_packages_to_user', 'Install python packages with --user?', recommended=False):
        mypips()

    mkdir('~/.config')

    with writefile('~/.config/dev_requirements.txt') as f:
        f.write('flake8\n')
        for p in _get_some_packages(theworks=True):
            f.write(p + '\n')


@section(quick=True, enabled=not_work_machine and yesno('install_envup', 'Install envup?', default=False))
def envup_install():
    pipinstall('libtmux', trypips=['pip3'])
    symlink('bin/envup', '~/bin/envup')
    mkdir('~/.envup')
    symlink('envup/loki.json', '~/.envup/loki.json')
    symlink('envup/p90-bg.json', '~/.envup/p90-bg.json')
    symlink('envup/p90-code.json', '~/.envup/p90-code.json')
    symlink('envup/p90-resume.json', '~/.envup/p90-resume.json')
    symlink('envup/p90-resume-bg.json', '~/.envup/p90-resume-bg.json')


@section(quick=True)
def git():
    hooksdir = HOME + '/.githooks'
    mkdir(hooksdir)

    # symlink our pre-commit hook into ~/.githooks
    symlink('git/hooks/pre-commit', '~/.githooks/pre-commit')
    symlink('git/hooks/applypatch-msg', '~/.githooks/applypatch-msg')
    symlink('git/hooks/commit-msg', '~/.githooks/commit-msg')
    symlink('git/hooks/fsmonitor-watchman', '~/.githooks/fsmonitor-watchman')
    symlink('git/hooks/p4-changelist', '~/.githooks/p4-changelist')
    symlink('git/hooks/p4-post-changelist', '~/.githooks/p4-post-changelist')
    symlink('git/hooks/p4-pre-submit', '~/.githooks/p4-pre-submit')
    symlink('git/hooks/p4-prepare-changelist', '~/.githooks/p4-prepare-changelist')
    symlink('git/hooks/post-applypatch', '~/.githooks/post-applypatch')
    symlink('git/hooks/post-checkout', '~/.githooks/post-checkout')
    symlink('git/hooks/post-commit', '~/.githooks/post-commit')
    symlink('git/hooks/post-index-change', '~/.githooks/post-index-change')
    symlink('git/hooks/post-merge', '~/.githooks/post-merge')
    symlink('git/hooks/post-receive', '~/.githooks/post-receive')
    symlink('git/hooks/post-rewrite', '~/.githooks/post-rewrite')
    symlink('git/hooks/post-update', '~/.githooks/post-update')
    symlink('git/hooks/pre-applypatch', '~/.githooks/pre-applypatch')
    symlink('git/hooks/pre-auto-gc', '~/.githooks/pre-auto-gc')
    symlink('git/hooks/pre-commit', '~/.githooks/pre-commit')
    symlink('git/hooks/pre-merge-commit', '~/.githooks/pre-merge-commit')
    symlink('git/hooks/pre-push', '~/.githooks/pre-push')
    symlink('git/hooks/pre-rebase', '~/.githooks/pre-rebase')
    symlink('git/hooks/pre-receive', '~/.githooks/pre-receive')
    symlink('git/hooks/prepare-commit-msg', '~/.githooks/prepare-commit-msg')
    symlink('git/hooks/proc-receive', '~/.githooks/proc-receive')
    symlink('git/hooks/push-to-checkout', '~/.githooks/push-to-checkout')
    symlink('git/hooks/rebase', '~/.githooks/rebase')
    symlink('git/hooks/reference-transaction', '~/.githooks/reference-transaction')
    symlink('git/hooks/sendemail-validate', '~/.githooks/sendemail-validate')
    symlink('git/hooks/update', '~/.githooks/update')

    lines = [
        # include our dotfiles git config from ~/.gitconfig
        "[include] path = %s/git/config" % HERE,
        # because git config files don't support ENV vars, we need to tell it where to find our hooks
        "[core] hooksPath = %s/.githooks" % HOME,
    ]

    if github_ssh_hack:
        lines.extend([
            '[url "git@phodge.github.com:phodge/"] insteadof = https://github.com/phodge/',
            '[url "git@phodge.github.com:phodge/"] insteadof = git@github.com:phodge/',
        ])

    blockinfile('~/.gitconfig', lines, WHERE_TOP)

    # put our standard ignore stuff into ~/.gitignore
    with open('%s/git/ignore' % HERE, 'r') as f:
        lines = [l.rstrip('\r\n') for l in f.readlines()]  # noqa: E741
        blockinfile('~/.gitignore',
                    lines,
                    "# exclude items from phodge/dotfiles",
                    "# end of items from phodge/dotfiles",
                    where=WHERE_TOP)

    gitwip = InstallFromSource('https://github.com/phodge/git-wip.git',
                               '~/src/git-wip.git')
    gitwip.symlink('bin/git-wip', '~/bin/git-wip')
    gitwip.symlink('bin/git-unwip', '~/bin/git-unwip')
    gitwip.select_branch('master')
    run(gitwip)


@section(enabled=bool(pipx_install_fn))
def pipx_install():
    pipx_install_fn()


@section(enabled=bool(pipx_install_fn))
def gitlost():
    execute(['pipx', 'install', 'git+https://github.com/phodge/git-lost.git'])


@section(enabled=want_mercurial)
def hg():
    ext = []

    if yesno('mercurial_keyring', 'Install mercurial keyring?'):
        # TODO: this things needs python-devel and openssl-devel - should we
        # provide a suggestion to install those on non-OSX OS's?
        pipinstall('mercurial_keyring', trypips=['pip2', 'pip3', 'pip'])
        ext.append('mercurial_keyring')

    if yesno('hg_strip_ext', 'Enable hg strip extension?'):
        ext.append('strip')

    # include our hg config from ~/.hgrc
    lineinfile('~/.hgrc', '%%include %s/hg/hgrc' % HERE, where=WHERE_TOP)

    # because we can't put the absolute path to our dotfiles hg/ignore file in
    # our hg/hgrc file, we have to put the config entry into the main ~/.hgrc
    # using a blockinfile()
    lines = [
        '[ui]',
        'ignore.dotfiles = {}/hg/ignore'.format(HERE),
    ]
    if ext:
        lines.append('[extensions]')
    for name in ext:
        lines.append('%s = ' % name)
    blockinfile('~/.hgrc', lines, WHERE_END)


# install nudge
@section(quick=True)
def nudge():
    symlink('nudge.git/bin/nudge', '~/bin/nudge')


@section(enabled=want_full and not_work_machine)
def legacypl():
    if yesno('install_legacypl', 'Create clone of legacy-pl?'):
        mkdir('~/playground-6')
        legacy = InstallFromSource('ssh://git@github.com/phodge/legacy-pl.git',
                                   '~/playground-6/legacy-pl.git')
        legacy.select_branch('develop')
        run(legacy)


@section(quick=True)
def ackrc():
    symlink('.ackrc')


@section(quick=True)
def yapf():
    symlink('.style.yapf')


@memoize
def wantpowerline():
    # FIXME: we can remove this helper
    return want_full


@memoize
def powerline_path():
    cmd = [POWERLINE_VENV + '/bin/python', '-c', 'import powerline; print(powerline.__file__)']
    powerline_file = execute(cmd, stdout=True)[1]
    return os.path.dirname(powerline_file.strip().decode('utf-8'))


@section(enabled=not_work_machine)
def pypirc():
    rc = HOME + '/.pypirc'
    if not yesno('write_pypirc', 'Write a .pypirc file?', want_full):
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
            execute(['vim', rc], stdout="TTY")
    execute(['chmod', '600', rc])


@section_macos(quick=True)
def osx():
    execute(['defaults', 'write', 'NSGlobalDomain', 'InitialKeyRepeat', '-int', '15'])
    # KeyRepeat < 1.0 doesn't work :-(
    execute(['defaults', 'write', 'NSGlobalDomain', 'KeyRepeat', '-float', '1.0'])
    # prevent Accessibility controls overriding key repeat rate - seems to be
    # needed for Sonoma and above?
    execute(['defaults', 'write', 'com.apple.Accessibility', 'KeyRepeatEnabled', '-int', '0'])


@section(quick=True)
def docker_utils():
    """Install google's container-diff for docker."""
    url = 'https://storage.googleapis.com/container-diff/latest/container-diff-darwin-amd64'
    dest = os.path.expanduser('~/bin/container-diff')
    download(url, dest)
    execute(['chmod', '755', dest])


@section(quick=True)
def ctags():
    ctagsdir = HOME + '/.ctags.d'
    mkdir(ctagsdir)
    for orig in glob.glob(HERE + '/ctags.d/*.ctags'):
        basename = os.path.basename(orig)
        symlink(orig, ctagsdir + '/' + basename)


@section_ubuntu(enabled=allow_installing_stuff)
def git_install():
    if not yesno('upgrade_git', 'Install latest git from ppa:git-core/ppa?', default=want_full):
        return

    for cmd in [
            ['sudo', 'apt-add-repository', '-y', 'ppa:git-core/ppa'],
            ['sudo', 'apt-get', 'update'],
            ['sudo', 'apt-get', 'install', 'git'],
    ]:
        execute(cmd, stdout="TTY")


@section_macos(enabled=allow_installing_stuff and haveexecutable('brew'))
def font_install():
    fonts = [
        'homebrew/cask-fonts/font-inconsolata',
        # this download doesn't seem to work any more
        # 'homebrew/cask-fonts/font-anonymous-pro',
    ]
    if wantpowerline():
        fonts.extend([
            'homebrew/cask-fonts/font-inconsolata-for-powerline',
            # this one seems to require `brew install svn` which I'm maybe not prepared to do
            # 'homebrew/cask-fonts/font-anonymice-powerline',
        ])
    # install some nicer fonts
    execute(['brew', 'install'] + fonts)


@section_macos(quick=True)
def iterm2_prefs():
    if yesno('use_iterm2_prefs', 'Use custom iterm2 prefs?', default=True):
        execute([
            'defaults',
            'write',
            'com.googlecode.iterm2.plist',
            'PrefsCustomFolder',
            '-string',
            HERE + '/iterm2',
        ])
        execute([
            'defaults',
            'write',
            'com.googlecode.iterm2.plist',
            'LoadPrefsFromCustomFolder',
            '-bool',
            'true',
        ])


@section_macos(enabled=haveexecutable('brew') and allow_installing_stuff)
def install_alt_tab():
    # https://github.com/lwouis/alt-tab-macos
    if not yesno('install_alt_tab', 'Install alt-tab app-switcher for MacOS?'):
        return

    execute(['brew', 'install', '--cask', 'alt-tab'])

    print("You need to open AltTab app and grant permissions for it to work")
    yesno('alt_tab_setup_done', 'Have you opened AltTab app at least once?', noprompt=False)

    # NOTE: the config file for this app is at
    # ~/Library/Preferences/com.lwouis.alt-tab-macos.plist but there doesn't
    # seem to be a way to move the file into the repo the app recreates the
    # file when it saves changes


@section(enabled=allow_installing_stuff)
def install_pyenv():
    if not yesno('want_pyenv', 'Git clone pyenv to ~/.pyenv?', default=None):
        return

    gitclone = InstallFromSource('https://github.com/pyenv/pyenv.git', '~/.pyenv')
    gitclone.select_branch('master')
    run(gitclone)

    gitclone2 = InstallFromSource('https://github.com/pyenv/pyenv-virtualenv',
                                  '~/.pyenv/plugins/pyenv-virtualenv')
    gitclone2.select_branch('master')
    run(gitclone2)

    # NOTE: on ubuntu you'll need to install libffi-dev
    if IS_UBUNTU:
        installpkg('libffi-dev', apt='libffi-dev')
        installpkg('pkgconf', apt='pkgconf')


@section(enabled=want_alacritty)
def install_alacritty():
    # write an alacritty.yml config that imports the ones from this repo
    imports = [f'{HERE}/alacritty-base.toml']

    # FIXME: add some proper MacOS detection to homely
    if IS_OSX:
        imports.append(f'{HERE}/alacritty-macos.toml')

        def _export(d: dict):
            inner = []
            for k, v in d.items():
                if isinstance(v, (str, int)):
                    safe = repr(v)
                elif isinstance(v, dict):
                    safe = _export(v)
                else:
                    raise Exception("TODO: bork")  # noqa
                inner.append(k + ' = ' + safe)
            return '{ ' + ', '.join(inner) + ' }'

        keybindings = []
        keybindings.append(dict(
            key='T',
            mods='Control|Command',
            command=dict(program='/Applications/Alacritty.app/Contents/MacOS/alacritty'),
        ))
        keybindings.append(dict(
            key='T',
            mods='Control|Command|Shift',
            command=dict(program=HERE + '/bin/macos-launch-todos'),
        ))
        keybindings.append(dict(
            key='S',
            mods='Control|Command',
            command=dict(program=HERE + '/bin/macos-launch-terminal-selector'),
        ))

        with writefile('~/.config/alacritty-keybindings.toml') as f:
            f.write('[keyboard]\n')
            f.write('bindings = [\n')
            for bind in keybindings:
                f.write('    ' + _export(bind) + ',\n')
            f.write(']\n')

        imports.append(f'{HOME}/.config/alacritty-keybindings.toml')
    elif IS_UBUNTU:
        # TODO: DOTFILES023: this version of alacritty is too old (needs to be
        # at least 0.13 so that it uses toml files for configuration)
        execute(['sudo', 'snap', 'install', '--classic', 'alacritty'], stdout="TTY")

    blockinfile(
        '~/.config/alacritty.toml',
        ['import = ['] + [f'  "{path}",' for path in imports] + [']'],
        WHERE_TOP,
    )

    if install_alacritty_homebrew:
        execute(['brew', 'install', 'alacritty'])

        # XXX:
        # There is an issue where upstream libraries used by alacritty handle
        # CMD+H and hide the alacritty window, preventing our own CMD+H key
        # binding from working. The only workaround right now is to override
        # the shortcut at OS level
        #
        # See https://github.com/alacritty/alacritty/issues/5923
        for scope in ['io.alacritty', 'org.alacritty']:
            execute([
                'defaults',
                'write',
                scope,
                'NSUserKeyEquivalents',
                '-dict-add',
                'Hide alacritty',
                '@^~$h',
            ])


def pull_submodules(filter_path):
    from homely.ui import head
    head("Pulling latest submodules under {}/".format(filter_path))

    # git a list of git submodules
    _, stdout, _ = execute(['git', 'submodule', 'status', filter_path], cwd=HERE, stdout=True)
    paths = [
        line[1:].split(' ')[1]
        for line in stdout.decode('utf-8').splitlines()
    ]
    for path in paths:
        cmd = ['git', 'submodule', 'update', '--init', '--remote', '--recursive', '--', path]
        execute(cmd, cwd=HERE)

    # then we need to follow up with a 'git submodule update --recursive' in
    # case the submodules have their own submodules that we accidentally
    # fast-forwarded
    for path in paths:
        cmd = ['git', 'submodule', 'update', '--recursive', '--', path]
        execute(cmd, cwd=HERE)

    # check whether submodules are changed
    _, stdout, _ = execute(['git', 'status', '--short', filter_path], cwd=HERE, stdout=True)
    if stdout.strip():
        execute(['git', 'add', filter_path], cwd=HERE)
        execute(['git', 'commit', '-m', 'Automated update of submodules under {}'.format(filter_path)], cwd=HERE)


@section(enabled=want_poetry, interval='4w')
def poetry_install():
    if IS_OSX:
        installpkg('poetry', brew='poetry')
        return

    if haveexecutable('poetry'):
        execute(['poetry', 'self', 'update'], stdout="TTY")
    else:
        execute(
            ['sh', '-c', 'curl -sSL https://install.python-poetry.org | python3 -'],
            stdout="TTY",
        )


@section_macos(enabled=want_full and yesno('install_fnm', 'Install fnm?'))
def install_fnm():
    """https://github.com/Schniz/fnm"""
    # NOTE: this is currently mac-os only because I don't have a quick
    # one-liner to install on Ubuntu yet
    # TODO: DOTFILES015 install on ubuntu
    installpkg('fnm', brew='fnm')

    # bash setup
    lineinfile('~/.bashrc', 'eval "$(fnm completions --shell bash)"')
    lineinfile('~/.bashrc', 'eval $(fnm env)')

    if wantzsh():
        # setup for zsh
        lineinfile('~/.zshrc', 'eval $(fnm env)  # initialise fnm')
        mkdir('~/.zsh')
        zsh_completion = execute(['fnm', 'completions', '--shell', 'zsh'], stdout=True)[1]
        with writefile('~/.zsh/_fnm') as f:
            f.write(zsh_completion.decode('utf-8'))


# note that these need to be carried out in order of dependency
include('jerjerrod/HOMELY.py')
include('powerline/HOMELY.py')
include('tmux/HOMELY.py')
include('vim/HOMELY.py')
include('shell/HOMELY.py')
include('homely_dev/HOMELY.py')
include('php/HOMELY.py')
include('ubuntu/HOMELY.py')
