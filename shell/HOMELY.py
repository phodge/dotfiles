from homely.general import section

from HOMELY import full_install, HOME, wantjerjerrod


@section
def install_fast_hg_status():
    import os
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
