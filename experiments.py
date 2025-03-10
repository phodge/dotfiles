from homely.general import section, writefile
from HOMELY import EXP, HOME


# I. DEVICE IDS
#
# Each device needs its own unique ID. Create a unique ID for this device by
# running the following command:
#
#   test -e $HOME/.config/experiments_uuid || uuidgen > $HOME/.config/experiments_uuid
#
# Then add a variable for your device below:
DEEPCOOL2_UUID = "acc4f383-d2f3-411c-a84d-68e7891b9007"
MACITRON_UUID = "todo_here"
SPARK_UUID = "e162867b-4d2c-49d7-ab4b-ed0b563e79cc"
OCTOMACM2_UUID = "982B22E0-830D-48FD-8B51-BC31909CDEC1"


# Use Vimade for dimming inactive windows in Vim/Neovim?
#
# Pros:
# - Highlight the current active window
# Cons:
# - Can be slow with many buffers open
#
# Note: old setting was called "want_vimade"
EXP.define_experiment(
    'FEAT_VIM_VIMADE',
    # Not currently used anywhere because it is too slow.
    by_uuid=[],
    active_until=None
)

# Attempt #1 at fixing Italic fonts in tmux on Ubuntu 22.04
EXP.define_experiment(
    # probably should be scrapped in favour of EXP_TMUX_DEFAULT_TERMINAL
    'EXP_TMUX_ITALIC_FIX1',
    by_uuid=[],
    active_until='2025-05-01',
)
EXP.define_experiment(
    # probably should be scrapped in favour of EXP_TMUX_DEFAULT_TERMINAL
    'EXP_TMUX_ITALIC_FIX2',
    by_uuid=[],
    active_until='2025-05-01',
)

# add 'set -g default-terminal tmux-256color to tmux.conf'.
# This should fix itatlic text in neovim in tmux.
#
# Seems to work in DEEPCOOL2_UUID (Ubuntu 22.04) but need to activate it on
# more environments to ensure its working.
#
# Test By:
# - open ~/src/blog.git/content/posts/real-cpu-cooling/index.md and search for ' _\w'
# - execute
#        :hi String gui=undercurl
#        :hi Identifier gui=strikethrough
#
# Confirmed not needed on SPARK_UUID
EXP.define_experiment(
    'EXP_TMUX_DEFAULT_TERMINAL',
    by_uuid=[DEEPCOOL2_UUID],
    active_until='2025-05-01',
)


@section(quick=True)
def refresh_experiments():
    with writefile(HOME + '/.config/experiments.sh') as f:
        first = True
        for exp in EXP.all_experiments():
            if first:
                first = False
            else:
                f.write("\n")

            state, reason = exp.get_state_and_reason()
            value = 1 if state else 0
            f.write(f"# From {exp.source}\n")
            f.write(f'export {exp.name}={value}  # {reason}\n')
