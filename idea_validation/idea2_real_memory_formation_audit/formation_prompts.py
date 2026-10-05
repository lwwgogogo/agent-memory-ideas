"""Four frozen, generic Agent-style formation prompts."""
from core import formation_prompt, FORMATION_TYPES

def prompt_for(world, formation_type, budget):
    if formation_type not in FORMATION_TYPES:
        raise ValueError(formation_type)
    return formation_prompt(world, formation_type, budget)
