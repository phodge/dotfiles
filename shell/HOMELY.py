import os
import re

import simplejson

from HOMELY import HOME, getpippaths, wantfull, wantjerjerrod
from homely.general import (WHERE_END, WHERE_TOP, blockinfile, lineinfile,
                            mkdir, section, symlink)
from homely.system import execute, haveexecutable
from homely.ui import allowinteractive, allowpull, note, warn, yesno

bash_profile = os.environ['HOME'] + '/.bash_profile'
bashrc = os.environ['HOME'] + '/.bashrc'
zshrc = os.environ['HOME'] + '/.zshrc'


def install_completions(rcfile):
    if wantjerjerrod():
        lineinfile(rcfile, 'want_click_completion jerjerrod')


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


@section
def install_fast_hg_status():

    wanted = yesno('install_fast_hg_status', 'Install fast-hg-status?', wantfull())
    if not wanted:
        return

    mkdir('~/src')
    url = 'https://bitbucket.org/seanfarley/fast-hg-prompt'
    local = HOME + '/src/fast-hg-prompt.hg'

    # if we also are using jerjerrod, make sure we don't track this repo
    if wantjerjerrod():
        lineinfile('~/.config/jerjerrod/jerjerrod.conf',
                   'FORGET %s' % local,
                   where=WHERE_END)

    if not os.path.isdir(local):
        if not allowpull():
            warn("Cloning of {} not allowed".format(url))
            return
        with note("Cloning {}".format(url)):
            execute(['hg', 'clone', '--insecure', url, local])
    elif allowpull():
        with note("Pulling changes for {}".format(url)):
            execute(['hg', 'pull', '-u', '--insecure'], cwd=local)

    # compile it now
    execute(['make'], cwd=local)

    # put symlinks to things in
    symlink("{}/fast-hg-status".format(local), '~/bin/fast-hg-status')
