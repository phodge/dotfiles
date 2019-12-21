import os
import re

import simplejson
from homely.general import (WHERE_END, WHERE_TOP, blockinfile, lineinfile,
                            mkdir, run, section, symlink)
from homely.install import InstallFromSource
from homely.system import execute, haveexecutable
from homely.ui import allowinteractive, allowpull, note, warn, yesno

from HOMELY import (HOME, IS_OSX, allowinstallingthings, getpippaths, wantfull,
                    wantjerjerrod)

bash_profile = os.environ['HOME'] + '/.bash_profile'
bashrc = os.environ['HOME'] + '/.bashrc'
zshrc = os.environ['HOME'] + '/.zshrc'


def install_completions(rcfile):
    lineinfile(rcfile, 'want_click_completion homely')
    if wantjerjerrod():
        lineinfile(rcfile, 'want_click_completion jerjerrod')


@section
def bash_install():
    if not (IS_OSX and haveexecutable('brew')):
        return

    if not allowinstallingthings():
        return

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


@section
def shellrc():
    lineinfile('~/.shellrc',
               'source $HOME/dotfiles/shell/init.sh',
               where=WHERE_END)


@section
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

    if haveexecutable('python2'):
        lines += list(_findpybin('python2'))
    if haveexecutable('python3') and haveexecutable('pip3'):
        lines += list(_findpybin('python3'))

    # if we are installing pip modules into separate bin paths, add them to our $PATH now
    pippaths = getpippaths()
    for path in [pippaths.get("pip2"), pippaths.get("pip3")]:
        if path:
            lines.append('PATH_HIGH="%s:$PATH_HIGH"' % path)

    lines.append('PATH_HIGH="$HOME/bin:$PATH_HIGH"')

    blockinfile('~/.shellrc',
                lines,
                '# start of PATH modifications',
                '# end of PATH modifications')


@section
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


@section
def zsh_config():
    lineinfile('~/.zshrc', 'source $HOME/.shellrc', where=WHERE_TOP)
    install_completions('~/.zshrc')
    lineinfile('~/.zshrc', 'shell_init_done  # this line must be last', where=WHERE_END)
    antigen = InstallFromSource('https://github.com/zsh-users/antigen.git',
                                '~/src/antigen.git')
    antigen.select_tag('v2.2.3')
    run(antigen)
