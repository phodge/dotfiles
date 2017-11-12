import re
from pathlib import Path
from subprocess import check_output

import click
import git
from typing import Optional

import neovim

LINE_RE = re.compile(r'^(?:\w+)\s+([0-9a-f]+)\s')


@click.command()
@click.argument('bufnr')
@click.argument('commitsha')
def main(bufnr, commitsha):
    nvim = neovim.attach('stdio')

    buf = nvim.buffers[int(bufnr)]
    repo = git.Repo(buf.name, search_parent_directories=True)

    files = get_files_from_ref(repo, commitsha)
    packages = get_packages_from_files(files)

    # add highlighting for the current commit
    hl_init(nvim)
    hl_add(nvim, 'gitrebaseCurrent', commitsha)

    # get all other refs from the buffer
    refs = set()
    for line in buf:
        m = LINE_RE.match(line)
        if m:
            refs.add(m.group(1))

    for ref in refs:
        if ref != commitsha:
            otherfiles = get_files_from_ref(repo, ref)
            if otherfiles == files:
                hl_add(nvim, 'gitrebaseSameFiles', ref)
            elif otherfiles & files:
                hl_add(nvim, 'gitrebaseCommonFiles', ref)
            else:
                otherpackages = get_packages_from_files(otherfiles)
                if otherpackages & packages:
                    hl_add(nvim, 'gitrebaseCommonPackages', ref)


def get_files_from_ref(repo, ref):
    cmd = [
        'git',
        'diff-tree',
        '--no-commit-id',
        '--name-only',
        '-r',
        ref
    ]
    lines = check_output(cmd).decode('utf-8').splitlines()
    return set(lines)


def get_packages_from_files(files):
    packages = set()
    for examine in map(Path, files):
        pkg = get_package_from_path(examine)
        if pkg:
            packages.add(str(pkg))
    return packages


def get_package_from_path(examine: Path) -> Optional[Path]:
    while len(examine.parts):
        for ini in ('setup.py', 'setup.cfg', 'flit.ini'):
            if (examine / ini).exists():
                return examine
        examine = examine.parent
    return None


def hl_init(nvim):
    # link highlight groups
    nvim.command('hi! link gitrebaseSameFiles Typedef')
    nvim.command('hi! link gitrebaseCommonFiles Operator')
    nvim.command('hi! link gitrebaseCommonPackages Macro')
    nvim.command('hi! link gitrebaseCurrent Function')

    # clear highlight groups
    nvim.command('syn clear gitrebaseSameFiles')
    nvim.command('syn clear gitrebaseCommonFiles')
    nvim.command('syn clear gitrebaseCommonPackages')
    nvim.command('syn clear gitrebaseCurrent')


def hl_add(nvim, group, ref):
    nvim.command('syn keyword {} {} containedin=gitrebaseCommit'.format(
        group, ref))


if __name__ == '__main__':
    # make a list of all files in that sha
    main()
