from os import environ
from os.path import exists, join

from homely.files import symlink
from homely.general import mkdir, section
from homely.system import execute
from homely.ui import yesno

from HOMELY import (jerjerrod_addline, mypips, want_full,
                    want_python2_anything, wantjerjerrod)


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

    # create a python2 virtualenv as well
    want_py2_venv = want_python2_anything and yesno(
        'create_homely_venv_py2',
        'Create a python2 virtualenv for homely?',
        recommended=False,
    )
    if want_py2_venv:
        py2venv = join(venv, 'py2venv')
        if not exists(join(py2venv, 'bin')):
            execute(['virtualenv', '--python=python2.7', py2venv], stdout="TTY")
        # create a symlink to the git repo
        symlink(checkout, join(py2venv, 'homely.git'))

    # need to install editable version of homely.git in both virtualenvs
    venv_pip = venv + '/bin/pip'

    pips = [venv_pip]
    if want_py2_venv:
        pips.append(py2venv + '/bin/pip')

    for pip in pips:
        execute([pip, 'install', '--editable', checkout])
        mypips(pip)
        execute([pip, 'install', 'pytest'])

    # install build/packaging tools just in the python3 version
    execute([venv_pip, 'install', 'Sphinx', 'sphinx-autobuild', 'twine'])

    if wantjerjerrod():
        # register the playground with jerjerrod
        jerjerrod_addline('WORKSPACE', venv, ignore=["py2venv"])

    execute([venv_pip, 'install', 'Sphinx', 'sphinx-autobuild', 'pytest', 'twine'])

    # we may want to install pandoc to make the slides, but
    if yesno('homley_want_pandoc', 'Install pandoc to create slides?', recommended=True):
        from homely.install import installpkg
        installpkg('pandoc')
