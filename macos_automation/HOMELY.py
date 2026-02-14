from textwrap import dedent
from homely.ui import yesno
from homely.general import haveexecutable
from homely.system import execute
from HOMELY import section_macos, manual_step, allow_installing_stuff


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


@section_macos(enabled=allow_installing_stuff)
def macos_better_touch_tool():
    new_bindings = _get_macos_keybindings()
    open_terminal_key = new_bindings["OPEN_TERMINAL"][0].macos_human_readable
    toggle_maximize_key = new_bindings["TOGGLE_MAXIMIZED"][0].macos_human_readable

    manual_step(
        'macos_better_touch_tool_install',
        'Install and configure Better Touch Tool',
        dedent(
            '''
            1. Download and install BTT v5.139 from https://folivora.ai/releases/btt5.139-2025012805.zip
            2. Open BTT and grant screen-recording and accessibility
               permissions in System Preferences.
            3. Configure BTT:
               A) Launch BTT on startup
               B) Disable automatic update checking (until we get a new license?)
               C) Disable window snapping
            '''
        ),
        undoable=True,
    )
    manual_step(
        'macos_btt_shortcut_open_terminal',
        'Add a Better Touch Tool shortcut for OPEN_TERMINAL',
        dedent(
            f'''
            1. Open BTT Configuration
            2. Add a Keyboard Shortcut
               Key sequence: {open_terminal_key}
               Actions:
               i) Send Shortcut to a Specific App: Alacritty
                  Shortcut: {open_terminal_key}
               ii) 'open application': Alacritty
            '''
        ),
        undoable=True,
    )

    simple_btt_keys = [
        ("FORCE_MAXIMIZED", "Maximize window"),
        ("MOVE_WINDOW_NEXT_DISPLAY", "Center Window on Next Monitor"),
        ("SWITCH_TO_WORKSPACE_LEFT", "Move Left a Space"),
        ("SWITCH_TO_WORKSPACE_RIGHT", "Move Right a Space"),
    ]

    for keyname, btt_action in simple_btt_keys:
        keysequence = new_bindings[keyname][0].macos_human_readable
        manual_step(
            f'macos_btt_shortcut_{keyname}',
            f'Add a Better Touch Tool shortcut for {keyname}',
            dedent(
                f'''
                1. Open BTT Configuration
                2. Add a Keyboard Shortcut
                   Key sequence: {keysequence}
                   Action: {btt_action}
                '''
            ),
            undoable=True,
        )

    manual_step(
        'macos_btt_shortcut_maximize_window',
        'Add a Better Touch Tool shortcut for FORCE_MAXIMIZED',
        dedent(
            f'''
            1. Open BTT Configuration
            2. Add a Keyboard Shortcut
               Key sequence: {force_maximize_key}
               Action: Maximize Window
            4. Add a Keyboard Shortcut
               Key sequence: ????
               Action: Navigating Spaces ... > Move Window One Space/Desktop Left
            '''
        ),
        undoable=True,
    )


@section_macos(enabled=haveexecutable('brew') and allow_installing_stuff)
def macos_alt_tab_util():
    # https://github.com/lwouis/alt-tab-macos
    if not yesno(
        "install_alt_tab",
        "Do you want to install Alt-Tab for enhanced app-switching UI in macOS?",
    ):
        return

    execute(['brew', 'install', '--cask', 'alt-tab'])

    # NOTE: the config file for this app is at
    # ~/Library/Preferences/com.lwouis.alt-tab-macos.plist but there doesn't
    # seem to be a way to move the file into the repo the app recreates the
    # file when it saves changes. We can at least try to copy the repo file
    # into ~/Library/Preferences/?
    manual_step(
        'macos_alt_tab_plist_file',
        'Copy com.lwouis.alt-tab-macos.plist into ~/Library/Preferences/',
        '1. Maually copy com.lwouis.alt-tab-macos.plist to ~/Library/Preferences/',
        undoable=False,
    )

    manual_step(
        'macos_alt_tab_system_permissions',
        'Grant system permissions for Alt-Tab utility',
        '1. Open AltTab and grant permissions for it to work.',
        undoable=False,
    )
    manual_step(
        'macos_alt_tab_configuration',
        'Manually configure Alt-Tab utility',
        dedent(
            '''
            Open Alt-Tab preferences and configure the following:
            1. General
               A) Start at login ON
               B) Menubar icon to be the colourful one
            2. Controls
               A) Shortcut 1
                  i)   Trigger shortcut: CMD+Tab
                  ii)  Show windows from spaces: Visible spaces
               B) Shortcut 2
                  i)  Trigger shortcut: CMD+Tilde
                  ii) Show windows from spaces: Visible spaces
            3. Appearance
               A) Appearance: Thumbnails
               B) Size: Small
               C) Theme: System
               D) Customize Thumbnails style:
                  i)   Hide Space number labels ON
                  ii)  Preview selected window ON
                  iii) Align Windows: Leading
               E) Show on: Screen including menu bar
               F) Animations:
                  i) Apparition delay of Switcher: 0ms
            4. Blacklists
               A) com.apple.finder: Hide in Alt Tab when no open window
            '''
        ),
        undoable=False,
    )
