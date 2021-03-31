import glob
import json
import os
import os.path
import platform
import re

from homely.general import (WHERE_END, WHERE_TOP, blockinfile, download,
                            haveexecutable, include, lineinfile, mkdir, run,
                            section, symlink, writefile)
from homely.install import InstallFromSource, installpkg
from homely.pipinstall import pipinstall
from homely.system import execute
from homely.ui import yesno
from homely._ui import allowinteractive

HOME = os.environ['HOME']
HERE = os.path.dirname(__file__)


IS_OSX = os.getenv('HOME').startswith('/Users/')


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


@memoize
def wantfull():
    return not yesno('only_config',
                     'Minimal install? (Config files only - nothing extra installed)',
                     None)


@memoize
def need_installpkg(*, apt=None, brew=None, yum=None):
    if not allowinstallingthings():
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
def allowinstallingthings():
    if not wantfull():
        return False

    return yesno(
        'allow_install',
        'Allow installing of packages using yum/apt or `sudo make install` etc?',
        None
    )


@memoize
def install_fedora_copr():
    if not allowinstallingthings():
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
    if not wantfull():
        return False
    return yesno('want_jerjerrod', 'Use jerjerrod for project monitoring?', True)


@memoize
def want_silver_searcher():
    return yesno('install_ag', 'Install ag (required for fzf)?', wantfull())


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
    return yesno('install_nvim', 'Install neovim?', wantfull())


@memoize
def install_nvim_via_apt():
    if not wantnvim():
        return False

    if not allowinstallingthings():
        return False

    if not haveexecutable('apt-get'):
        return False

    return yesno('install_nvim_package', 'Install nvim from apt?')


@memoize
def wantzsh():
    return yesno('use_zsh', 'Install zsh config?', wantfull())


@memoize
def want_unicode_fix():
    q = 'Old versions of glibc can cause render issues with GnomeTerminal>ssh>tmux>powerline. Remove Unicode chars in powerline status?'
    return yesno('want_unicode_fix', q)


@section
def install_winwin_shortcuts():
    if not wantfull():
        return

    if not allowinstallingthings():
        return

    if not haveexecutable('defaults'):
        # FIXME: get this working under Ubuntu as well
        return

    q = 'Install macOS system terminal shortcuts (requires Alacritty)?'
    if not yesno('want_winwin_shortcuts', q):
        return

    # we need to install winwin package or the launcher won't be able to find
    # the libs
    execute(['pip3', 'install', '--user', '-e', '.'], cwd=HERE + '/winwin.git')

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
                print("Wrote wildcards to {}".format(dest))
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
        '{}/bin/macos-launch-terminal-selector'.format(HERE),
    )

    all_pbs = execute(['defaults', 'read', 'pbs'], stdout=True)[1]
    if b'NSServicesStatus' not in all_pbs:
        print("NSServicesStatus not found")
        return

    from subprocess import Popen, PIPE
    import plistlib

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
        if data[key] != value:
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
def my_settings():
    try:
        from homely.install import setallowinstall
    except ImportError:
        raise Exception('setallowinstall() not importable - please upgrade homely')

    setallowinstall(allowinstallingthings())


@section
def brew_install():
    if not (IS_OSX and wantfull()):
        return

    if haveexecutable('brew'):
        return

    if yesno('install_homebrew', 'Install Homebrew?', default=True):
        install_cmd = '/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"'
        execute(['bash', '-c', install_cmd], stdout="TTY")


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
    ]
    # try each of the glob patterns and see if we find any matches
    matches = []
    for pattern in globs:
        matches.extend(glob.glob(os.path.expanduser(pattern)))
    for m in matches:
        lineinfile(os.path.join(m, 'phodge-dotfiles.pth'), pypath)
    if not len(matches):
        raise Exception("Didn't add %s anywhere" % pypath)


@section
def install_pip():
    if not allowinstallingthings():
        return
    import subprocess
    if not haveexecutable('pip2'):
        if yesno('global_pip2', 'Install pip2 systemwide?', None):
            cmd = 'curl https://bootstrap.pypa.io/get-pip.py | sudo python2'
            subprocess.check_call(cmd, shell=True)


