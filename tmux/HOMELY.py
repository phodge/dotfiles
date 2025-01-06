import sys

from homely.general import (WHERE_TOP, blockinfile, mkdir, run, section,
                            writefile)
from homely.install import InstallFromSource, installpkg
from homely.system import execute, haveexecutable
from homely.ui import warn, yesno

from HOMELY import (HERE, HOME, allow_installing_stuff, need_installpkg,
                    powerline_path, want_full, wantpowerline)

want_tmux = allow_installing_stuff and yesno(
    'install_tmux',
    'Install tmux?',
    want_full,
)


@section(enabled=want_tmux)
def tmux_config():
    tmux_plugins = yesno('install_tmux_plugins',
                         'Install TPM and use tmux plugins?',
                         want_full)

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

    # add our dotfiles python folder to PYTHONPATH before restarting the powerline daemon
    #lines.append("set-environment PYTHONPATH '%(DOTFILES)s/python'")
    if tmux_plugins:
        lines.append('source "%(DOTFILES)s/tmux/plugins.conf"')
        # FIXME: the only way to determine if TPM installed correctly is to
        # press `[PREFIX]`, `I` to do a plugin install

    lines.append('source "%(DOTFILES)s/tmux/tmux.conf"')
    lines.append('source ~/.tmux/keybindings.conf')

    if wantpowerline():
        wildcards["POWERLINE"] = powerline_path()
        lines.extend([
            # always replace the daemon on startup, so that re-sourcing the
            # tmux conf always loads updated python modules
            'source "%(POWERLINE)s/bindings/tmux/powerline.conf"',
            'run-shell "powerline-daemon --replace -q"',
        ])
    lines = [l % wildcards for l in lines]  # noqa: E741
    blockinfile('~/.tmux.conf',
                lines,
                '# start of automated tmux config',
                '# end of automated tmux config',
                where=WHERE_TOP)


# install or compile tmux
@section(enabled=want_tmux)
def tmux_install():
    if yesno('own_tmux', 'Compile tmux from source?', None):
        need_installpkg(
            apt=('libevent-dev', 'ncurses-dev'),
            brew=('automake', 'libevent'),
        )
        tmux = InstallFromSource('https://github.com/tmux/tmux.git',
                                 '~/src/tmux.git')
        tmux.select_tag('3.3a')
        tmux.compile_cmd([
            # distclean will always fail if there's nothing to clean
            ['bash', '-c', 'make distclean || :'],
            # TODO: need to replace all _SYS_QUEUE_H_ with _COMPACT_QUEUE_H_ in compat/queue.h if building a version <3.5a
            # (See https://trac.macports.org/ticket/70719 and https://github.com/tmux/tmux/pull/4041/files)
            ['sh', 'autogen.sh'],
            ['./configure', '--disable-utf8proc'],
            ['make'],
        ])
        tmux.symlink('tmux', '~/bin/tmux')
        tmux.symlink('tmux.1', '~/man/man1/tmux.1')
        run(tmux)
    else:
        try:
            # install tmux using brew or apt-get ...
            installpkg('tmux')
        except Exception:
            print("-" * 50)
            print("Compiling `tmux` failed - do you need to install automake or gcc?")  # noqa
            print("-" * 50)
            raise


