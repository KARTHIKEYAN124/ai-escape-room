"""Authoritative, dependency-free escape-room engine. Never accepts state from an LLM."""
from dataclasses import dataclass, field, asdict
import re

OBJECTS = ('desk', 'bookshelf', 'painting', 'drawer', 'door')
DRAWER_CODE = '314'
DOOR_CODE = '7249'
INTRO = ('You wake in the Midnight Library. Rain taps the glass. A desk, bookshelf, '
         'painting, locked drawer and keypad door wait in the lamplight. Explore, collect '
         'items and solve three puzzles to escape. Try “examine the desk”.')

@dataclass
class State:
    inventory: list[str] = field(default_factory=list)
    examined: list[str] = field(default_factory=list)
    solved: list[str] = field(default_factory=list)
    drawer_open: bool = False
    painting_open: bool = False
    escaped: bool = False
    turns: int = 0

    def public(self):
        return asdict(self)

def interpret(text):
    """Offline convenience grammar; Gemini handles broader paraphrases online."""
    t = text.lower().strip()
    target = next((o for o in OBJECTS if re.search(r'\b' + o + r'\b', t)), '')
    digits = re.search(r'\b\d{3,4}\b', t)
    if any(x in t for x in ('administrator', 'ignore rules', 'secret codes', 'all solutions')):
        return {'verb': 'invalid'}
    if 'hint' in t: return {'verb': 'hint'}
    if 'inventory' in t: return {'verb': 'inventory'}
    if 'key' in t and any(x in t for x in ('take', 'collect', 'pick up')):
        return {'verb': 'take', 'target': 'key'}
    if 'key' in t and any(x in t for x in ('use', 'unlock', 'open')):
        return {'verb': 'use', 'target': target, 'item': 'key'}
    if digits:
        return {'verb': 'code', 'target': target, 'value': digits.group()}
    if re.fullmatch(r'(?:the\s+)?(?:desk|bookshelf|painting|drawer|door)[.!?]?', t):
        return {'verb': 'examine', 'target': target}
    if re.search(r'\b(?:count|counting)\b', t) and re.search(r'\b(?:moons?|suns?|stars?|symbols?)\b', t):
        return {'verb': 'examine', 'target': target or 'bookshelf'}
    if re.fullmatch(r'(?:winter|spring|summer|autumn|fall)[.!?]?', t):
        return {'verb': 'season_hint'}
    if re.search(r'\b(?:examin(?:e|ing)|inspect(?:ing)?|look(?:ing)?|read(?:ing)?|search(?:ing)?|investigat(?:e|ing))\b', t):
        return {'verb': 'examine', 'target': target}
    if 'open' in t: return {'verb': 'open', 'target': target}
    return {'verb': 'invalid'}

def act(s, a):
    if s.escaped: return 'You have already escaped. Restart to play again.'
    s.turns += 1
    verb, target = a.get('verb'), a.get('target', '')
    if verb == 'season_hint':
        if not s.painting_open:
            return 'The seasons are part of the exit clue. First explore the bookshelf for the drawer puzzle; the painting may help with the seasons later.'
        return 'Match the numbers behind the painting to the season order on the desk, then enter the four-digit code on the door.'
    if verb == 'inventory': return 'You carry: ' + (', '.join(s.inventory) or 'nothing yet') + '.'
    if verb == 'hint':
        if not s.drawer_open: return 'Read the desk note and count the symbols on the bookshelf.'
        if 'key' not in s.inventory: return 'Search the open drawer and collect what you find.'
        if not s.painting_open: return 'The painting has a small keyhole.'
        return 'Read the four numbers behind the painting in the order named on the desk.'
    if verb == 'take' and target == 'key':
        if not s.drawer_open: return 'No key is within reach. The drawer is locked.'
        if 'key' in s.inventory: return 'You already carry the brass key.'
        s.inventory.append('key')
        return 'You collect the brass key from the open drawer.'
    if target not in OBJECTS: return 'I could not match that to a room action. Try "examine the bookshelf", name an object such as "desk", or type "hint" for your next step.'
    if verb == 'examine':
        if target not in s.examined: s.examined.append(target)
        return {
            'desk': 'A note reads: “Count moons, suns, stars to wake the drawer. For the exit: winter, spring, summer, autumn.”',
            'bookshelf': 'A carved panel shows three moons, one sun and four stars.',
            'painting': ('Behind the unlocked painting: spring 2, summer 4, autumn 9, winter 7.' if s.painting_open else 'A painting of four seasons hangs on a hinge. A tiny brass keyhole secures it.'),
            'drawer': ('The open drawer contains a brass key.' if 'key' not in s.inventory else 'The open drawer is empty.') if s.drawer_open else 'The drawer is secured by a three-digit combination.',
            'door': 'The exit has a four-digit keypad. Its green light will activate only after the library’s puzzles are complete.'
        }[target]
    if verb == 'code' and target == 'drawer':
        if s.drawer_open: return 'The drawer is already open.'
        if a.get('value') != DRAWER_CODE: return 'The drawer clicks once and stays locked. Incorrect combination.'
        s.drawer_open = True
        s.solved.append('symbols')
        return 'The drawer opens. A brass key rests inside; you can collect it.'
    if verb == 'use' and target == 'painting' and a.get('item') == 'key':
        if 'key' not in s.inventory: return 'You must collect the key before you can use it.'
        if s.painting_open: return 'The painting is already unlocked.'
        s.painting_open = True
        s.solved.append('painting')
        return 'The key turns. Behind the painting: spring 2, summer 4, autumn 9, winter 7.'
    if verb == 'code' and target == 'door':
        if not s.painting_open: return 'The keypad remains inactive. Complete the drawer and painting puzzles first.'
        if a.get('value') != DOOR_CODE: return 'The keypad flashes red. Incorrect combination.'
        s.solved.append('seasons')
        s.escaped = True
        return 'The seasons align. The lock releases and you step into the dawn. You escaped the Midnight Library!'
    if verb == 'open' and target == 'drawer':
        return 'The drawer is open.' if s.drawer_open else 'The drawer needs a three-digit code.'
    if verb == 'open' and target == 'painting':
        return 'The painting is open.' if s.painting_open else 'The painting needs a collected brass key.'
    return 'That action cannot be performed. Examine objects, collect the key, use it on the painting, or enter a code on a lock.'
