from pathlib import Path

from homely.files import lineinfile, mkdir, symlink
from homely.general import haveexecutable, run, section
from homely.install import InstallFromSource
from homely.system import execute
from homely.ui import yesno

from HOMELY import (HERE, IS_OSX, POWERLINE_VENV, WINWIN_VENV,
                    jerjerrod_addline, venv_exec, wantjerjerrod)

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


REPO_PATH = Path('~/src/jerjerrod.git').expanduser()


@section(enabled=wantjerjerrod())
def jerjerrod_clone():
    if REPO_PATH.exists():
        # attempt git-pull in the repo
        execute(['git', 'pull', '--rebase'], cwd=str(REPO_PATH))
    else:
        execute([
            'git',
            'clone',
            'https://github.com/phodge/jerjerrod.git',
            str(REPO_PATH),
        ])


@section(enabled=wantjerjerrod())
def jerjerrod_install():
    # install jerjerrod into powerline's virtualenv
    venv_exec(POWERLINE_VENV + '/bin/pip', ['pip', 'install', '-e', str(REPO_PATH)])

    # make a symlink in ~/bin
    # XXX: this is largely because on macOS, the jerjerrod package's pyproject.toml can't be
    # installed in --editable mode by the builtin python3.8 pip
    symlink(POWERLINE_VENV + '/bin/jerjerrod', '~/bin/jerjerrod')

    # also need to install jerjerrod into winwin's virtualenv
    venv_exec(WINWIN_VENV + '/bin/pip', ['pip', 'install', '-e', str(REPO_PATH)])

    # install jerjerrod libs for winwin, which is installed using /usr/bin/pip3
    # so that it has necessary permissions on later version of macOS
    if False and IS_OSX and haveexecutable('/usr/bin/pip3'):
        # XXX: this version of pip3 is too old to understand how to install in
        # --editable mode with just a pyproject.toml, so we need to just
        # install it as-is so that powerline has access to jerjerrod libs as
        # well
        execute(['/usr/bin/pip3', 'install', '--user', '.'], cwd=str(REPO_PATH))

    jerjerrod_addline('PROJECT', '~/playground-6/*.git')
    jerjerrod_addline('PROJECT', '~/src/*.git')
    jerjerrod_addline('PROJECT', '~/src/*.hg')
    jerjerrod_addline('PROJECT', HERE)
