"""Bounded adaptive question difficulty; proficiency is evaluated separately."""
BLOOMS_LEVELS = {1:'Remember',2:'Understand',3:'Apply',4:'Analyze',5:'Evaluate',6:'Create'}

def get_next_blooms_level(current_level, is_correct):
    return max(1,min(6,current_level + (1 if is_correct else -1)))
