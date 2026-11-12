import random
import time

_STORE = {}


def issue():
    now = time.time()
    for key, (_, expires) in list(_STORE.items()):
        if expires < now:
            _STORE.pop(key, None)
    alphabet = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
    code = ''.join(random.choice(alphabet) for _ in range(4))
    cid = f'{int(now)}{random.randint(1000, 9999)}'
    _STORE[cid] = (code.lower(), now + 180)
    letters = ''.join(
        f'<text x="{18 + index * 24}" y="28" font-size="22" fill="#0f766e" '
        f'transform="rotate({random.randint(-12, 12)} {18 + index * 24} 28)">{char}</text>'
        for index, char in enumerate(code)
    )
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="40">'
        '<rect width="120" height="40" rx="6" fill="#f3faf8"/>'
        f'{letters}</svg>'
    )
    return cid, svg


def check(cid, value):
    row = _STORE.pop(str(cid or ''), None)
    if not row:
        return False
    code, expires = row
    if expires < time.time():
        return False
    return code == str(value or '').strip().lower()
