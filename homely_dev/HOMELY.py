from os import environ
from os.path import exists, join

from HOMELY import mypips, wantfull
from homely.general import mkdir, section
from homely.ui import system, yesno


@section
def homely_dev():
    if not wantfull():
        return

    if not yesno("create_homely_venv",
                 "Create ~/playground-homely virtualenv?", False):
        return

    venv = environ['HOME'] + '/playground-homely'

    # create container dir
    mkdir(venv)
    checkout = join(venv, 'homely.git')

    # create the virtualenv if it doesn't already exist
    if not exists(join(venv, 'bin')):
        system(['virtualenv', '--python=python3', venv], stdout="TTY")

    # check out homely.git repo if it isn't there yet
    if not exists(checkout):
        system(['git', 'clone', 'git@github.com:phodge/homely.git', checkout],
               stdout="TTY")

    # need to install editable version of homely.git
    venv_pip = venv + '/bin/pip'
    system([venv_pip, 'install', '--editable', checkout])

    mypips(venv_pip)

    system([venv_pip, 'install', 'sphinx-autobuild', 'pytest'])
