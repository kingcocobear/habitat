#!/usr/bin/env python3
"""
ternary.py - balanced ternary math for the habitat.

Balanced ternary is the number system the Soviet Setun computer (1958) used.
Each digit (a "trit") is one of three values:

    -1  written "-"
     0  written "0"
    +1  written "+"

Numbers are written most-significant trit first, so "+0-" means
(+1 * 9) + (0 * 3) + (-1 * 1) = 8.

Everything here is plain Python with no outside packages, works offline,
and does its arithmetic trit by trit (it does not just convert to a normal
number, add, and convert back).

Run it directly to see a demo and self-test:

    python ternary.py            # demo
    python ternary.py --test     # self-test
    python ternary.py 42 -17     # show numbers in balanced ternary and add them
"""

import sys

TRIT_CHARS = {-1: "-", 0: "0", 1: "+"}
CHAR_TRITS = {"-": -1, "0": 0, "+": 1}

# Setun used 18-trit words. A 6-trit "tryte" holds -364..+364.
TRYTE = 6
WORD = 18


# ---------------------------------------------------------------- conversion

def to_trits(n):
    """Whole number -> list of trits, least-significant first."""
    if n == 0:
        return [0]
    trits = []
    while n != 0:
        r = n % 3
        n //= 3
        if r == 2:          # 2 is written as -1 with a carry of +1
            r = -1
            n += 1
        trits.append(r)
    return trits


def from_trits(trits):
    """List of trits (least-significant first) -> whole number."""
    total = 0
    for t in reversed(trits):
        total = total * 3 + t
    return total


def to_str(n):
    """Whole number -> balanced ternary text, e.g. 8 -> '+0-'."""
    return "".join(TRIT_CHARS[t] for t in reversed(to_trits(n)))


def from_str(s):
    """Balanced ternary text -> whole number, e.g. '+0-' -> 8."""
    if not s or any(c not in CHAR_TRITS for c in s):
        raise ValueError("balanced ternary text may only contain + 0 -")
    return from_trits([CHAR_TRITS[c] for c in reversed(s)])


def _trim(trits):
    """Drop leading zeros (which sit at the end of a least-first list)."""
    while len(trits) > 1 and trits[-1] == 0:
        trits.pop()
    return trits


# ---------------------------------------------------------------- arithmetic

def _add_trit(a, b, carry):
    """Add three trits. Returns (sum_trit, carry_trit)."""
    s = a + b + carry          # ranges -3..+3
    if s > 1:
        return s - 3, 1
    if s < -1:
        return s + 3, -1
    return s, 0


def add(a, b):
    """Add two trit lists (least-significant first), trit by trit."""
    out, carry = [], 0
    for i in range(max(len(a), len(b))):
        ta = a[i] if i < len(a) else 0
        tb = b[i] if i < len(b) else 0
        s, carry = _add_trit(ta, tb, carry)
        out.append(s)
    if carry:
        out.append(carry)
    return _trim(out)


def negate(a):
    """Flip every trit. In balanced ternary that is all it takes to negate."""
    return [-t for t in a]


def subtract(a, b):
    return add(a, negate(b))


def multiply(a, b):
    """Shift-and-add multiply. Each trit of b adds, skips, or subtracts a."""
    result = [0]
    for shift, tb in enumerate(b):
        if tb == 0:
            continue
        part = [0] * shift + (a if tb == 1 else negate(a))
        result = add(result, part)
    return _trim(result)


def sign(a):
    """Sign of a trit list is just its top non-zero trit: -1, 0 or +1."""
    for t in reversed(a):
        if t != 0:
            return t
    return 0


# ---------------------------------------------------------------- 3-way logic
# Three-valued logic: -1 = no / false, 0 = unknown / maybe, +1 = yes / true.

def t_not(a):
    return -a


def t_and(a, b):
    """True only if both are true; 'maybe' if unsure; false if either is."""
    return min(a, b)


def t_or(a, b):
    return max(a, b)


def t_consensus(a, b):
    """Agree -> that value. Disagree -> 0 (no decision)."""
    return a if a == b else 0


# ---------------------------------------------------------------- brain helper

