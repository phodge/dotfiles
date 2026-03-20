---
name: writing-code
description: General instructions for any situation where an agent is asked to write code.
---

In general, comments should explain WHY something is being done.

Any code that is likely to be confusing, hard to understand, or makes use of
esoteric or non-mainstream libraries or features should have comments to
explain what it is doing.

Don't assume that the person reading the code is familiar with esoteric or
non-mainstream libraries or command-line tools or flags. When you use such
libraries, tools, or flags, add a comment to explain what the library or tool
is doing. If possible add a link to the feature's documentation in the comment.

Examples of esoteric or non-mainstream libraries and tools would be:
1. Regular expressions using features beyond '.', '^' or basic character classes
2. SQL queries using syntax beyond simple JOIN / LEFT JOIN, WHERE FIELD = VALUE
3. Invoking shell CLI tools such as "awk" or "sed"
3. Invoking git with a command more advanced than a simple "clone", "pull",
   "push", "checkout". Or invoking a git command with --arguments or -flags.
