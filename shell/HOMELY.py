import os
import os.path
import re

import simplejson
from homely.general import (WHERE_END, WHERE_TOP, blockinfile, download,
                            lineinfile, mkdir, run, section)
from homely.install import InstallFromSource
from homely.system import execute, haveexecutable
from homely.ui import allowinteractive, note, warn, yesno

from HOMELY import (allow_installing_stuff, getpippaths, section_macos,
                    want_python2_anything, wantjerjerrod, wantzsh)

bash_profile = os.environ['HOME'] + '/.bash_profile'
bashrc = os.environ['HOME'] + '/.bashrc'
zshrc = os.environ['HOME'] + '/.zshrc'
HERE = os.path.dirname(__file__)


def install_completions(rcfile):
    lineinfile(rcfile, 'want_click_completion homely')
    if wantjerjerrod():
        lineinfile(rcfile, 'want_click_completion jerjerrod')


@section_macos(enabled=allow_installing_stuff and haveexecutable('brew'))
def bash_install():
    if not yesno('upgrade_bash', 'Upgrade bash?', default=False):
        return

    # install newer version of bash using homebrew or some other mechanism
    execute(['brew', 'install', 'bash'])

    bash_exec = '/usr/local/bin/bash'

    # how to add /usr/local/bin/bash to /etc/shells?
    for line in open('/etc/shells').readlines():
        if line.strip() == bash_exec:
            break
    else:
        # TODO: this line needs testing
        execute(
            ['sudo', 'bash', '-c', 'echo {} >> /etc/shells'.format(bash_exec)],
            stdout="TTY")

    if os.getenv('SHELL') != bash_exec:
        USER = os.getenv('USER')
        execute(['sudo', 'chpass', '-s', bash_exec, USER], stdout="TTY")


@section(quick=True)
def shellrc():
    # this is to prevent a problem where the U+26A1 lightning character would
    # take up 2 characters of display width in Alacritty>zsh on my MSFT M1 mac,
    # screwing up the LHS prompt when it was visible.
    lightning_ok = yesno(
        'alacritty_unicode_lightning_width_issues',
        'OK to use "⚡" in zsh prompt?',
        recommended=True,
    )
    symbol = '⚡' if lightning_ok else 'e'
    lineinfile(
            '~/.shellrc',
            f'ZSH_THEME_GIT_CHANGED_SYMBOL="{symbol}"',
            where=WHERE_TOP,
    )

    lineinfile('~/.shellrc',
               'source {}/init.sh'.format(HERE),
               where=WHERE_END)


@section(quick=True)
def shell_path():
    pathregex = re.compile(r'\bpython[/\-]?\d\.\d+\b', re.IGNORECASE)

    lines = []

    def _findpybin(pycmd):
        code = 'import sys, simplejson; print(simplejson.dumps(sys.path))'
        raw = execute([pycmd, '-c', code], stdout=True)[1].decode('utf-8')
        paths = simplejson.loads(raw)
        for path in paths:
            if not path.startswith(os.environ['HOME']):
                continue
            if not pathregex.search(path):
                continue
            suffix = '/lib/python/site-packages'
            if not path.endswith(suffix):
                continue
            binpath = path[0:-len(suffix)] + '/bin'
            if not os.path.exists(binpath):
                continue
            yield 'PATH_HIGH="{}:$PATH_HIGH"'.format(binpath)

    if want_python2_anything and haveexecutable('python2'):
        lines += list(_findpybin('python2'))
    if haveexecutable('python3') and haveexecutable('pip3'):
        lines += list(_findpybin('python3'))

    # if we are installing pip modules into separate bin paths, add them to our $PATH now
    pippaths = getpippaths()
    try:
        lines.append('PATH_HIGH="%s:$PATH_HIGH"' % pippaths['pip3'])
    except KeyError:
        pass
    try:
        if want_python2_anything:
            lines.append('PATH_HIGH="%s:$PATH_HIGH"' % pippaths['pip2'])
    except KeyError:
        pass

    lines.append('PATH_HIGH="$HOME/bin:$PATH_HIGH"')

    blockinfile('~/.shellrc',
                lines,
                '# start of PATH modifications',
                '# end of PATH modifications')


@section(quick=True)
def bash_config():

    def _bashprofile():
        if os.path.islink(bash_profile):
            return
        if os.path.exists(bash_profile):
            if not allowinteractive():
                warn("%s needs manual review" % bash_profile)
                return
            msg = ('Move the contents of ~/.bash_profile into other files, and'
                   ' then delete the file when you are done')
            cmd = ['vim',
                   bash_profile,
                   '+top new',
                   '+normal! I{}'.format(msg),
                   '+normal! gql',
                   ]
            execute(cmd, stdout="TTY")
        if os.path.exists(bash_profile):
            if os.stat(bash_profile).st_size > 1:
                warn("{} still contains data".format(bash_profile))
                return
            os.unlink(bash_profile)
        with note("Creating symlink {} -> {}".format(bash_profile, bashrc)):
            os.symlink(bashrc, bash_profile)

    def _bashrc():
        lineinfile('~/.bashrc', 'source $HOME/.shellrc', where=WHERE_TOP)
        install_completions('~/.bashrc')
        lineinfile('~/.bashrc', 'shell_init_done  # this line must be last', where=WHERE_END)

    with note("Turn {} into a symlink".format(bash_profile)):
        _bashprofile()

    with note("Set up {}".format(bashrc)):
        _bashrc()


@section(enabled=wantzsh())
def zsh_config():
    lineinfile('~/.zshrc', 'source $HOME/.shellrc', where=WHERE_TOP)
    install_completions('~/.zshrc')
    lineinfile('~/.zshrc', 'shell_init_done  # this line must be last', where=WHERE_END)
    antigen = InstallFromSource('https://github.com/zsh-users/antigen.git',
                                '~/src/antigen.git')
    antigen.select_tag('v2.2.3')
    run(antigen)


@section(quick=True)
def git_completion():
    # TODO: would be good to use git submodules for these so we get pinned/stable versions
    # install completion utilities for bash
    url = 'https://raw.githubusercontent.com/git/git/master/contrib/completion/git-completion.bash'
    download(url, '~/src/git-completion.bash')
    lineinfile('~/.bashrc', 'source $HOME/src/git-completion.bash', where=WHERE_END)

    # install completion utilities for zsh
    url = 'https://raw.githubusercontent.com/git/git/master/contrib/completion/git-completion.zsh'
    mkdir('~/.zsh')
    download(url, '~/.zsh/_git')
