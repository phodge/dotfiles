import json
from functools import partial
from pathlib import Path
from subprocess import TimeoutExpired

import neovim

# jobs that are currently being run
_jobs = {}
_next_job_id = 1
_shutdown = False


class Job:
    __slots__ = ['job_id', 'proc']

    def __init__(self, proc):
        global _next_job_id
        self.job_id = _next_job_id
        _next_job_id += 1
        self.proc = proc


class InvalidConfig(Exception):
    def __init__(self, cfg_path, detail=None):
        msg = "{} is not valid".format(cfg_path)
        if detail:
            msg += ": "
            msg += detail
        super().__init__(msg)


class Config:
    def __init__(self, path, blob):
        self._path = path
        self._actions = []
        for item in blob:
            import pprint
            print('item = ' + pprint.pformat(item))  # noqa TODO
            raise Exception("TODO: what is it?")  # noqa
            self._actions.append(Action(**item))


def _descend(child, parent):
    """
    A generator that yields every Path from <child> up to its <parent>,
    inclusive.
    """
    assert str(child).startswith(str(parent))
    yield child
    while child != parent:
        child = child.parent
        yield child


def main():
    nvim = neovim.attach('stdio')

    # set up RPC hooks
    nvim.run_loop(partial(handle_request, nvim),
                  partial(handle_notification, nvim))


def handle_notification(nvim, message, args):
    if message == 'spacetea_shutdown':
        # put ourselves in `shutdown` mode so that the on-exit hooks won't try
        # to do anything
        global _shutdown
        _shutdown = True

        # - shut down all background jobs immediately
        for job in _jobs.values():
            job.proc.kill()

        # for for jobs to die. If they don't die within 2 seconds, kill them
        for job_id in list(_jobs.keys()):
            try:
                _jobs[job_id].proc.wait(2)
            except TimeoutExpired:
                _jobs[job_id].proc.kill()
            _jobs.pop(job_id)

        # we're done here
        return

    raise Exception("Unexpected RPC Notification")  # noqa


def handle_request(nvim, message, args):
    if message == 'spacetea_shutdown':
        # - shut down all background jobs immediately
        # - return some sort of background job
        raise Exception("TODO: finish this")  # noqa

    if message == 'spacetea_runcommand':
        if len(args) > 1:
            raise Exception('Invalid args for {!r}: {!r}'.format(message, args))

        arg = args[0]

        if arg == 'test':
            # TODO: test this with a buffer that points to a non-existent file
            current = Path(nvim.current.buffer.name).resolve()

            # what's the repo root?
            root = _get_root(current)

            for path in _descend(current, root):
                RunTests(path, root=root)
            return

        if arg == 'config':
            # use GetConfigPath(`pwd`) and then `:edit` that file
            raise Exception("TODO: finish this")  # noqa

        if arg.startswith('config '):
            #filename = arg[7:]
            # - use GetConfigPath(FILENAME) to get the .spacetea path
            # - add a section for FILENAME in that `.spacetea`
            # - :edit the `.spacetea`
            raise Exception("TODO: finish this")  # noqa

        raise Exception('Invalid command argument: {!r}'.format(arg))

    raise Exception('Unexpected RPC Request {!r}'.format(message))


def _get_root(startat):
    """
    Find the likely "root" of the project that owns <startat>. For now we just
    recurse up through parent directories until we find a '.git' or '.hg'
    folder. It is possible this thing will return None if it can't figure out a
    good project root.
    """
    assert isinstance(startat, Path)
    examine = startat
    while len(examine.parts) > 2:
        if (examine / '.git').exists():
            return examine
        if (examine / '.hg').exists():
            return examine
        examine = examine.parent
    return None


def RunTests(path, *, root):
    cfg_path = GetConfigPath(root)
    if not cfg_path.exists():
        GenerateFileConfig(cfg_path, path)
        cfg = {}
    else:
        cfg = LoadConfigForPath(cfg_path, path)

    for action in cfg.get_actions():
        RunAction(action, key=path)


def RunAction(action, *, key):
    raise Exception("TODO: run an action")  # noqa


def LoadConfigForPath(cfg_path, path):
    with cfg_path.open() as f:
        blob = json.load(f)

    try:
        return Config(path, blob.get(path, []))
    except AttributeError:
        raise InvalidConfig(cfg_path)


def GetConfigPath(root):
    return root / '.spacetea'


def GenerateFileConfig(cfg_path):
    raise Exception("TODO: generate an empty config file")  # noqa


def StopTestsForFile(file_or_dir):
    #- if there is already a job running for this file_or_dir, kill it
    raise Exception("TODO: stop it")  # noqa


if __name__ == '__main__':
    main()
