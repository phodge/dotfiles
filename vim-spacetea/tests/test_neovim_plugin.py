from pathlib import Path


def test_commands_are_run_on_save(project):
    """
    This test sets up a .spacetea in a fake dir and verifies that neovim will
    automatically run the configured commands when a buffer is saved.
    """
    # create a file with unimportant file contents
    with project.open('hello.txt', 'w') as f:
        f.write('hello world\n')

    # add a strategy to hello.txt that will create a file we can check later
    outfile = Path('outputs.txt')

    project.setconfig('hello.txt',
                      strategy="touch", target=str(outfile))

    project.nvim(['hello.txt', '+wq'])

    assert outfile.exists()