# my favourite developer tools
@section
def tools():
    if allowinstallingthings() and yesno('install_ack', 'Install ack?', False):
        installpkg('ack', apt='ack-grep')
    if allowinstallingthings() and want_silver_searcher():
        installpkg('ag',
                   yum='the_silver_searcher',
                   apt='silversearcher-ag')
    if allowinstallingthings() and yesno('install_ripgrep', 'Install ripgrep?', True):
        yum = False
        if haveexecutable('yum') and install_fedora_copr():
            yum = 'ripgrep'
        installpkg('ripgrep', yum=yum)

    if yesno('install_with', 'Install `with` utility?', wantfull()):
        withutil = InstallFromSource('https://github.com/mchav/with',
                                     '~/src/with.git')
        withutil.symlink('with', '~/bin/with')
        withutil.select_branch('master')
        run(withutil)

    if yesno('install_universal_ctags', 'Install Universal Ctags?', wantfull()):
        need_installpkg(apt=('autoconf', 'g++'))
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
    elif allowinstallingthings() and yesno('install_ctags', 'Install `ctags`?', wantfull()):
        installpkg('ctags')
    if allowinstallingthings() and yesno('install_patch', 'Install patch?', wantfull()):
        installpkg('patch')

    if allowinstallingthings() and yesno('install_tidy', 'Install tidy cli tool?', wantfull()):
        installpkg('tidy')

    # on OSX we want to install gnu utils (brew install coreutils findutils)
    # and put /usr/local/opt/coreutils/libexec/gnubin in PATH
    if IS_OSX and haveexecutable('brew') and allowinstallingthings():
        if yesno('brew_install_coreutils', 'Install gnu utils?', default=wantfull()):
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
    if not yesno('install_fzf', 'Install fzf?', wantfull()):
        return

    if haveexecutable('brew'):
        installpkg('fzf')
        fzf_path = '/usr/local/opt/fzf'
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
    if wantzsh():
        lineinfile('~/.zshrc', 'source {}/shell/completion.zsh'.format(fzf_path))
        lineinfile('~/.zshrc', 'source {}/shell/key-bindings.zsh'.format(fzf_path))


@memoize
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

        stdout = execute([pip, '--version'], stdout=True)[1].decode('utf-8').rstrip()
        assert re.search(r' \(python \d+\.\d+\)$', stdout)
        version = stdout.rsplit(' ', 1)[1][:-1]
        path = '%s/.local/python-%s-bin' % (HOME, version)

        scripts[pip] = path
        lineinfile('~/.vimrc', "let %s = ['%s']" % (var, path), where=WHERE_END)

    return scripts


def mypipinstall(*args, **kwargs):
    return pipinstall(*args, scripts=getpippaths(), **kwargs)


def venv_exec(venv_pip, cmd, **kwargs):
    import shlex
    env = kwargs.pop('env', None)
    if env is None:
        env = os.environ
    env.pop('__PYVENV_LAUNCHER__', None)
    activate = os.path.dirname(venv_pip) + '/activate'
    cmd = ['bash', '-c', 'source {} && {}'.format(activate, " ".join(map(shlex.quote, cmd)))]
    return execute(cmd, env=env, **kwargs)


def mypips(venv_pip=None, write_dev_reqs=False):
    # of course we probably want virtualenv!
    if venv_pip is None:
        pipinstall('virtualenv')

    theworks = wantfull() or venv_pip

    # these packages will be installed using the virtualenv's pip, or pip2+pip3 depending on what's
    # present. They're needed for development.
    packages = [
        'jedi',
        'yapf',
        'isort',
        # needed for `git rebase -i` commit comparisons
        'GitPython',
    ]

    if wantnvim() and not install_nvim_via_apt():
        # if we want nvim then we probably need the pynvim package
        packages.append('pynvim')

    # a nice python repl
    if theworks or yesno('install_ptpython', 'PIP Install ptpython?', True):
        packages.append('ptpython')

    # another nice python repl
    if theworks or yesno('install_ipython', 'PIP Install iPython?', True):
        packages.append('ipython')

    # a few of my macros use `q` for logging
    if theworks or yesno('install_python_q', 'PIP Install `q`?', True):
        packages.append('q')

    if write_dev_reqs:
        assert venv_pip is None
        mkdir('~/.config')

        with writefile('~/.config/dev_requirements.txt') as f:
            f.write('flake8\n')
            for p in packages:
                f.write(p + '\n')

    for package in packages:
        if venv_pip:
            venv_exec(venv_pip, ['pip', 'install', package])
        else:
            mypipinstall(package, trypips=['pip2', 'pip3'])

    # if it's a virtualenv, always just install flake8. Otherwise, we need to ask the user if
    # they want to install both
    if venv_pip:
        venv_exec(venv_pip, ['pip', 'install', 'flake8'])
    else:
        # always install simplejson globally as we need it for other parts of our homely install
        mypipinstall('simplejson', trypips=['pip2', 'pip3'])

        have_pip3 = haveexecutable('pip3')
        if have_pip3 and yesno('install_flake8_python3', 'Install flake8 for python3?'):
            mypipinstall('flake8', ['pip3'])
        if yesno('install_flake8_python2', 'Install flake8 for python2?'):
            mypipinstall('flake8', ['pip2'])


@section
def pipfavourites():
    # install my favourite pip modules with --user
    mypips(write_dev_reqs=True)


@section
def envup_install():
    pipinstall('libtmux', trypips=['pip3'])
    symlink('bin/envup', '~/bin/envup')
    mkdir('~/.envup')
    symlink('envup/loki.json', '~/.envup/loki.json')
    symlink('envup/p90-bg.json', '~/.envup/p90-bg.json')
    symlink('envup/p90-code.json', '~/.envup/p90-code.json')
    symlink('envup/p90-resume.json', '~/.envup/p90-resume.json')
    symlink('envup/p90-resume-bg.json', '~/.envup/p90-resume-bg.json')


