if [ -n "$BASHPID" -o -n "$BASH_VERSION" ]; then
    DOTFILES_PATH="$(dirname ${BASH_SOURCE[0]})"
else
    DOTFILES_PATH="$(dirname ${(%):-%N})"
fi
source $DOTFILES_PATH/shell/_experiments.sh


# I. DEVICE IDS
#
# Each device needs its own unique ID. Create a unique ID for this device by
# running the following command:
#
#   test -e $HOME/.config/experiments_uuid || uuidgen > $HOME/.config/experiments_uuid
#
# Then add a variable and function for your new machine below:
DEEPCOOL2_UUID=acc4f383-d2f3-411c-a84d-68e7891b9007
MACITRON_UUID=todo_here
SPARK_UUID=todo_here
OCTOMACM2_UUID=todo_here


# II. DECLARE FEATURES & EXPERIMENTS
#
# Each experiment should a structure similar to the following:
#
#   # This feature will do X.
#   # Activated on LAPTOP3 on 2025-04-01.
#   # Also activated for all MacOS devices on 2025-04-08.
#   exp_by_device FEAT_XYZ $LAPTOP3_UUID
#   exp_by_macos FEAT_XYZ
#
# Declare the name, duration and learnings of all experiments here

# Not currently used anywhere because it is too slow
exp_unused FEAT_USE_VIMADE

# turn on Github Copilot in Neovim?
exp_by_device FEAT_NEOVIM_COPILOT $DEEPCOOL2_UUID
exp_by_device FEAT_NEOVIM_COPILOT $OCTOMACM2_UUID
