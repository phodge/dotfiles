from homely.general import section, symlink, writefile
from homely.install import installpkg
from homely.system import execute, haveexecutable
from homely.ui import yesno

from HOMELY import want_full


@section(quick=True)
def ubuntu_swap_caps_escape():
    if not want_full:
        return

    if not yesno('ubuntu_swap_caps_escape', 'Ubuntu: Swap caps/escape using dconf-editor?'):
        return

    cmd = ['dconf', 'read', '/org/gnome/desktop/input-sources/xkb-options']
    current = execute(cmd, stdout=True)[1].strip()
    if b"'caps:swapescape'" in current:
        # already done
        return

    if current == b'' or current == b'[]':
        new_value = "['caps:swapescape']"
    else:
        raise Exception("TODO: don't know how to modify xkb-options value")  # noqa

    execute(['dconf', 'write', '/org/gnome/desktop/input-sources/xkb-options', new_value])


@section
def ubuntu_key_repeat_rate():
    if not want_full:
        return

    if not yesno('ubuntu_set_repeat_rate', 'Ubuntu: Set keyboard repeat rate?'):
        return

    new_values = [
        ('repeat-interval', 'uint32 15'),
        ('delay',           'uint32 210'),
    ]
    for key, value in new_values:
        execute(['gsettings', 'set', 'org.gnome.desktop.peripherals.keyboard', key, value])


@section(quick=True)
def ubuntu_app_switcher_current_workspace():
    if not want_full:
        return

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


@section
def ubuntu_install_devilspie2():
    """
    Install devilspie2 under Ubuntu.

    devilspie2 can "pin" apps like Rhythmbox or Spotify, causing them to move across all
    desktops/workspaces. This means I don't accidentally flip to another desktop/workspace when I
    go to play some music or respond to a chat message.
    """
    if not haveexecutable('apt-get'):
        return

    if not want_full:
        return

    question = 'Install devilspie2 to manage window sticky bits?'
    if not yesno('want_devilspie2', question, default=True):
        return

    installpkg('devilspie2', apt='devilspie2', brew=None)

    symlink('devilspie2', '~/.config/devilspie2')

    with writefile('~/.config/autostart/devilspie2.desktop') as f:
        f.write("[Desktop Entry]\n")
        f.write("Type=Application\n")
        f.write("Name=devilspie2\n")
        f.write("Exec=/usr/bin/devilspie2\n")
        f.write("Comment=devilspie2 - react to gnome window events\n")
        f.write("X-GNOME-Autostart-enabled=true\n")
