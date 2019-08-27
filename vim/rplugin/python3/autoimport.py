import enum
import functools
import re
from importlib import import_module

import pynvim

NAME_RE = re.compile(r'^[a-z_][a-z0-9_]*', re.IGNORECASE)

# these will be added without prompting if there are no conflicts
COMMON_STDLIB = [
    'abc',
    'asyncio',
    'base64',
    'collections',
    'configparser',
    'contextlib',
    'dataclasses',
    'decimal',
    'enum',
    'functools',
    'itertools',
    'json',
    'logging',
    'math',
    'os',
    'os.path',
    'pathlib',
    'random',
    're',
    'shlex',
    'shutil',
    'simplejson',
    'subprocess',
    'sys',
    'tempfile',
    'textwrap',
    'typing',
    'typing_extensions',
    'warnings',
]

# these will be suggested
OTHER_STDLIB = [
    'argparse',
    'atexit',
    'calendar',
    'contextvars',
    'datetime',
    'difflib',
    'distutils',
    'errno',
    'glob',
    'hashlib',
    'homely',
    'html',
    'html.entities',
    'http',
    'http.client',
    'http.cookiejar',
    'http.cookies',
    'http.server',
    'importlib',
    'inspect',
    'io',
    'mimetypes',
    'modulefinder',
    'operator',
    'optparse',
    'platform',
    'pprint',
    'readline',
    'requests',
    'select',
    'socket',
    'sqlite3',
    'string',
    'time'
    'weakref',
    'xml',
    'zipfile',
]

EXTERNAL = [
    'click',
    'homely',
    'homely.files',
    'homely.general',
    'homely.install',
    'homely.pipinstall',
    'homely.system',
    'homely.ui',
    'neovim',
    'sqlalchemy',
    'sqlalchemy.sql',
    'sqlalchemy.sql.functions',
    'sqlalchemy.event',
    'sqlalchemy.pool',
    'sqlalchemy.engine',
    'sqlalchemy.interfaces',
    'sqlalchemy.exc',
    'sqlalchemy.types',
    'sqlalchemy.dialects',
    'sqlalchemy.schema',
]

EXTERNAL_SPECIFIC = {
    'Href': 'werkzeug',
    # TODO: add sqlalchemy stuff here
    'Gitlab': 'gitlab',
}


# make a list of stdlib modules (cached)
# TODO: rather than asking the current python process, allow asking the correct
# python version
@functools.lru_cache()
def getStdlibNames():
    # TODO: do we want to have a hardcoded list of stdlib names here or offer suggestions from the
    # entire stdlib?
    return COMMON_STDLIB


class Origin(enum.Enum):
    stdlib = 'from stdlib'
    external = 'from external package'
    tags = 'from tags'


@functools.lru_cache(maxsize=1000, typed=True)
def getAllStdlibSuggestions(target):
    ret = []
    for libname in COMMON_STDLIB + OTHER_STDLIB:
        # are we trying to import the module itself?
        if target == libname:
            ret.append((libname, None, Origin.stdlib))

        try:
            module = import_module(libname)
        except ImportError:
            # ignore missing imports - we might not have that module in our python version
            continue
        if hasattr(module, target):
            ret.append((libname, target, Origin.stdlib))
    return ret


def getAllExternalLibSuggestions(target):
    # NOTE: this can't be cached - in case a new module is installed we wouldn't pick it up
    external = []
    for otherlib in EXTERNAL:
        try:
            import_module(otherlib)
            external.append(otherlib)
        except ImportError:
            # ignore if the package is not available
            continue

    # we now have a list of external modules that *are* available and this is something we *can*
    # use to cache import lookups
    return getKnownExternalLibSuggestions(target, tuple(external))


@functools.lru_cache(maxsize=1000, typed=True)
def getKnownExternalLibSuggestions(target, externallibs):
    ret = []
    for otherlib in sorted(externallibs):
        module = import_module(otherlib)

        if otherlib == target:
            ret.append((otherlib, None, Origin.external))

        # get suggestions out of the module itself
        if hasattr(module, target):
            ret.append((otherlib, target, Origin.stdlib))

    return ret


@functools.lru_cache(maxsize=1000, typed=True)
def getOtherLibSuggestions(target, otherlib):
    raise Exception("TODO: finish this")  # noqa


@pynvim.plugin
class Autoimport:
    def __init__(self, vim):
        self.vim = vim

    def showWarning(self, msg):
        self.vim.command('echohl WarningMsg')
        try:
            self.vim.command("echo '{}'".format(msg.replace("'", "''")))
        finally:
            self.vim.command('echohl None')

    @pynvim.command('AddPythonImport', nargs=1, sync=True)
    def autoimport(self, args):
        if not len(args):
            self.showWarning('An import name is required')
            return

        target = args[0]
        if not NAME_RE.match(target):
            self.showWarning('Cannot import {!r}'.format(target))
            return

        # short-circuit #1: if target is one of the COMMON_STDLIB modules, we add an import for
        # it immediately without prompting
        if target in COMMON_STDLIB:
            self.addSimpleImport(target)
            return

        # step1: find out where we can import this thing from
        suggestions = self.getSuggestionsFromTags(target)
        suggestions.extend(getAllStdlibSuggestions(target))
        suggestions.extend(getAllExternalLibSuggestions(target))

        # if there's no suggestions, bomb out
        if not len(suggestions):
            self.showWarning('Cannot auto-import {}: not found in stdlib or tags'.format(target))
            return

        self.showWarning('Bad things')
        return

    def getSuggestionsFromTags(self, target):
        ret = []
        for tag in self.vim.call('taglist', target):
            if tag['name'] == target and tag['filename'].endswith('.py'):
                # strip off .py
                stripped = tag['filename'][:-3]

                # make filename relative to current dir
                # TODO: this would be faster in python
                relative = self.vim.call('fnamemodify', stripped, ':.')

                # convert path separators to .
                candidate = relative.replace('/', '.')

                # if the name ends with '.__init__', strip it off
                if candidate.endswith('.__init__'):
                    candidate = candidate[:-9]

                ret.append((candidate, target, Origin.tags))
        return ret
