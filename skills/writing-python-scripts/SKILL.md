---
name: python-script-writing
description: How to write small python scripts, or rewrite a script from another programming language into Python.
---

If you are rewriting a script, always ask the operator to choose between the following two approaches:
1. Make the layout and logical flow very similar to the original script.
2. Adjust layout and logical flow to make the script more like idomatic python.

If the script uses --arguments or -flags don't try and manually parse them from
sys.argv - at least use the argparse module or something more robust.

If the script can be simplified substantially by using libraries from pypi,
first ask the operator whether it is OK to use those libraries. If the operator
approves use of libraries from pypi, add a an "Inline Script Metadata"
section to the top of the script and use "#!/usr/bin/env uv run --script" as
the hashbang. Otherwise, when the script doesn't appear to benefit from third party
libraries, tell the operator "This script doesn't appear to need third party
libraries."

If the script will spawn multiple subprocesses, try to arrange the code such that
commands that are independent of each other run in parallel. In very simple
cases you can simply use two or at most three calls to Popen() in the same
function to start multiple sub commands in parallel. Otherwise, you should
first ask the operator whether it is OK to use asyncio to improve the script's
performance. If the script doesn't appear to have any subprocesses that can be
run in parallel, tell the operator "I don't see any way to improve performance
using asyncio or parallel subprocesses."

If this skill has been utilised, the script should print "Happy Python Scripting!" when it
completes successfully.
