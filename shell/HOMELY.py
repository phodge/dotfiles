import os
from homely.general import section, lineinfile, blockinfile, WHERE_TOP

from HOMELY import full_install, HOME, wantjerjerrod


bash_profile = os.environ['HOME'] + '/.bash_profile'
bashrc = os.environ['HOME'] + '/.bashrc'
zshrc = os.environ['HOME'] + '/.zshrc'

lineinfile('~/.shellrc',
           'source $HOME/dotfiles/shell/init.sh',
           where=WHERE_TOP)


@section
def shell_path():
    import re
    from homely.ui import system
    from homely.general import haveexecutable
    import simplejson
    pathregex = re.compile(r'\bpython[/\-]?\d\.\d+\b', re.IGNORECASE)

    lines = []

    def _findpybin(pycmd):
        code = 'import sys, simplejson; print(simplejson.dumps(sys.path))'
        raw = system([pycmd, '-c', code], stdout=True)[1].decode('utf-8')
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
            yield 'PATH="{}:$PATH"'.format(binpath)

    if haveexecutable('python2'):
        lines += list(_findpybin('python2'))
    if haveexecutable('python3'):
        lines += list(_findpybin('python3'))

    lines.append('PATH="$HOME/bin:$PATH"')

    blockinfile('~/.shellrc',
                lines,
                '# start of PATH modifications',
                '# end of PATH modifications')


@section
def bash_config():
    from homely.ui import note, warn, isinteractive, system

    def _bashprofile():
        if os.path.islink(bash_profile):
            return
        if os.path.exists(bash_profile):
            if not isinteractive():
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
            system(cmd, stdout="TTY")
        if os.path.exists(bash_profile):
            if os.stat(bash_profile).st_size > 1:
                warn("{} still contains data".format(bash_profile))
                return
            os.unlink(bash_profile)
        with note("Creating symlink {} -> {}".format(bash_profile, bashrc)):
            os.symlink(bashrc, bash_profile)

    def _bashrc():
        lineinfile('~/.bashrc', 'source $HOME/.shellrc', where=WHERE_TOP)

    with note("Turn {} into a symlink".format(bash_profile)):
        _bashprofile()

    with note("Set up {}".format(bashrc)):
        _bashrc()


@section
def zsh_config():
    lineinfile('~/.zshrc', 'source $HOME/.shellrc', where=WHERE_TOP)


@section
def install_fast_hg_status():
    from homely.ui import yesnooption, allowpull, note, warn, system
    from homely.general import mkdir, symlink, lineinfile, WHERE_END

    wanted = yesnooption('install_fast_hg_status',
                         'Install fast-hg-status?',
                         default=full_install)
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
            system(['hg', 'clone', url, local])
    elif allowpull():
        with note("Pulling changes for {}".format(url)):
            system(['hg', 'pull', '-u'], cwd=local)

    # compile it now
    system(['make'], cwd=local)

    # put symlinks to things in
    symlink("{}/fast-hg-status".format(local), '~/bin/fast-hg-status')
