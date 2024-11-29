import os
from pathlib import Path

from homely.general import WHERE_END, lineinfile, mkdir, symlink, writefile
from homely.install import installpkg
from homely.system import execute
from homely.ui import yesno

from HOMELY import HERE, HOME, section_ubuntu, want_full, allow_installing_stuff


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


@section_ubuntu(enabled=allow_installing_stuff)
def ubuntu_key_repeat_rate():
    if not yesno('ubuntu_set_repeat_rate', 'Ubuntu: Set keyboard repeat rate?', recommended=True):
        return

    _gsettings_set('org.gnome.desktop.peripherals.keyboard', 'repeat-interval', 'uint32 15')
    _gsettings_set('org.gnome.desktop.peripherals.keyboard', 'delay',           'uint32 210')


@section_ubuntu(enabled=allow_installing_stuff)
def ubuntu_os_key_bindings():
    # see:
    #  gsettings list-recursively org.gnome.shell.keybindings
    #  gsettings list-recursively org.gnome.desktop.wm.keybindings
    #  { for schema in $(gsettings list-schemas); do echo; echo $schema; gsettings list-recursively $schema; done; } > schemas.txt
    if not yesno('ubuntu_set_os_keybindings', 'Ubuntu: Install OS keybindings (maximize windows, etc)?', recommended=True):
        return

    _gsettings_set('org.gnome.desktop.wm.keybindings', 'toggle-fullscreen',     "['<Alt>Return']")
    _gsettings_set('org.gnome.desktop.wm.keybindings', 'toggle-maximized',      "['<Shift><Super>Down']")
    _gsettings_set('org.gnome.desktop.wm.keybindings', 'maximize',              "@as []")
    _gsettings_set('org.gnome.desktop.wm.keybindings', 'move-to-monitor-right', "['<Super>Down']")


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
    """
    question = 'Install devilspie2 to manage window sticky bits (share apps across all desktops)?'
    if not yesno('want_devilspie2', question, default=True):
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
