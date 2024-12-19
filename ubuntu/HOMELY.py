import os
from pathlib import Path

from homely.general import WHERE_END, lineinfile, mkdir, symlink, writefile
from homely.install import installpkg
from homely.system import execute
from homely.ui import yesno

from HOMELY import HERE, HOME, section_ubuntu, want_full, allow_installing_stuff
from HOMELY import get_key_combos_for_action


@section_ubuntu(enabled=allow_installing_stuff, quick=True)
def ubuntu_swap_caps_escape():
    if not yesno('ubuntu_swap_caps_escape', 'Ubuntu: Swap caps/escape using dconf-editor?'):
        return

    cmd = ['dconf', 'read', '/org/gnome/desktop/input-sources/xkb-options']
    current = execute(cmd, stdout=True)[1].strip()
    if b"'caps:swapescape'" in current:
        # already done
        return

    if current == b'' or current == b'[]' or current == b'@as []':
        new_value = "['caps:swapescape']"
    else:
        raise Exception("TODO: don't know how to modify xkb-options value")  # noqa

    execute(['dconf', 'write', '/org/gnome/desktop/input-sources/xkb-options', new_value])


def _gsettings_set(area, key, value):
    execute(['gsettings', 'set', area, key, value])


def _dconf_write(key, value):
    execute(['dconf', 'write', key, value])


@section_ubuntu(enabled=allow_installing_stuff)
def ubuntu_key_repeat_rate():
    if not yesno('ubuntu_set_repeat_rate', 'Ubuntu: Set keyboard repeat rate?', recommended=True):
        return

    _gsettings_set('org.gnome.desktop.peripherals.keyboard', 'repeat-interval', 'uint32 15')
    _gsettings_set('org.gnome.desktop.peripherals.keyboard', 'delay',           'uint32 210')


def _get_gsettings_bind(keybinds):
    if not keybinds:
        return "@as []"

    strings = []
    for k in keybinds:
        strings.append(k.gnome_key)

    return "['" + "','".join(strings) + "']"


@section_ubuntu(enabled=allow_installing_stuff)
def ubuntu_os_key_bindings():
    # see:
    #  gsettings list-recursively org.gnome.shell.keybindings
    #  gsettings list-recursively org.gnome.desktop.wm.keybindings
    #  for schema in $(gsettings list-schemas); do echo; echo $schema; gsettings list-recursively $schema; done
    #  dconf dump /
    if not yesno('ubuntu_set_os_keybindings', 'Ubuntu: Install OS keybindings (maximize windows, etc)?', recommended=True):
        return

    # TODO(DOTFILES020) these need to be implemented on MacOS also
    wmactions = {
        ('MOVE_WINDOW_NEXT_DISPLAY',  'move-to-monitor-right'),
        ('MOVE_WINDOW_PREV_DISPLAY',  'move-to-monitor-left'),
        ('TOGGLE_MAXIMIZED',          'toggle-maximized'),
        ('FORCE_MAXIMIZED',           'maximize'),
        #('TOGGLE_FULLSCREEN',         'toggle-fullscreen'),
        ('TOGGLE_FULLSCREEN',         'toggle-above'),
        ('MINIMIZE_WINDOW',           'minimize'),
        ('_RESIZE_WINDOW_LEFT_HALF',  'move-to-side-e'),
        ('_RESIZE_WINDOW_RIGHT_HALF', 'move-to-side-e'),
        ('SWITCH_TO_WORKSPACE_LEFT',  'switch-to-workspace-left'),
        ('SWITCH_TO_WORKSPACE_RIGHT',  'switch-to-workspace-right'),
    }

    gnomeshellactions = {
        ('OS_SCREENSHOT_UI',           'show-screenshot-ui'),
        ('SHOW_ALL_WORKSPACE_WINDOWS', 'toggle-overview'),
    }

    mutteractions = {
        ('RESIZE_WINDOW_LEFT_HALF',  'toggle-tiled-left'),
        ('RESIZE_WINDOW_RIGHT_HALF', 'toggle-tiled-right'),
    }

    action_paths = [
        ('org.gnome.desktop.wm.keybindings', wmactions),
        ('org.gnome.shell.keybindings',      gnomeshellactions),
        ('org.gnome.mutter.keybindings',     mutteractions),
    ]

    # do we use dconf or gsettings
    # XXX: only my work linux machine I needed to use `dconf write /org/gnome/...` instead of gsettings
    use_gsettings = False

    for gnomepath, actions in action_paths:
        for ouraction, gnomeaction in actions:
            keybinds = _get_gsettings_bind(get_key_combos_for_action('os', ouraction))
            if use_gsettings:
                _gsettings_set(gnomepath, gnomeaction, keybinds)
            else:
                dconfpath = '/' + gnomepath.replace('.', '/') + '/'
                _dconf_write(dconfpath + gnomeaction, keybinds)

    # Get rid of CTRL+Period emoji shortcut. Slack already has its own action
    # for this key combo, CTRL+Semicolon can be used instead for emoji.
    if False:
        # XXX: this appears to not work. :-(
        _gsettings_set('org.freedesktop.ibus.panel.emoji', 'hotkey', "['<Control>semicolon']")


@section_ubuntu(enabled=allow_installing_stuff)
def ubuntu_mouse_speed():
    if not yesno('ubuntu_set_mouse_speed', 'Ubuntu: Set mouse speed / acceleration?', recommended=True):
        return

    _gsettings_set('org.gnome.desktop.peripherals.mouse', 'accel-profile', 'flat')
    # XXX: this used to be "0.0" but on my new Ubuntu PC with a corded mouse
    # and dual 4K monitors that speed was waaaayyyy too slow. (This may also be
    # due to using X11 instead of Wayland on this PC)
    _gsettings_set('org.gnome.desktop.peripherals.mouse', 'speed',         '0.8')


