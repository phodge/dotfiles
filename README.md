INSTALLATION INSTRUCTIONS
=========================

Ubuntu
------

First, make life easier on yourself:

    export PATH=$HOME/.local/bin

Next, `python3-pip` seems to install an old version of pip3 that segfaults, and
`ensurepip` doesn't seem to be installed. So you can use:

    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
	python3 get-pip.py --user && pip3 --version && rm -i get-pip.py


Universal
---------

1) Install homely:

    pip3 install homely

2) Clone this repo locally:

    git clone git+https://github.com/phodge/dotfiles.git ~/dotfiles

3) Use homely to make changes locally:

    homely add ~/dotfiles


COPYING THE GOOD BITS
=====================

You may find that you can copy some functions decorated with `@section` and
they will work in your own `HOMELY.py` scripts.