class TmuxCustomMode(object):
    _all = (
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        ',<.>/?:[]-_=+!@%^&*()`'
        # NOTE: these currently don't work under tmux 3
        #'{}'
    )
    # TODO: what about #'"~;
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
            line = 'bind-key -n {key} switch-client -T {table} \\; display-message "{safeprompt}"'
            yield line.format(table=self._table, key=key, safeprompt=safeprompt)

        for key in self._prefixkeys:
            line = 'bind-key {key} switch-client -T {table} \\; display-message "{safeprompt}"'
            yield line.format(table=self._table, key=key, safeprompt=safeprompt)

        for key, command in self._bindings:
            seen.add(key)
            line = 'bind-key -T {table} {key} {command} \\; switch-client -T {table} \\; display-message "{safeprompt}"'
            yield line.format(table=self._table, key=key, command=command, safeprompt=safeprompt)
        # set up bindings for any keys that haven't been seen
        for key in self._all:
            if key not in seen:
                line = 'bind-key -T {table} {key} switch-client -T {table} \\; display-message "INVALID KEY {key}! {safeprompt}"'
                yield line.format(table=self._table, key=key, safeprompt=safeprompt)
        for key in self._special:
            if key not in seen:
                line = 'bind-key -T {table} {key} switch-client -T {table} \\; display-message "INVALID KEY {key}! {safeprompt}"'
                yield line.format(table=self._table, key=key, safeprompt=safeprompt)

        yield 'bind-key -T {table} Escape display-message "Exiting ..."'.format(table=self._table)


@section(enabled=want_tmux, quick=True)
def tmux_keys():
    import re

    lines = []

    # needs to be installed for the current version of python
    # TODO: DOTFILES025: give homely a requirements.txt mechanism
    cmd = [
        'pip3.%d' % sys.version_info.minor,
        'install',
        '--user',
        'pyyaml',
    ]
    if sys.version_info.minor >= 12:
        # for 3.12+ we need the new PEP-668 override flag
        cmd.append('--break-system-packages')
    execute(cmd)

    # XXX: dirty hack to import the key bindings module
    oldpath = sys.path[:]
    sys.path.append(HERE)
    from keybindings import get_tmux_key_bindings
    sys.path = oldpath

    tmux_keys = get_tmux_key_bindings()

    if haveexecutable("reattach-to-user-namespace"):
        tmux_copy_cmd = 'copy-pipe-and-cancel "reattach-to-user-namespace pbcopy"'
    elif haveexecutable("pbcopy"):
        tmux_copy_cmd = 'copy-pipe-and-cancel "pbcopy"'
    elif True:
        # XXX: I've been having issues with Ubuntu terminal lately where it
        # can't decipher the terminal codes coming from tmux's
        # copy-selection command
        tmux_copy_cmd = 'copy-pipe-and-cancel "xsel -b -i"'
    else:
        # TODO: any reason not to use this?
        tmux_copy_cmd = 'copy-selection'

    sections = [
        ('direct', 'bind-key -n {key} {binding}'),
        ('prefixed', 'bind-key {key} {binding}'),
        ('copy-mode-vi', 'bind-key -T copy-mode-vi {key} send-keys -X {binding}'),
    ]

    for sectionname, template in sections:
        for binding in tmux_keys.get(sectionname, {}):
            if hasattr(binding.command, 'keys'):  # is it a dict?
                if 'special' in binding.command:
                    assert binding.command['special'] == 'tmux_copy_cmd'
                    use_binding = tmux_copy_cmd
                else:
                    raise Exception("Invalid binding %r" % binding)
            else:
                use_binding = binding.command

            if binding.key == "CR":
                bindwhat = "Enter"
            elif binding.key == "ESC":
                bindwhat = "Escape"
            elif binding.key == "SPACE":
                bindwhat = "Space"
            else:
                assert not binding.key.islower(), f"Lowercase keycombo {binding.key!r} is not allowed"
                bindwhat = binding.key.lower()

            modifiers = ''
            assert not binding.win
            if binding.ctrl:
                modifiers += 'C-'
            if binding.alt:
                modifiers += 'M-'
            if binding.shift:
                # XXX: this means you can't bind SHIFT+Escape etc
                assert bindwhat.islower(), f"Invalid keycombo {bindwhat!r}"
                bindwhat = bindwhat.upper()
            lines.append(template.format(key=modifiers + bindwhat, binding=use_binding))

    # we also want to make our special PANE mode
    pm = TmuxCustomMode(
        'panemode',
        "PANEMODE: Move between panes using h, j, k, l. Resize panes using H, J, K, L")
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

    with writefile('~/.tmux/keybindings.conf') as f:
        for line in lines:
            f.write(line)
            f.write("\n")
