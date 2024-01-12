import argparse
import re
from pathlib import Path
from subprocess import check_output
from typing import Optional

import neovim

import git

LINE_RE = re.compile(r'^(?:\w+)\s+([0-9a-f]+)\s')


def main(bufnr: int, commitsha: str):
    nvim = neovim.attach('stdio')

    buf = nvim.buffers[bufnr]
    repo = git.Repo(buf.name, search_parent_directories=True)

    files = get_files_from_ref(repo, commitsha)

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


def hl_init(nvim):
    # link highlight groups
    nvim.command('hi! link gitrebaseSameFiles Typedef')
    nvim.command('hi! link gitrebaseCommonFiles Operator')
    nvim.command('hi! link gitrebaseCurrent Function')

    # clear highlight groups
    nvim.command('syn clear gitrebaseSameFiles')
    nvim.command('syn clear gitrebaseCommonFiles')
    nvim.command('syn clear gitrebaseCurrent')


def hl_add(nvim, group, ref):
    nvim.command('syn keyword {} {} containedin=gitrebaseCommit'.format(
        group, ref))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('bufnr', type=int)
    parser.add_argument('commitsha')
    args = parser.parse_args()
    # make a list of all files in that sha
    main(int(args.bufnr), args.commitsha)
