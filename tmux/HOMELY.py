import sys
from homely.general import (
    section,
    haveexecutable,
    blockinfile,
    WHERE_END,
    WHERE_TOP,
    mkdir,
    run,
)
from homely.pipinstall import pipinstall
from homely.install import InstallFromSource, installpkg
from homely.ui import warn, yesnooption

from HOMELY import (
    cachedfunc, HERE, HOME, full_install, wantpowerline,
    powerline_path,
)


@cachedfunc
def _wanttmux():
    return yesnooption('install_tmux', 'Install tmux?', default=full_install)


@section
def tmux_config():
    if _wanttmux():
        # needed for tmux
        if wantpowerline():
            pipinstall('powerline-status', [3], user=True)

        tmux_plugins = yesnooption('install_tmux_plugins',
                                   'Install TPM and use tmux plugins?',
                                   default=full_install)

        if tmux_plugins:
            mkdir('~/.tmux')
            mkdir('~/.tmux/plugins')
            tpm = InstallFromSource('https://github.com/tmux-plugins/tpm',
                                    '~/.tmux/plugins/tpm')
            tpm.select_branch('master')
            run(tpm)

        # what to put in tmux config?
        wildcards = {"DOTFILES": HERE, "HOME": HOME}
        lines = []
        if wantpowerline():
            wildcards["POWERLINE"] = powerline_path()
            lines.extend([
                # always replace the daemon on startup, so that re-sourcing the
                # tmux conf always loads updated python modules
                'run-shell "powerline-daemon --replace -q"',
                'source "%(POWERLINE)s/bindings/tmux/powerline.conf"',
            ])
        if tmux_plugins:
            lines.append('source "%(DOTFILES)s/tmux/plugins.conf"')
            # FIXME: the only way to determine if TPM installed correctly is to
            # press `[PREFIX]`, `I` to do a plugin install
        lines.append('source "%(DOTFILES)s/tmux/tmux.conf"')
        lines = [l % wildcards for l in lines]
        blockinfile('~/.tmux.conf',
                    lines,
                    '# start of automated tmux config',
                    '# end of automated tmux config',
                    where=WHERE_TOP)


# install or compile tmux
@section
def tmux_install():
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
            tmux.symlink('tmux.1', '~/man/man1/tmux.1')
            run(tmux)
        else:
            try:
                # install tmux using brew or apt-get ...
                installpkg('tmux')
            except:
                print("-" * 50)
                print("Compiling `tmux` failed - do you need to install automake or gcc?")  # noqa
                print("-" * 50)
                raise

