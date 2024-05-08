import re
from pathlib import Path
from dataclasses import dataclass


KEYFILE = Path(__file__).parent / 'keys.yaml'
regex = re.compile(r"^(CTRL-)?(ALT-)?(WIN-)?(S-)?([ -~]|CR|BS|SPACE|ESC)$")


@dataclass
class Keybind:
    command: str | dict[str, str]
    key: str
    ctrl: bool
    alt: bool
    shift: bool
    win: bool


def get_tmux_key_bindings():
    import yaml

    with open(KEYFILE) as f:
        document = yaml.safe_load(f)

    if 'tmux' not in document:
        return {}

    ret = {}
    for sectionname, stuff in document['tmux'].items():
        for keycombo, command in stuff.items():
            m = regex.match(keycombo)
            if not m:
                raise Exception("Invalid keycombo for tmux: direct: %r" % keycombo)

            ctrl, alt, win, shift, key = m.groups()

            sectionbinds = ret.setdefault(sectionname, [])
            sectionbinds.append(Keybind(
                command=command,
                key=key,
                ctrl=bool(ctrl),
                alt=bool(alt),
                win=bool(win),
                shift=bool(shift),
            ))

            assert not win, "WIN- prefix not allowed for tmux keybinding %r" % keycombo

    return ret
