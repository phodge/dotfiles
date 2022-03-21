from homely.general import run, section, WHERE_TOP
from homely.files import lineinfile
from homely.install import InstallFromSource
from homely.ui import yesno

from HOMELY import HERE, jerjerrod_addline, wantjerjerrod, IS_OSX


jerjerrod_clear_cache_in_shell = wantjerjerrod() and yesno(
    'jerjerrod_clear_cache_in_shell',
    'Jerjerrod: automatic cache clearing in zsh shells?',
    recommended=True,
)

jerjerrod_clear_cache_in_vim = wantjerjerrod() and yesno(
    'jerjerrod_clear_cache_in_vim',
    'Jerjerrod: automatic cache clearing in Vim using BufWritePost?',
    recommended=True,
)


@section(quick=True)
def jerjerrod_system_flags():
    """Control how zsh/vim will manage jerjerrod's cache."""
    lineinfile(
        '~/.shellrc',
        'export JERJERROD_CLEAR_CACHE_IN_SHELL='.format(
            '1' if jerjerrod_clear_cache_in_shell else ''
        ),
    )

    lineinfile(
        '~/.vim/prefs.vim',
        'let g:jerjerrod_cache_clearing = {}  " set by phodge\'s dotfiles'.format(
            '1' if jerjerrod_clear_cache_in_vim else '0'
        ),
        where=WHERE_TOP,
    )


@section
def jerjerrod_install():
    if not wantjerjerrod():
        return

    # install from source!
    inst = InstallFromSource('https://github.com/phodge/jerjerrod.git',
                             '~/src/jerjerrod.git')
    inst.select_branch('master')
    # TODO: if you uninstall jerjerrod, this won't actually reinstalll it :-(
    inst.compile_cmd([
        # NOTE: only install jerjerrod where we've installed powerline
        ['pip3', 'install', '--user', '-e', '.'],
    ])
    run(inst)

    jerjerrod_addline('PROJECT', '~/src/*.git')
    jerjerrod_addline('PROJECT', '~/src/*.hg')
    jerjerrod_addline('PROJECT', HERE)
