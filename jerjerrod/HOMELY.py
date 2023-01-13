from pathlib import Path

from homely.files import lineinfile, mkdir, symlink
from homely.general import haveexecutable, run, section
from homely.install import InstallFromSource
from homely.system import execute
from homely.ui import yesno

from HOMELY import HERE, IS_OSX, jerjerrod_addline, wantjerjerrod

# TODO: this could be moved to mydots-configure
jerjerrod_clear_cache_in_shell = wantjerjerrod() and yesno(
    'jerjerrod_clear_cache_in_shell',
    'Jerjerrod: automatic cache clearing in zsh shells?',
    recommended=True,
)


@section(quick=True)
def jerjerrod_system_flags():
    """Control how zsh/vim will manage jerjerrod's cache."""
    lineinfile(
        '~/.shellrc',
        'export JERJERROD_CLEAR_CACHE_IN_SHELL={}'.format(
            '1' if jerjerrod_clear_cache_in_shell else ''
        ),
    )


VENV_PATH = Path('~/playground-6/virtualenvs/jerjerrod.venv').expanduser()


@section(enabled=wantjerjerrod(), interval='4w')
def jerjerrod_virtualenv_upgrade():
    if VENV_PATH.exists():
        execute(
            ['python3', '-m', 'venv', '--upgrade-deps', str(VENV_PATH)]
        )


@section(enabled=wantjerjerrod())
def jerjerrod_install():
    # create a virtualenv for jerjerrod
    mkdir(str(VENV_PATH.parent.parent))
    mkdir(str(VENV_PATH.parent))
    if not VENV_PATH.exists():
        # create the virtualenv
        execute(
            ['python3', '-m', 'venv', '--upgrade-deps', str(VENV_PATH)]
        )

    # create a symlink of jerjerrod to the virtualenv
    symlink(str(VENV_PATH / 'bin/jerjerrod'), '~/bin/jerjerrod')

    # NOTE: only install jerjerrod where we've installed powerline
    install_commands = [
        [str(VENV_PATH / 'bin/pip'), 'install', '-e', '.'],
    ]

    if IS_OSX and haveexecutable('/usr/bin/pip3'):
        # XXX: this version of pip3 is too old to understand how to install in
        # --editable mode with just a pyproject.toml, so we need to just
        # install it as-is so that powerline has access to jerjerrod libs as
        # well
        install_commands.append(
            ['/usr/bin/pip3', 'install', '--user', '.'],
        )

    # install from source!
    inst = InstallFromSource('https://github.com/phodge/jerjerrod.git',
                             '~/playground-6/jerjerrod.git')
    inst.select_branch('master')
    # TODO: if you uninstall jerjerrod, this won't actually reinstalll it :-(
    inst.compile_cmd(install_commands)
    run(inst)

    jerjerrod_addline('PROJECT', '~/playground-6/*.git')
    jerjerrod_addline('PROJECT', '~/src/*.git')
    jerjerrod_addline('PROJECT', '~/src/*.hg')
    jerjerrod_addline('PROJECT', HERE)
