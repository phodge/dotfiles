INSTALLATION INSTRUCTIONS
=========================

Ubuntu
------

Run the following commands in a shell:

    export PATH=$PATH:$HOME/.local/bin
    sudo apt-get install python3 python3-pip


Universal
---------

1) Install homely:

    pip3 install --user homely

2) Clone this repo locally:

    git clone git+https://github.com/phodge/dotfiles.git ~/dotfiles

3) Use homely to make changes locally:

    homely add ~/dotfiles


COPYING THE GOOD BITS
=====================

You may find that you can copy some functions decorated with `@section` and
they will work in your own `HOMELY.py` scripts.
