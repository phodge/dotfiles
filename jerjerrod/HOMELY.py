from homely.general import run, section
from homely.install import InstallFromSource

from HOMELY import HERE, jerjerrod_addline, wantjerjerrod


@section
def jerjerrod_install():
    if not wantjerjerrod():
        return

    # install from source!
    inst = InstallFromSource('https://github.com/phodge/jerjerrod.git',
                             '~/src/jerjerrod.git')
    inst.select_branch('master')
    inst.compile_cmd([
        # NOTE: only install jerjerrod where we've installed powerline
        ['pip3', 'install', '--user', '-e', '.'],
    ])
    run(inst)

    jerjerrod_addline('PROJECT', '~/src/*.git')
    jerjerrod_addline('PROJECT', '~/src/*.hg')
    jerjerrod_addline('PROJECT', HERE)
