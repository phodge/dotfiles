---
name: working-with-git-repos-and-python-projects
description: General instructions for working with python project in a git repo.
---

Don't assume that tools like "pytest" can be executed with "python" or
"python3".

If there is a README.md in the repo root, read it to see if there are explicit
instructions for how to set up a python virtual environment, and whether it
should be managed with "uv", "poetry" or another tool. If these instructions
exist, do one of the following:
1. If the virtual environment doesn't exist yet, summarise the setup
   instructions and ASK the operator if they would like the virtual environment
   created for them. If they approve, go ahead and create the virtual
   environment using those instructions, then use that virtual environment for
   any future commands that need it.
2. If a virtual environment already exists, ASK the operator and whether they
   would like to use that virtual environment. If they approve, use that
   virtual environment for all future commands that need one.
3. If the operator doesn't want to use a virtual environment as per the repo
   instructions, ASK if they would like to create a virtual environment using
   the following approach:
   - Run `python3 -m venv .venv_3<python_minor_version>` to create a virtualenv using the default python3 executable.
   - Examine any pyproject.cfg, pyproject.toml or other python project
     configuration files to see whether there are dev dependencies to install
     and determine what CLI flags pip might need to install the dev dependencies
   - Run `.venv3_/bin/pip install -e .` to install the project and its dependencies (including dev dependencies) into that virtual environment.
   If they approve, create the virtual environment as per that approach, and use this virtual environment for all future commands that need it.
   - The virtual environment can be created in the background, but no commands
     should attempt to use it until all dependencies have been installed
     successfully.

If the repo doesn't contain instructions for virtual environment management, look for a python virtual environment in the root of the git repo,
with a name like ".venv*" or similar. If there are multiple to choose from,
ALWAYS ask the operator which virtual environment they would like to use.

