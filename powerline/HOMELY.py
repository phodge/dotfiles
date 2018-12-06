import os

from homely.general import WHERE_END, blockinfile, mkdir, section, writefile
from homely.system import execute, haveexecutable
from homely.ui import yesno

from HOMELY import (HERE, HOME, allowinstallingthings, mypipinstall,
                    powerline_path, want_unicode_fix, wantjerjerrod,
                    wantpowerline)


@section
def powerline():
    if not wantpowerline():
        return

    mypipinstall('powerline-status', ['pip3'])

    mkdir('~/.config')
    mkdir('~/.config/powerline')
    paths = [
        "%s/config_files" % powerline_path(),
        "%s/powerline" % HERE,
        "%s/.config/powerline" % HOME,
    ]

    if not haveexecutable('brew') and allowinstallingthings():
        msg = 'Install fonts-powerline package for this OS? (Works on Ubuntu)'
        if yesno('powerline_fonts', msg, False, noprompt=False):
            execute(['sudo', 'apt-get', 'install', 'fonts-powerline'], stdout="TTY")

    lines = [
        'export POWERLINE_CONFIG_PATHS=%s' % ":".join(paths),
    ]
    if want_unicode_fix():
        lines.append('export HOMELY_POWERLINE_HOUSE=H')

    blockinfile(
        '~/.shellrc',
        lines,
        WHERE_END
    )

    # ask the user what colour prefs they would like and put it in
    # ~/.config/powerline/colors.sh
    colourfile = os.path.join(HOME, '.config', 'powerline', 'colours.sh')
    load = False
    defaults = dict(
        bg="gray1",
        fg1="white",
        fg2="gray6",
    )
    if not os.path.exists(colourfile):
        if yesno(None, 'Select base colours now?', True, noprompt=False):
            # load available colours from colors.json
            with open("%s/config_files/colors.json" % powerline_path()) as f:
                import simplejson
                colors = simplejson.load(f)
            with open(colourfile, 'w') as f:
                f.write("# Set the 3 variables using colour names from below.\n")
                f.write("# WARNING! If you misspell a colour your powerline may not work!\n")
                f.write("#\n")
                f.write("# primary background colour\n")
                f.write("bg=%(bg)s\n" % defaults)
                f.write("# foreground colour for highlighted tab\n")
                f.write("fg1=%(fg1)s\n" % defaults)
                f.write("# foreground colour for other tabs\n")
                f.write("fg2=%(fg2)s\n" % defaults)
                f.write("# possible colours:\n")
                for name in sorted(colors.get("colors", {})):
                    f.write("#   %s\n" % name)
            execute(['vim', colourfile], stdout="TTY")
            load = True
    else:
        load = True
        if yesno(None, 'Select base colours now?', False, noprompt=False):
            execute(['vim', colourfile], stdout="TTY")

    colourset = defaults
    if load:
        with open(colourfile, 'r') as f:
            for line in [l.rstrip() for l in f]:
                if len(line) and not line.startswith('#'):
                    import pprint
                    print('line = ' + pprint.pformat(line))  # noqa TODO
                    name, val = line.split('=')
                    colourset[name] = val
    data = {}
    data["groups"] = {
        "window:current":       {"bg": colourset["bg"],  "fg": colourset["fg1"], "attrs": []},
        "window_name":          {"bg": colourset["bg"],  "fg": colourset["fg1"], "attrs": ["bold"]},  # noqa
        "session:prefix":       {"bg": colourset["bg"],  "fg": "gray90", "attrs": ["bold"]},
        "active_window_status": {"fg": colourset["fg2"], "bg": "gray0", "attrs": []},
        "hostname":             {"bg": colourset["bg"],  "fg": "gray90", "attrs": []},
    }
    # write out a colorscheme override for tmux using our powerline colours
    mkdir('~/.config')
    mkdir('~/.config/powerline')
    mkdir('~/.config/powerline/colorschemes')
    mkdir('~/.config/powerline/colorschemes/tmux')
    import simplejson
    dumped = simplejson.dumps(data)
    with writefile('~/.config/powerline/colorschemes/tmux/default.json') as f:
        f.write(dumped)


@section
def powerline_theme():
    if not wantpowerline():
        return

    right = [
        {"function": "todonext.powerline.firstitem"},
    ]

    if haveexecutable('jerjerrod') and wantjerjerrod():
        wsnames = "jerjerrod.powerline.wsnames"
        right += [
            {"function": "jerjerrod.powerline.wsscancount"},
            {"function": wsnames, "args": {"category": "JERJERROD:CHANGED"}},
            {"function": wsnames, "args": {"category": "JERJERROD:UNTRACKED"}},
            {"function": wsnames, "args": {"category": "JERJERROD:UNPUSHED"}},
            {"function": wsnames, "args": {"category": "JERJERROD:UNKNOWN"}},
        ]

    right.append({
        "function": "homely.powerline.shortstatus",
        "args": {
            "autoupdate": True,
            "reattach_to_user_namespace": haveexecutable('reattach-to-user-namespace'),
            "colors": {
                "paused": "HOMELY:PAUSED",
                "running": "HOMELY:RUNNING",
                "failed": "HOMELY:FAILED",
                "noconn": "HOMELY:NOCONN",
                "dirty": "HOMELY:DIRTY",
                "never": "HOMELY:NEVER",
                "ok": "HOMELY:OK",
            }
        },
    })
    right.append({
        "function": "powerline.segments.common.time.date",
        "name": "time",
        "args": {
            "format": "%H:%M",
            "istime": True,
        },
    })
    right.append({"function": "powerline.segments.common.net.hostname"})

    config = {"segments": {"right": right}}
    if want_unicode_fix():
        config["segment_data"] = {"time": {"before": ""}}

    import simplejson
    dumped = simplejson.dumps(config)
    mkdir('~/.config')
    mkdir('~/.config/powerline')
    mkdir('~/.config/powerline/themes')
    mkdir('~/.config/powerline/themes/tmux')
    with writefile('~/.config/powerline/themes/tmux/default.json') as f:
        f.write(dumped)
