"""
Tests for the python engine that runs in the background for Spacetea

The engine does the following jobs:
- does the logic for the :SpaceTea test command
  -  run test for the current buf

"""
from pathlib import Path


def test_SpaceTea_RunTests_touch(project):
    """
    Test that a 'touch' strategy for a file will touch a particular target
    file (i.e. create it or update its last-modified time).
    """
    # test that the RunTests function will ... what?
    from spacetea.plugin import RunAction
    from spacetea.actions import Touch

    target = 'hello.txt'
    outfile = Path('touchme.txt')
    action = Touch(target=str(outfile))

    RunAction(action, key=target)

    assert outfile.exists()


def test_SpaceTea_RunTests_pytest():
    """
    Test that a 'pytest' strategy for a file will invoke a `py.test`
    subprocess.
    """
    # test that the RunTests function will ... what?
    from spacetea import Config, RunTests

    raise Exception("TODO: complete this test")  # noqa


def test_SpaceTea_RunTests_command():
    """
    Test that a 'command' strategy for a file will invoke an arbitrary shell
    command.
    """
    # test that the RunTests function will ... what?
    from spacetea import Config, RunTests

    raise Exception("TODO: complete this test")  # noqa
