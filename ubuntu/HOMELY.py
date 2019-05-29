from homely.general import section
from homely.system import execute
from homely.ui import yesno

from HOMELY import wantfull


@section
def ubuntu_swap_caps_escape():
    if not wantfull():
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
    if not wantfull():
        return

    if not yesno('ubuntu_set_repeat_rate', 'Ubuntu: Set keyboard repeat rate?'):
        return

    new_values = [
        ('repeat-interval', 'uint32 15'),
        ('delay',           'uint32 210'),
    ]
    for key, value in new_values:
        execute(['gsettings', 'set', 'org.gnome.desktop.peripherals.keyboard', key, value])


@section
def ubuntu_app_switcher_current_workspace():
    if not wantfull():
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
