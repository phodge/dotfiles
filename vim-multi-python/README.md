vim-multi-python
================

Provides several things which make it easy to work with multiple versions of python at once:

* I want to support py2.7 and 3.4+, which means I need to highlight as errors
  syntax that is only available in py3 or py2 but not both.
* I may want to temporarily raise my py3 ceiling to py3.5 so that I can see
  asyncio highlighting as well

Therefore we define the following functions.

`multipython#togglepy2()`:

toggles python2 support between `2.4` (2.4+), `2.7` and `""` (disabled).

In order to activate `2.4` mode you must have a `python2.4` executable in your
path.

Generally speaking, if your minimum version is X, then core features from
higher versions of python will be highlighted as errors. And also, that python
executable and it's site-packages bin dir will be used by
`multipython#getpythoncmd()`.

`multipython#setpy2(version)`:

Sets minimum python2 support to the exact `version` which can be one of `2.4` `2.7` or `""` to turn it off.

`multipython#setpy3(version)`:

Sets minimum python3 support to the exact `version` which can be one of `3.4` `3.5` or `""` to turn it off.

`multipython#togglepy3()`:

toggles python3 support between `3.4` (3.4+), `3.5` (3.5+) and `""` (disabled).

`multipython#setpreferredpy(number)`:

`number` can be `2` or `3`. If your buffer has both py2 and py3 support, this
dictates which python version will be used for commands like `flake8`. Defaults to `3`. Your $PATH

`multipython#getpythoncmd(majorversion, command="python")`:
`majorversion` must be `"2"` or `"3"` or "" to get whichever the user preferrs.
You can use it in ways such as `flake8exec = multipython#getpythoncmd("",
"flake8")` to run whichever flake8 the user prefers.

`multipython#setpy2paths(paths)`:
`paths` is a list of folder names to be added to $PATH when looking for for the specified

`multipython#max_py_version([version])` returns the maximum python version the user is targetting
`b:python_major_version`: available in any buffer with the `python` filetype.
Will always be one of:

* `"py2"`: python-2-only
* `"py3"`: python-3-only
* `"py`b:python_major` and `b:python_minor_version`
* `multipython#addversiondetector([callback])`: define a 
    
