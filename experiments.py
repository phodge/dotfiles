from homely.general import section, writefile
from HOMELY import EXP, HOME


DEEPCOOL2_UUID = "acc4f383-d2f3-411c-a84d-68e7891b9007"
MACITRON_UUID = "todo_here"
SPARK_UUID = "todo_here"
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
