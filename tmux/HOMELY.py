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


class TmuxCustomMode(object):
    _all = ('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            ',<.>/?:[{]}-_=+!@$%^&*()`~')
    # TODO: what about #'";
    _special = ['Enter', 'Left', 'Right', 'Up', 'Down', 'Space']

    def __init__(self, table, prompt):
        super(TmuxCustomMode, self).__init__()
        self._table = table
        self._prompt = prompt
        self._rootkeys = []
        self._prefixkeys = []
        self._bindings = []

    def rootkeybind(self, key):
        self._rootkeys.append(key)

    def prefixkeybind(self, key):
        self._prefixkeys.append(key)

    def bindkey(self, key, command):
        assert key != 'Escape'
        self._bindings.append((key, command))

    def getlines(self):
        safeprompt = self._prompt.replace('\\', '\\\\').replace('"', '\\"')
        seen = set()

        for key in self._rootkeys:
            seen.add(key)
            line = 'bind-key -n {key} switch-client -T {table} \; display-message "{safeprompt}"'
            yield line.format(table=self._table, key=key, safeprompt=safeprompt)

        for key in self._prefixkeys:
            line = 'bind-key {key} switch-client -T {table} \; display-message "{safeprompt}"'
            yield line.format(table=self._table, key=key, safeprompt=safeprompt)

        for key, command in self._bindings:
            seen.add(key)
            line = 'bind-key -T {table} {key} {command} \; switch-client -T {table} \; display-message "{safeprompt}"'
            yield line.format(table=self._table, key=key, command=command, safeprompt=safeprompt)
        # set up bindings for any keys that haven't been seen
        for key in self._all:
            if key not in seen:
                line = 'bind-key -T {table} {key} switch-client -T {table} \; display-message "INVALID KEY {key}! {safeprompt}"'
                yield line.format(table=self._table, key=key, safeprompt=safeprompt)
        for key in self._special:
            if key not in seen:
                line = 'bind-key -T {table} {key} switch-client -T {table} \; display-message "INVALID KEY {key}! {safeprompt}"'
                yield line.format(table=self._table, key=key, safeprompt=safeprompt)

        yield 'bind-key -T {table} Escape display-message "Exiting ..."'.format(table=self._table)


@section
def tmux_keys():
    if not _wanttmux():
        return

    import re

    lines = []

    # needs to be installed for the current version of python
    pipinstall('pyyaml', [sys.version_info.major], user=True)
    import yaml

    with open(HERE + '/keybindings/keys.yaml') as f:
        document = yaml.load(f)
    regex = re.compile(r"^(C-)?(O-)?(M-)?(S-)?([ -~]|CR|BS|SPACE|ESC)$")
    if 'tmux' in document:
        static = {}
        dynamic = {}
        if haveexecutable("reattach-to-user-namespace"):
            static['tmux_copy_cmd'] = 'copy-pipe "reattach-to-user-namespace pbcopy"'
        elif haveexecutable("pbcopy"):
            static['tmux_copy_cmd'] = 'copy-pipe "pbcopy"'
        else:
            static['tmux_copy_cmd'] = 'copy-selection'
        sections = []
        sections.append(('direct', 'bind-key -n'))
        sections.append(('prefixed', 'bind-key'))
        sections.append(('vi-copy', 'bind-key -t vi-copy'))
        for sectionname, command in sections:
            for keycombo, binding in document["tmux"].get(sectionname, {}).items():
                if hasattr(binding, 'keys'):
                    if 'static' in binding:
                        binding = static[binding['static']]
                    elif 'dynamic' in binding:
                        binding = dynamic[binding['dynamic']]()
                    else:
                        raise Exception("Invalid binding %r" % binding)
                m = regex.match(keycombo)
                if not m:
                    warn("Invalid keycombo for tmux: direct: %r" % keycombo)
                    continue
                ctrl, opt, meta, shift, key = m.groups()
                if key == "CR":
                    key = "Enter"
                elif key == "ESC":
                    key = "Escape"
                elif key == "SPACE":
                    key = "Space"
                else:
                    assert not key.islower(), "Lowercase keycombo %r is not allowed" % keycombo
                    key = key.lower()
                line = command
                line += ' '
                if ctrl:
                    line += 'C-'
                assert not opt, "O- prefix not allowed for tmux keybinding %r" % keycombo
                if meta:
                    line += 'M-'
                if shift:
                    assert key.islower(), "Invalid keycombo %r" % keycombo
                    key = key.upper()
                line += key
                line += ' '
                line += binding
                lines.append(line)

    # we also want to make our special PANE mode
    pm = TmuxCustomMode('panemode', "PANEMODE: Move between panes using h, j, k, l. Resize panes using H, J, K, L")
    pm.prefixkeybind('p')
    pm.prefixkeybind('C-p')
    pm.bindkey('h', 'select-pane -L')
    pm.bindkey('j', 'select-pane -D')
    pm.bindkey('k', 'select-pane -U')
    pm.bindkey('l', 'select-pane -R')
    pm.bindkey('H', 'resize-pane -L 2')
    pm.bindkey('J', 'resize-pane -D 2')
    pm.bindkey('K', 'resize-pane -U 2')
    pm.bindkey('L', 'resize-pane -R 2')
    lines.extend(pm.getlines())

    blockinfile('~/.tmux.conf',
                lines,
                '# start of automated tmux keybindings',
                '# end of automated tmux keybindings',
                where=WHERE_END)
