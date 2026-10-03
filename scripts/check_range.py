# -*- coding: utf-8 -*-
"""check_range.py -- verify that every note in an ABC file fits an instrument's range.

Usage:
    python check_range.py tune.abc [more.abc ...]            # default: violin G3..E7
    python check_range.py tune.abc --min G3 --max A6
    python check_range.py tune.abc --instrument viola        # C3..A6

Every note outside [min, max] is printed with its bar number and the bar text.
Exit code is 1 when any note is out of range, else 0.

Pitch parsing: ABC pitch letters C D E F G B are the octave of middle C (C4);
lowercase c..b are one octave up (C5..B5); each trailing comma lowers one
octave, each apostrophe raises one. Accidentals do not affect the range check
(a semitone never crosses the boundary decision by more than one semitone;
borderline cases are printed for human review).

Common instrument ranges (open strings / standard limits):
    violin  G3 E7     viola C3 A6     cello C2 C6     flute C4 D7
"""
import re
import sys

NOTE_RE = re.compile(r"[\^_=]*([A-Ga-gz])([,']*)(\d+(?:/\d*)?|/+)?")
INLINE_FIELD_RE = re.compile(r"\[[A-Za-z]:[^\]]*\]")

SEMI = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

INSTRUMENTS = {
    'violin': ('G3', 'E7'),
    'viola': ('C3', 'A6'),
    'cello': ('C2', 'C6'),
    'flute': ('C4', 'D7'),
}


def pitch_value(name):
    """'G3' -> midi number (G3 = 55)."""
    m = re.match(r"([A-Ga-g])(\d)", name)
    return (int(m.group(2)) + 1) * 12 + SEMI[m.group(1).upper()]


def abc_note_value(letter, octave_marks):
    """ABC note -> midi number, ignoring accidentals."""
    base = 4 if letter.isupper() else 5
    octave = base - octave_marks.count(',') + octave_marks.count("'")
    return (octave + 1) * 12 + SEMI[letter.upper()]


def pitch_name(midi):
    names = 'C C# D D# E F F# G G# A A# B'.split()
    return f'{names[midi % 12]}{midi // 12 - 1}'


def check(path, lo, hi):
    lines = open(path, encoding='utf-8').read().split('\n')
    music = []
    in_header = True
    for ln in lines:
        ln = ln.strip()
        if in_header:
            if ln.startswith('K:'):
                in_header = False
            continue
        if not ln or ln.startswith('%%') or re.match(r'^[A-Za-z]:', ln):
            continue
        music.append(ln)

    text = ' '.join(music)
    text = text.replace(':|]', '|').replace(':|', '|').replace('|:', '|')
    text = text.replace('|]', '|')
    bars = [b.strip() for b in text.split('|')]

    print(f'--- {path}: range {pitch_name(lo)}..{pitch_name(hi)}')
    bad = 0
    for i, b in enumerate(bars):
        b2 = INLINE_FIELD_RE.sub(' ', b)
        b2 = re.sub(r'"[^"]*"', ' ', b2)
        b2 = re.sub(r'![^!]*!', ' ', b2)
        for m in NOTE_RE.finditer(b2):
            letter, marks = m.group(1), m.group(2)
            if letter == 'z':
                continue
            v = abc_note_value(letter, marks)
            if v < lo or v > hi:
                bad += 1
                print(f'bar {i:2d}: {letter}{marks} = {pitch_name(v)}  OUT OF RANGE  | {b[:60]}')
    print(f'{bad} out-of-range note(s)')
    return bad


args = [a for a in sys.argv[1:] if not a.startswith('-')]
lo, hi = pitch_value('G3'), pitch_value('E7')
for i, a in enumerate(sys.argv):
    if a == '--min':
        lo = pitch_value(sys.argv[i + 1])
    elif a == '--max':
        hi = pitch_value(sys.argv[i + 1])
    elif a == '--instrument':
        lo, hi = (pitch_value(x) for x in INSTRUMENTS[sys.argv[i + 1]])

rc = 0
for p in args:
    rc |= check(p, lo, hi)
sys.exit(1 if rc else 0)
