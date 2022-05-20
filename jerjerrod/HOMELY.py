from homely.general import run, section, haveexecutable, WHERE_TOP
from homely.files import lineinfile
from homely.install import InstallFromSource
from homely.ui import yesno

from HOMELY import HERE, jerjerrod_addline, wantjerjerrod, IS_OSX


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


@section(enabled=wantjerjerrod())
def jerjerrod_install():
    # NOTE: only install jerjerrod where we've installed powerline
    install_commands = [
        ['pip3', 'install', '--user', '-e', '.'],
    ]

    if IS_OSX and haveexecutable('/usr/bin/pip3'):
        # XXX: this version of pip3 is too old to understand how to install in
        # ---editable mode with just a pyproject.toml, so we need to just
        # install it as-is
        install_commands.append(
            ['/usr/bin/pip3', 'install', '--user', '.'],
        )

    # install from source!
    inst = InstallFromSource('https://github.com/phodge/jerjerrod.git',
                             '~/src/jerjerrod.git')
    inst.select_branch('master')
    # TODO: if you uninstall jerjerrod, this won't actually reinstalll it :-(
    inst.compile_cmd(install_commands)
    run(inst)

    jerjerrod_addline('PROJECT', '~/src/*.git')
    jerjerrod_addline('PROJECT', '~/src/*.hg')
    jerjerrod_addline('PROJECT', HERE)
