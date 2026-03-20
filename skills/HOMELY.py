import os

from homely.general import mkdir, section, symlink
from homely.ui import note, yesno

from HOMELY import HERE

SKILLS_DIR = os.path.join(HERE, 'skills')


want_agent_skills = yesno(
    'want_agent_skills',
    'Want skills/ symlinked to ~/.claude and ~/.agents?',
    None,
)


@section(quick=True, enabled=want_agent_skills)
def agent_skills():
    mkdir('~/.claude')
    mkdir('~/.claude/skills')
    mkdir('~/.agents')
    mkdir('~/.agents/skills')

    for name in os.listdir(SKILLS_DIR):
        skill_path = os.path.join(SKILLS_DIR, name)
        if os.path.isdir(skill_path) and not name.startswith(('.', '_')):
            symlink(skill_path, '~/.claude/skills/' + name)
            symlink(skill_path, '~/.agents/skills/' + name)
        else:
            note("Skipping " + name)