class TernaryMind:
    """
    A tiny decision register for a habitat being.

    A being weighs something by collecting votes, each one a trit:
        +1 = for, 0 = no opinion, -1 = against
    Votes can carry a whole-number weight. The tally is kept in balanced
    ternary and the decision is simply the sign of the tally:
        +1 = do it, 0 = undecided, -1 = don't

    The tally is clamped to one tryte (-364..+364) so it saves as 6 characters.
    """

    LIMIT = (3 ** TRYTE - 1) // 2      # 364

    def __init__(self, tally="0"):
        self.trits = to_trits(from_str(tally))

    def vote(self, trit, weight=1):
        if trit not in (-1, 0, 1):
            raise ValueError("a vote must be -1, 0 or +1")
        if weight < 0:
            raise ValueError("weight must be 0 or more")
        step = multiply(to_trits(weight), [trit])
        self.trits = add(self.trits, step)
        value = max(-self.LIMIT, min(self.LIMIT, from_trits(self.trits)))
        self.trits = to_trits(value)
        return self

    def decide(self):
        return sign(self.trits)

    def reset(self):
        self.trits = [0]
        return self

    @property
    def value(self):
        return from_trits(self.trits)

    def __str__(self):
        text = "".join(TRIT_CHARS[t] for t in reversed(self.trits))
        return text.rjust(TRYTE, "0")

    # save / load as plain text so it drops into a JSON save file
    def to_save(self):
        return str(self)

    @classmethod
    def from_save(cls, text):
        return cls(text)


# ---------------------------------------------------------------- self-test

def self_test():
    checks = 0
    for n in range(-400, 401):
        assert from_trits(to_trits(n)) == n
        assert from_str(to_str(n)) == n
        assert from_trits(negate(to_trits(n))) == -n
        assert sign(to_trits(n)) == (n > 0) - (n < 0)
        checks += 4
    for a in range(-60, 61):
        for b in range(-60, 61):
            ta, tb = to_trits(a), to_trits(b)
            assert from_trits(add(ta, tb)) == a + b
            assert from_trits(subtract(ta, tb)) == a - b
            assert from_trits(multiply(ta, tb)) == a * b
            checks += 3
    big_a, big_b = 3 ** 17 - 5, -(3 ** 16) + 12345
    assert from_trits(add(to_trits(big_a), to_trits(big_b))) == big_a + big_b
    assert from_trits(multiply(to_trits(big_a), to_trits(big_b))) == big_a * big_b
    checks += 2
    assert to_str(8) == "+0-" and to_str(-8) == "-0+" and to_str(0) == "0"
    assert to_str(2) == "+-" and to_str(5) == "+--"
    checks += 5
    for a in (-1, 0, 1):
        assert t_not(t_not(a)) == a
        for b in (-1, 0, 1):
            assert t_and(a, b) == t_and(b, a) and t_or(a, b) == t_or(b, a)
            assert t_not(t_and(a, b)) == t_or(t_not(a), t_not(b))   # De Morgan
            assert t_consensus(a, b) == (a if a == b else 0)
            checks += 3
    m = TernaryMind()
    assert m.decide() == 0 and str(m) == "000000"
    m.vote(1, 5).vote(-1, 2)
    assert m.value == 3 and m.decide() == 1 and str(m) == "0000+0"
    m.vote(-1, 10)
    assert m.value == -7 and m.decide() == -1
    assert TernaryMind.from_save(m.to_save()).value == -7
    m.vote(1, 100000)
    assert m.value == TernaryMind.LIMIT and str(m) == "++++++"
    m.vote(-1, 100000)
    assert m.value == -TernaryMind.LIMIT and str(m) == "------"
    checks += 9
    for bad in ("", "12", "+2"):
        try:
            from_str(bad)
            raise AssertionError("bad text accepted")
        except ValueError:
            checks += 1
    return checks


def demo():
    print("Balanced ternary: each digit is - (minus one), 0, or + (plus one)\n")
    for n in (0, 1, 2, 3, 8, 42, -42, 364):
        print(f"  {n:>5}  =  {to_str(n)}")
    a, b = 42, -17
    print(f"\n  {a} + {b}:  {to_str(a)} + {to_str(b)} = "
          f"{''.join(TRIT_CHARS[t] for t in reversed(add(to_trits(a), to_trits(b))))}"
          f"  ({a + b})")
    print(f"  negating 42 just flips every trit: {to_str(42)} -> {to_str(-42)}")
    m = TernaryMind()
    m.vote(1, 4).vote(-1, 1).vote(0, 9)
    word = {1: "do it", 0: "undecided", -1: "don't"}[m.decide()]
    print(f"\n  A being votes +4, -1, and a shrug: tally {m} -> {word}")


def main(argv):
    if "--test" in argv:
        print(f"ternary self-test passed ({self_test()} checks)")
        return 0
    nums = [x for x in argv if x.lstrip("-").isdigit()]
    if nums:
        vals = [int(x) for x in nums]
        for v in vals:
            print(f"{v} = {to_str(v)}")
        if len(vals) == 2:
            print(f"sum = {to_str(vals[0] + vals[1])}  ({vals[0] + vals[1]})")
        return 0
    demo()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
