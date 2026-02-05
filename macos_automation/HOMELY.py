from textwrap import dedent
from HOMELY import section_macos, manual_step


@section_macos()
def macos_manual_keybindings():
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
    manual_step(
        'macos_keyboard_shortcuts_mission_control',
        'Install Mission Control keyboard shortcuts',
        dedent(
            '''
            1. Open System Settings > Keyboard > Keyboard Shortcuts > Mission Control.
            2. Change 'Mission Control' to 'CMD+Option+Up'.
            3. Change 'Mission Control -> Move Left a Space' to 'CMD+Option+Left'.
            4. Change 'Mission Control -> Move Right a Space' to 'CMD+Option+Left'.
            '''
        ),
        undoable=False,
    )
    manual_step(
        'macos_keyboard_shortcuts_window_management',
        'Install Window Management keyboard shortcuts',
        dedent(
            '''
            1. Open System Settings > Keyboard > Keyboard Shortcuts > Windows.
            2. Change 'Halves -> Tile Left Half' to 'Option+Left'.
            3. Change 'Halves -> Tile Right Half' to 'Option+Right'.
            '''
        ),
        undoable=False,
    )
