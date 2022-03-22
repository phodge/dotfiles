import json
import os

from homely.general import mkdir, section, writefile
from homely.system import execute, haveexecutable
from homely.ui import yesno

from HOMELY import want_php_anything

INIT_DONE = False
HOME = os.getenv('HOME')


def init_composer():
    global INIT_DONE

    if not haveexecutable('composer'):
        raise Exception("TODO: composer is not installed")  # noqa

    composer_config = {
        'minimum-stability': 'dev',
        'prefer-stable': True,
    }
    mkdir('~/.config')
    mkdir('~/.config/composer')
    with writefile('~/.config/composer/composer.json') as f:
        json.dump(composer_config, f)

    INIT_DONE = True


@section(enabled=want_php_anything)
def install_php_language_server():
    if not yesno('want_php_langserver', 'Install PHP Language Server?'):
        return

    init_composer()

    execute(
        ['composer', 'global', 'require', 'felixfbecker/language-server'],
    )
    execute(
        ['composer', 'run-script', 'parse-stubs'],
        cwd=HOME + '/.config/composer/vendor/felixfbecker/language-server',
    )


@section(enabled=want_php_anything)
def install_php_cs_fixer():
    if not yesno('want_php_cs_fixer', 'Install php-cs-fixer?'):
        return

    init_composer()

    execute(
        ['composer', 'global', 'require', 'friendsofphp/php-cs-fixer'],
    )
