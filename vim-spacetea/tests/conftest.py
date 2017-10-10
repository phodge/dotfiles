import json
import pathlib
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from subprocess import check_call

import pytest


@pytest.fixture(scope="function")
def tmpdir(request):
    path = tempfile.mkdtemp()
    try:
        yield pathlib.Path(path)
    finally:
        shutil.rmtree(path)


class Project:
    def __init__(self, tmpdir):
        # make a temp dir to work with
        self._dir = tmpdir

    def setconfig(self, path, **kwargs):
        cfgfile = self._dir / '.spacetea'
        if cfgfile.exists():
            with cfgfile.open() as f:
                cfg = json.load(f)
        else:
            cfg = {}

        cfg[path] = kwargs

        with cfgfile.open('w') as f:
            json.dump(cfg, f)

    @contextmanager
    def open(self, path, *args, **kwargs):
        with (self._dir / path).open(*args, **kwargs) as f:
            yield f

    def nvim(self, args):
        runtimepath = Path(__file__).parent.parent
        logfile1 = self._dir / 'nvim.log'
        logfile2 = self._dir / 'subprocesses.log'
        cmd = [
            'nvim',
            '-u', 'NONE',
            # redirect output to logfile1 so that we have a record of any
            # errors encountered along the way
            '+redir > {}'.format(logfile1),
            # tell spacetea to send the subprocess' stderr to logfile2
            "+let g:spacetea_logfile = '{}'".format(logfile2),
            # modify 'runtimepath' so that the autoload file is found
            '+set runtimepath+=%s' % runtimepath,
            # make sure spacetea will be operating in 'blocking' mode
            '+let g:spacetea_async = 0',
            # load the spacetea plugin file
            '+source %s' % (runtimepath / 'plugin/spacetea.vim'),
        ]
        try:
            check_call(cmd + args, timeout=10)
        finally:
            with logfile1.open() as f:
                sys.stdout.write(f.read())
            with logfile2.open() as f:
                sys.stdout.write(f.read())


@pytest.fixture(scope="function")
def project(tmpdir):
    yield Project(tmpdir)
