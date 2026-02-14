from textwrap import dedent
from HOMELY import section_macos, manual_step


def _get_macos_keybindings():
    from keybindings import get_new_bindings
    return get_new_bindings()["os"]


@section_macos()
def macos_system_keyboard_setup():
    manual_step(
        'macos_keyboard_function_keys_as_function_keys',
        'Configure F1, F2 as function keys by default',
        dedent(
            '''
            1. Open System Settings > Keyboard > Keyboard Shortcuts > Function Keys.
            2. Turn on 'Use F1, F2, etc. keys as standard function keys.
            '''
        ),
        undoable=False,
    )
    manual_step(
        'macos_keyboard_modifier_keys_for_external_keyboard',
        'Configure Modifier Keys for external keyboard',
        dedent(
            '''
            1. Ensure external keyboard is connected.
            2. Open System Settings > Keyboard > Keyboard Shortcuts > Modifier Keys.
            3. Set Caps Lock key to Escape.
            4. Set Option key to Command.
            5. Set Command key to Option.
            '''
        ),
        undoable=False,
    )


@section_macos()
def macos_standard_keybindings():
    new_bindings = _get_macos_keybindings()

    # TODO: rather than grabbing the first keybind, it would be nice to have some validation of keys_new.yaml that
    # A) ensures required keybindings are present
    # B) prevents or at least warns when there are duplicates of the same keybinding or key combination
    mission_control_key = new_bindings["SHOW_ALL_WORKSPACE_WINDOWS"][0].macos_human_readable
    left_half_key = new_bindings["RESIZE_WINDOW_LEFT_HALF"][0].macos_human_readable
    right_half_key = new_bindings["RESIZE_WINDOW_RIGHT_HALF"][0].macos_human_readable

    manual_step(
        'macos_keyboard_shortcuts_mission_control',
        'Install Mission Control keyboard shortcuts',
        dedent(
            f'''
            1. Open System Settings > Keyboard > Keyboard Shortcuts > Mission Control.
            2. Change 'Mission Control' to '{mission_control_key}'.
            '''
        ),
        undoable=False,
    )
    manual_step(
        'macos_keyboard_shortcuts_window_management',
        'Install Window Management keyboard shortcuts',
        dedent(
            f'''
            1. Open System Settings > Keyboard > Keyboard Shortcuts > Windows.
            2. Change 'Halves -> Tile Left Half' to '{left_half_key}'.
            3. Change 'Halves -> Tile Right Half' to '{right_half_key}'.
            '''
        ),
        undoable=False,
    )
