from os import environ
from os.path import exists, join

from homely.general import mkdir, section
from homely.system import execute
from homely.ui import yesno

from HOMELY import (jerjerrod_addline, mypips, venv_exec, want_full,
                    wantjerjerrod, POWERLINE_VENV)


@section(enabled=want_full)
def homely_dev():
    if not yesno("create_homely_venv",
                 "Create ~/playground-homely virtualenv?", False):
        return

    venv = environ['HOME'] + '/playground-homely'

    # create container dir
    mkdir(venv)
    checkout = join(venv, 'homely.git')

    # create the virtualenv if it doesn't already exist
    if not exists(join(venv, 'bin')):
        execute(['virtualenv', '--python=python3', venv], stdout="TTY")

    # check out homely.git repo if it isn't there yet
    if not exists(checkout):
        execute(['git', 'clone', 'git@github.com:phodge/homely.git', checkout],
                stdout="TTY")

    # need to install editable version of homely.git in both virtualenvs
    venv_pip = venv + '/bin/pip'
    venv_exec(venv_pip, ['pip', 'install', '--editable', checkout])

    # also need to install editable version into the powerline virtualenv
    venv_exec(POWERLINE_VENV + '/bin/pip', ['pip', 'install', '--editable', checkout])

    mypips(venv_pip)

    # install all dev requirements
    venv_exec(venv_pip, ['pip', 'install', '-r', join(checkout, 'requirements_dev.txt')])

    if wantjerjerrod():
        # register the playground with jerjerrod
        jerjerrod_addline('WORKSPACE', venv, ignore=["py2venv"])

    # we may want to install pandoc to make the slides, but
    if yesno('homley_want_pandoc', 'Install pandoc to create slides?', recommended=True):
        from homely.install import installpkg
        installpkg('pandoc')
