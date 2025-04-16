from pathlib import Path
import tempfile
from textwrap import dedent
from subprocess import run

WORD_LIST_1 = list(filter(None, dedent(
    '''
    car
    red
    gnome
    battle
    fork
    knife
    spoon
    '''
).splitlines()))

DOTFILES_ROOT = Path(__file__).parent.parent

ALL_TESTS = []


def test(func):
    ALL_TESTS.append(func)
    return func


@test
def test_1():
    with tempfile.TemporaryDirectory() as tempdir:
        tmpdir = Path(tempdir)
        with open(tmpdir / 'all_words.txt', 'x') as f:
            f.write('\n'.join(WORD_LIST_1))

        # make a subfolder for temp state
        state_dir = tmpdir / 'workhere'
        state_dir.mkdir()

        cmd = [
            str(DOTFILES_ROOT / 'bin/find-required-words'),
            f'--state-dir={state_dir}',
            '--parallel=2',
            # the original words list
            f'--word-list-file={tmpdir}/all_words.txt',
            # put the temporary word list folder name into the variable
            # $SOME_DIR when running each --command
            '--word-list-path-var=SOME_FILE',
            # red, battle, and fork must not appear in optional word list
            '--command=! grep red $SOME_FILE',
            '--command=! grep battle $SOME_FILE',
            '--command=! grep fork $SOME_FILE',
            f"--summary-json={tmpdir}/summary.json",
        ]
        run(cmd, check=True)

        # verify contents of state_dir
        final_required_words = set((state_dir / 'required.txt').read_text().splitlines())
        final_optional_words = set((state_dir / 'optional.txt').read_text().splitlines())
        assert final_required_words == {'red', 'battle', 'fork'}
        assert final_optional_words == {'car', 'gnome', 'knife', 'spoon'}


@test
def test_2():
    # test that Strategy1 correctly does binary search of leftover words at end
    words = [
        '00_yes',
        '01_yes',
        '02_no',
        '03_yes',
        '04_yes',
        '05_yes',
        '06_yes',
        '07_yes',
        '08_yes',
        '09_yes',
        '10_yes',
        '11_yes',
        '12_yes',
        '13_yes',
        '14_yes',
    ]

    # order of evaluation should be:
    # 00-07, 00-03, 00-01, 02-3, 02, 03, 08-14
    return  # TODO: implement a binary search strategy


for testfn in ALL_TESTS:
    print("Test " + testfn.__name__)
    testfn()
