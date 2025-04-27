import re
import textwrap
from pathlib import Path
from dataclasses import dataclass
from typing import Union


OLD_KEYFILE = Path(__file__).parent / 'keys.yaml'
NEW_KEYFILE = Path(__file__).parent / 'keys_new.yaml'


old_regex = re.compile(r"^(CTRL-)?(ALT-)?(WIN-)?(S-)?([ -~]|CR|BS|SPACE|ESC)$")


@dataclass
class TmuxKeybind:
    command: Union[str, dict[str, str]]
    key: str
    ctrl: bool
    alt: bool
    shift: bool
    win: bool


def get_tmux_key_bindings():
    """TODO: deprecate this in favour of new keymap file."""
    import yaml

    with open(OLD_KEYFILE) as f:
        document = yaml.safe_load(f)

    if 'tmux' not in document:
        return {}

    ret = {}
    for sectionname, stuff in document['tmux'].items():
        for keycombo, command in stuff.items():
            m = old_regex.match(keycombo)
            if not m:
                raise Exception("Invalid keycombo for tmux: direct: %r" % keycombo)

            ctrl, alt, win, shift, key = m.groups()

            sectionbinds = ret.setdefault(sectionname, [])
            sectionbinds.append(TmuxKeybind(
                command=command,
                key=key,
                ctrl=bool(ctrl),
                alt=bool(alt),
                win=bool(win),
                shift=bool(shift),
            ))

            assert not win, "WIN- prefix not allowed for tmux keybinding %r" % keycombo

    return ret


VALID_KEY_NAMES = set(textwrap.dedent(
    """
    Up Down Left Right
    Space Return
    Backspace
    Escape Tab
    Insert Delete
    Home End
    PageDown PageUp
    Print
    Backtick Minus Equals
    LeftBracket RightBracket
    Semicolon Quote
    Comma Period Slash Backslash
    """
).split())

GNOME_VALID_KEYS = set(textwrap.dedent(
    """
    Up Down Left Right
    Space Return
    Escape Tab
    Print
    """
).split())

GNOME_TRANSLATE_KEYS = {
    "PageDown": "Page_Down",
    "PageUp": "Page_Up",
}


@dataclass
class NewKeyCombo:
    key: str
    ctrl: bool = False
    alt: bool = False
    shift: bool = False
    win: bool = False

    @property
    def gnome_key(self) -> str:
        ret: str

        if len(self.key) == 1:
            ret = self.key
        elif re.match(r'^F\d+$', self.key):
            ret = self.key
        elif self.key in GNOME_VALID_KEYS:
            ret = self.key
        else:
            try:
                ret = GNOME_TRANSLATE_KEYS[self.key]
            except KeyError:
                raise Exception(f"TODO: how to translate key {self.key!r} for gnome?")  # noqa

        # prepend modifiers
        if self.win:
            ret = '<Super>' + ret
        if self.shift:
            ret = '<Shift>' + ret
        if self.alt:
            ret = '<Alt>' + ret
        if self.ctrl:
            ret = '<Control>' + ret

        return ret

    @classmethod
    def from_keystr(class_, keystr: str):
        prefixes = dict(
            ctrl='CTRL-',
            alt='ALT-',
            shift='S-',
            win='WIN-',
        )
        flags = {flagname: False for flagname in prefixes.keys()}

        orig = keystr
        for flagname, prefix in prefixes.items():
            if keystr.startswith(prefix):
                flags[flagname] = True
                keystr = keystr[len(prefix):]
            else:
                flags[flagname] = False

        # detect out-of-order prefixes
        for prefix in prefixes.values():
            if keystr.startswith(prefix):
                raise Exception(f"Keycombo {orig} has duplicate or out-of-order prefix {prefix!r}")

        # is the remaining text a recognised key
        if keystr in VALID_KEY_NAMES:
            key = keystr
        elif re.match(r'^F([2-9]|1\d?)$', keystr):
            # function keys
            key = keystr
        elif re.match(r'^[A-Z0-9]$', keystr):
            # letters and numbers
            key = keystr
        else:
            raise Exception(f"Unknown keystr {orig!r}")

        return class_(key=key, **flags)


_NEW_BINDINGS = None


def get_new_bindings():
    global _NEW_BINDINGS

    if _NEW_BINDINGS is None:
        _NEW_BINDINGS = _read_new_bindings()

    return _NEW_BINDINGS


def _read_new_bindings():
    import yaml

    with open(NEW_KEYFILE) as f:
        document = yaml.safe_load(f)

    keys_by_section = {}

    for section in document:
        keys_by_section[section] = _process_new_bindings(document[section])

    return keys_by_section


def _process_new_bindings(bindings) -> dict[str, list[NewKeyCombo]]:
    assert isinstance(bindings, dict)

    ret: dict[str, list[NewKeyCombo]] = {}
    for keystr, actionstr in bindings.items():
        if actionstr is None:
            continue

        ret.setdefault(actionstr, []).append(NewKeyCombo.from_keystr(keystr))

    return ret