@section
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
    blockinfile('~/.gitconfig', lines, WHERE_TOP)

    # put our standard ignore stuff into ~/.gitignore
    with open('%s/git/ignore' % HERE, 'r') as f:
        lines = [l.rstrip('\r\n') for l in f.readlines()]
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


@section
def gitlost():
    # 1) create a clone of git-lost in ~/playground-6?
    quest = 'Create a clone of git-lost.git in ~/playground-6?'
    if wantfull() and yesno('create_git_lost_dev', quest, default=False):
        mkdir('~/playground-6')
        gitlost = InstallFromSource('ssh://git@github.com/phodge/git-lost.git',
                                    '~/playground-6/git-lost.git')
        gitlost.select_branch('master')
        run(gitlost)

    # 2) Download git-lost bin script and chuck it in ~/bin?
    if wantfull():
        dest = HOME + '/bin/git-lost'
        download('https://raw.githubusercontent.com/phodge/git-lost/master/git-lost', dest)
        os.chmod(dest, 0o755)


@section
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
def zsh_config():
    if wantzsh():
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


@memoize
def wantpowerline():
    return yesno('use_powerline', 'Use powerline for tmux/vim?', wantfull())


@memoize
def powerline_path():
    cmd = ['python3', '-c', 'import powerline; print(powerline.__file__)']
    powerline_file = execute(cmd, stdout=True)[1]
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
                execute(['vim', rc], stdout="TTY")
    execute(['chmod', '600', rc])


@section
def osx():
    if haveexecutable('defaults'):
        execute(['defaults', 'write', 'NSGlobalDomain', 'InitialKeyRepeat', '-int', '15'])
        # KeyRepeat < 1.0 doesn't work :-(
        execute(['defaults', 'write', 'NSGlobalDomain', 'KeyRepeat', '-float', '1.0'])


@section
def docker_utils():
    """Install google's container-diff for docker."""
    url = 'https://storage.googleapis.com/container-diff/latest/container-diff-darwin-amd64'
    dest = os.path.expanduser('~/bin/container-diff')
    download(url, dest)
    execute(['chmod', '755', dest])


@section
def ctags():
    ctagsdir = HOME + '/.ctags.d'
    mkdir(ctagsdir)
    for orig in glob.glob(HERE + '/ctags.d/*.ctags'):
        basename = os.path.basename(orig)
        symlink(orig, ctagsdir + '/' + basename)


@section
def git_install():
    if not haveexecutable('apt-get'):
        return

    if not allowinstallingthings():
        return

    if not yesno('upgrade_git', 'Install latest git from ppa:git-core/ppa?', default=wantfull()):
        return

    for cmd in [
            ['sudo', 'apt-add-repository', '-y', 'ppa:git-core/ppa'],
            ['sudo', 'apt-get', 'update'],
            ['sudo', 'apt-get', 'install', 'git'],
    ]:
        execute(cmd, stdout="TTY")


@section
def font_install():
    if not IS_OSX:
        return

    if not haveexecutable('brew'):
        return

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


@section
def iterm2_prefs():
    if IS_OSX and yesno('use_iterm2_prefs', 'Use custom iterm2 prefs?', default=True):
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


@section
def install_pyenv():
    if not wantfull():
        return

    if not allowinstallingthings():
        return

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
    if haveexecutable('apt-get'):
        installpkg('libffi-dev', apt='libffi-dev')
        installpkg('pkgconf', apt='pkgconf')


@section
def install_alacritty():
    if not wantfull():
        return

    if not allowinstallingthings():
        return

    if not yesno('want_alacritty', 'Install Alacritty?', default=None):
        return

    # write an alacritty.yml config that imports the ones from this repo
    lines = ['import:']
    lines.append('  - {}/alacritty-base.yml'.format(HERE))

    # FIXME: add some proper MacOS detection to homely
    if haveexecutable('defaults'):
        lines.append('  - {}/alacritty-macos.yml'.format(HERE))

    if IS_OSX:
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

        with writefile('~/.config/alacritty-keybindings.yml') as f:
            json.dump({'key_bindings': keybindings}, f, indent='  ')

        lines.append('  - {}/.config/alacritty-keybindings.yml'.format(HOME))

    blockinfile('~/.config/alacritty.yml', lines, WHERE_TOP)

    if yesno('install_alacritty_homebrew', 'Install Alacritty via Homebrew?'):
        execute(['brew', 'install', 'alacritty'])


# TODO: https://github.com/clvv/fasd


# note that these need to be carried out in order of dependency
include('jerjerrod/HOMELY.py')
include('powerline/HOMELY.py')
include('tmux/HOMELY.py')
include('vim/HOMELY.py')
include('shell/HOMELY.py')
include('homely_dev/HOMELY.py')
include('php/HOMELY.py')
include('ubuntu/HOMELY.py')
