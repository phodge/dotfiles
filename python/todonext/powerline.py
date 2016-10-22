import os.path


def firstitem(pl, todofile=None):
    if todofile is None:
        todofile = os.path.join(os.environ['HOME'], 'TODO.txt')

    heading = None

    ret = []
    firstnonblank = True
    if os.path.exists(todofile):
        previndent = -1
        with open(todofile) as f:
            for line in map(str.rstrip, f):
                trimmed = line.lstrip()
                if not len(trimmed):
                    continue
                if firstnonblank:
                    firstnonblank = False
                    if line == trimmed and line.isupper():
                        heading = line
                        continue

                indent = len(line) - len(trimmed)
                if indent <= previndent:
                    break
                previndent = indent
                if trimmed.startswith('- '):
                    trimmed = trimmed[2:]
                if len(ret):
                    # append our own divider that's not as bright
                    ret.append({
                        'contents': '  ',
                        'highlight_groups': ["TODONEXT:DIVIDER"],
                        'draw_inner_divider': False,
                        'draw_hard_divider': False,
                    })
                ret.append({
                    'contents': trimmed,
                    'highlight_groups': ["TODONEXT:ITEM"],
                    'draw_inner_divider': False,
                    'draw_hard_divider': False,
                })
    if len(ret):
        ret.insert(0, {
            'contents': ' ',
            'highlight_groups': ["TODONEXT:ITEM"],
            'draw_hard_divider': False,
        })
        ret.insert(0, {
            'contents': ' {}'.format(heading or 'NEXT'),
            'highlight_groups': ["TODONEXT:HEAD"],
            'draw_hard_divider': False,
        })
        # something to try and get rid of the left-divider
        ret.insert(0, {
            'contents': '',
            'highlight_groups': ["background"],
            'draw_hard_divider': False,
        })
    return ret
