# -*- coding: utf-8 -*-
"""check_bars.py -- verify that every bar in an ABC file sums to the meter.

Usage:
    python check_bars.py tune.abc [more.abc ...]

Every bar whose total duration differs from the current meter is printed.
Bars SHORTER than the meter are reported as "pickup?" and must be confirmed
intentional by the engraver (anacrusis, the incomplete bar before a repeat,
a deliberate incomplete measure). Bars LONGER than the meter are reported as
"OVER" and are always errors. Inline [M:...] meter changes are tracked.
Exit code is 1 when any bar is OVER, else 0.

Supported: notes/rests with length suffixes (A, A2, A/, A//, A3/2), dotted
shorthands (A3/ for dotted-8th in L:1/8), grace notes {..} (zero duration),
decorations !..!, annotations "..", repeat bars |: :| [1 [2 |], ties.
Not supported: tuplets, chords, multiple voices (add them manually to the sum).
"""
import re
import sys
from fractions import Fraction

NOTE_RE = re.compile(r"[\^_=]*([A-Ga-gz])([,']*)(\d+(?:/\d*)?|/+)?")
INLINE_FIELD_RE = re.compile(r"\[([A-Za-z]):([^\]]*)\]")


def parse_meter(text):
    text = text.strip()
    if text == 'C':
        return Fraction(4, 4)
    if text == 'C|':
        return Fraction(2, 2)
    return Fraction(text)


def bar_length(bar, unit):
    """Sum the durations in one bar; unit = L: default length as Fraction."""
    s = INLINE_FIELD_RE.sub(' ', bar)          # [M:2/4] etc. carry no duration
    s = re.sub(r'"[^"]*"', ' ', s)             # annotations
    s = re.sub(r'![^!]*!', ' ', s)             # decorations (!fermata! ...)
    s = re.sub(r'\{[^}]*\}', ' ', s)           # grace notes: zero duration
    s = re.sub(r'\(\d+', ' ', s)               # tuplet markers (unsupported)
    s = s.replace('-', ' ')                    # ties
    total = Fraction(0)
    for m in NOTE_RE.finditer(s):
        letter, leng = m.group(1), m.group(3) or ''
        if letter in 'LMKTUVWw':               # stray field letters
            continue
        mult = Fraction(1)
        if leng:
            if set(leng) == {'/'}:
                mult = Fraction(1, 2 ** len(leng))
            elif '/' in leng:
                num, _, denom = leng.partition('/')
                mult = Fraction(int(num) if num else 1,
                                int(denom) if denom else 2)
            else:
                mult = Fraction(int(leng))
        total += unit * mult
    return total


def check(path):
    lines = open(path, encoding='utf-8').read().split('\n')
    unit = Fraction(1, 8)
    meter = Fraction(4, 4)
    music = []
    in_header = True
    for ln in lines:
        ln = ln.strip()
        if in_header:
            if ln.startswith('L:'):
                unit = Fraction(ln[2:])
            elif ln.startswith('M:'):
                meter = parse_meter(ln[2:])
            elif ln.startswith('K:'):
                in_header = False           # K: is the last header field
            continue
        if not ln or ln.startswith('%%') or re.match(r'^[A-Za-z]:', ln):
            continue                        # comments, lyric w: lines, fields
        music.append(ln)

    # normalise every barline variant to a plain split point
    text = ' '.join(music)
    text = text.replace(':|]', '|').replace(':|', '|').replace('|:', '|')
    text = text.replace(':||:', '|').replace('|]', '|')
    text = re.sub(r'\[\d', ' ', text)           # first/second ending brackets
    bars = [b.strip() for b in text.split('|')]

    print(f'--- {path}: unit {unit}, {len(bars)} bars')
    bad_over = bad_short = 0
    cur_meter = meter
    for i, b in enumerate(bars):
        if not b or b in (':',):
            continue
        for f, v in INLINE_FIELD_RE.findall(b):
            if f == 'M':
                cur_meter = parse_meter(v)      # meter change applies here
        total = bar_length(b.replace(':', ' '), unit)
        if total == 0:
            continue                            # annotation-only pseudo bar
        if total == cur_meter:
            continue
        if total > cur_meter:
            bad_over += 1
            status = 'OVER'
        else:
            bad_short += 1
            status = 'pickup?'
        print(f'bar {i:2d}: {str(total):>6} vs {str(cur_meter):>6}  {status:8s}| {b[:64]}')
    print(f'{bad_over} OVER, {bad_short} short (verify shorts are intentional)')
    return bad_over


rc = 0
for p in sys.argv[1:]:
    rc |= check(p)
sys.exit(rc)