@section_ubuntu(enabled=allow_installing_stuff, quick=True)
def ubuntu_app_switcher_current_workspace():
    if not yesno(
        'ubuntu_set_app_switcher_current_workspace',
        'Ubuntu: Set alt-tab to only use current workspace?',
    ):
        return

    execute([
        'gsettings',
        'set',
        'org.gnome.shell.app-switcher',
        'current-workspace-only',
        'true',
    ])


@section_ubuntu(enabled=allow_installing_stuff, quick=True)
def ubuntu_workspaces_on_all_monitors():
    if not yesno(
        'ubuntu_set_workspaces_all_monitors',
        'Ubuntu: Set Workspaces to use all monitors?',
    ):
        return

    execute([
        'gsettings',
        'set',
        'org.gnome.mutter',
        'workspaces-only-on-primary',
        'false',
    ])


@section_ubuntu(enabled=allow_installing_stuff)
def ubuntu_install_devilspie2():
    """
    Install devilspie2 under Ubuntu.

    devilspie2 can "pin" apps like Rhythmbox or Spotify, causing them to move across all
    desktops/workspaces. This means I don't accidentally flip to another desktop/workspace when I
    go to play some music or respond to a chat message.

    NOTE: In newer versions of Ubuntu you right-click the app title bar and
    tick "Always on visible workspace".
    """
    question = 'Install devilspie2 to manage window sticky bits (share apps across all desktops)?'
    if not yesno('want_devilspie2', question, default=False, recommended=False):
        return

    mkdir('~/.config')
    mkdir('~/.config/autostart')

    installpkg('devilspie2', apt='devilspie2', brew=None)

    symlink('devilspie2', '~/.config/devilspie2')

    with writefile('~/.config/autostart/devilspie2.desktop') as f:
        f.write("[Desktop Entry]\n")
        f.write("Type=Application\n")
        f.write("Name=devilspie2\n")
        f.write("Exec=/usr/bin/devilspie2\n")
        f.write("Comment=devilspie2 - react to gnome window events\n")
        f.write("X-GNOME-Autostart-enabled=true\n")


def _sudo(cmd, *args, **kwargs):
    return execute(['sudo'] + cmd, *args, stdout="TTY", **kwargs)


def _install_keyring(keyname: str, url: str):
    keypath = '/etc/apt/keyrings/' + keyname

    if not os.path.exists(keypath):
        _sudo(['install', '-m', '0755', '-d', '/etc/apt/keyrings'])
        curl = f'curl -fsSL {url}'
        gpg = f'gpg --dearmor -o {keypath}'
        execute(['bash', '-c', f'{curl} | sudo {gpg}'], stdout="TTY")

    _sudo(['chmod', 'a+r', keypath])


def _get_arch():
    return execute(['dpkg', '--print-architecture'], stdout=True)[1].strip().decode('utf-8')


@section_ubuntu(enabled=allow_installing_stuff and yesno('install_docker', 'Install docker?'))
def install_docker_engine():
    # Add Docker's official GPG key:
    installpkg('ca-certificates')
    installpkg('curl')
    installpkg('gnupg')

    _install_keyring('docker.gpg', 'https://download.docker.com/linux/ubuntu/gpg')

    # Add the repository to Apt sources:
    VERSION_CODENAME = execute(
        ['bash', '-c', '. /etc/os-release && echo "$VERSION_CODENAME"'],
        stdout=True,
    )[1].strip().decode('utf-8')
    arch = _get_arch()

    cfg = f"deb [arch={arch} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu {VERSION_CODENAME} stable"
    _sudo(['bash', '-c', f'echo "{cfg}" > /etc/apt/sources.list.d/docker.list'])

    # refresh package list or it won't work
    _sudo(['apt', 'update'])

    # finally - install the various docker packages
    # TODO: would be nice to have an API for installing multiple packages at once
    for pkg in [
            'docker-ce',
            'docker-ce-cli',
            'containerd.io',
            'docker-buildx-plugin',
            'docker-compose',
    ]:
        installpkg(pkg)

    USER = os.environ['USER']
    if yesno('add_USER_to_docker_group', f'Add {USER!r} to "docker" unix group?', recommended=True):
        _sudo(['usermod', '--append', '--groups', 'docker', USER])
        # XXX: the internet suggested I do this as well, but it seems to drop
        # me into a root shell when executing homely update
        # _sudo(['newgrp', 'docker'])


@section_ubuntu(enabled=allow_installing_stuff and yesno('install_github_cli', 'Install "gh" (github-cli)'))
def install_github_cli():
    def _sudo(cmd, *args, **kwargs):
        return execute(['sudo'] + cmd, *args, stdout="TTY", **kwargs)

    _install_keyring('githubcli-archive-keyring.gpg', 'https://cli.github.com/packages/githubcli-archive-keyring.gpg')

    arch = _get_arch()
    cfg = f"deb [arch={arch} signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main"
    _sudo(['bash', '-c', f'echo "{cfg}" > /etc/apt/sources.list.d/github-cli.list'])

    # finally - install the gh package
    installpkg('gh')


@section_ubuntu(enabled=want_full)
def i3_config():
    mkdir('~/.config')
    mkdir('~/.config/i3')

    i3_config_file = Path(HOME + '/.config/i3/config')
    if not i3_config_file.exists():
        i3_config_file.write_text("# set $screen1 HDMI-i\n# set $screen2 DP-0\n")

    lineinfile(str(i3_config_file), f'include {HERE}/i3/config', where=WHERE_END)
