import json
import os
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory

colourfile = Path(os.getenv('HOME')) / '.config/powerline/colours.sh'
defaults = dict(
    bg="gray1",
    fg1="white",
    fg2="gray6",
)

def get_powerline_path() -> Path:
    import powerline
    return Path(powerline.__file__).parent


def main() -> None:
    colors_json_path = get_powerline_path() / 'config_files/colors.json'

    # load available colours from colors.json
    with colors_json_path.open() as f:
        available_colors = json.load(f)

    # what colours are currently selected?
    if not colourfile.exists():
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

    with TemporaryDirectory() as tmpdir:
        with open(tmpdir + '/available.txt', 'w') as z:
            z.write("# possible colours:\n")
            for name in sorted(available_colors.get("colors", {})):
                z.write("#   %s\n" % name)

        run([
            'vim',
            colourfile,
            f'+topleft vsplit {tmpdir}/available.txt',
            '+wincmd p',
        ], check=True)

    print("NOTE: To apply changes, run this command:")
    print("  homely update --quick --nopull")


if __name__ == "__main__":
    main()
