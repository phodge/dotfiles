import re
from pathlib import Path
from dataclasses import dataclass


OLD_KEYFILE = Path(__file__).parent / 'keys.yaml'
old_regex = re.compile(r"^(CTRL-)?(ALT-)?(WIN-)?(S-)?([ -~]|CR|BS|SPACE|ESC)$")


@dataclass
class TmuxKeybind:
    command: str | dict[str, str]
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
