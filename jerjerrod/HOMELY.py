from HOMELY import HERE, wantjerjerrod
from homely.general import lineinfile, mkdir, run, section
from homely.install import InstallFromSource


@section
def jerjerrod_install():
    if not wantjerjerrod():
        return

    # install from source!
    inst = InstallFromSource('https://github.com/phodge/jerjerrod.git',
                             '~/src/jerjerrod.git')
    inst.select_branch('master')
    inst.compile_cmd([
        ['pip2', 'install', '--user', '-e', '.', '--upgrade'],
        ['pip3', 'install', '--user', '-e', '.', '--upgrade'],
    ])
    run(inst)

    # track projects in ~/src
    mkdir('~/.config')
    mkdir('~/.config/jerjerrod')
    # some sensible defaults for how I like to do things
    lines = [
        'PROJECT ~/src/*.git',
        'PROJECT ~/src/*.hg',
        'PROJECT {}'.format(HERE),
    ]
    for line in lines:
        lineinfile('~/.config/jerjerrod/jerjerrod.conf', line)
