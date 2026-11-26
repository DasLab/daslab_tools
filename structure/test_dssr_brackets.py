#!/usr/bin/env python3
"""Tests for dssr.assign_brackets. Run: python3 structure/test_dssr_brackets.py (or pytest)."""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dssr


def parse(db):
    """Strict multi-page dot-bracket -> set of pairs (raises on imbalance)."""
    opens = {o: c for o, c in dssr.BRACKETS}; closes = {c: o for o, c in dssr.BRACKETS}
    st, out = {}, set()
    for k, ch in enumerate(db):
        if ch in opens:
            st.setdefault(ch, []).append(k)
        elif ch in closes:
            out.add((st[closes[ch]].pop(), k))
    assert all(not v for v in st.values()), db
    return out


def test_nested_unchanged():
    db, pages = dssr.assign_brackets([(0, 6), (1, 5)], 7)
    assert db == "((...))" and pages == 1


def test_pseudoknot_unchanged():
    pairs = [(0, 9), (1, 8), (4, 13), (5, 12)]          # two crossing 2-bp helices
    db, pages = dssr.assign_brackets(pairs, 14)
    assert parse(db) == set(pairs) and pages == 2, db


def test_g_tetrad_one_partner():
    # 6Q6R-like parallel G4, GGGTGGGTGGGTGGGT: each tetrad G pairs with two neighbours (cyclic Hoogsteen)
    g = [[0, 4, 8, 12], [1, 5, 9, 13], [2, 6, 10, 14]]
    pairs = sorted({tuple(sorted((t[a], t[(a + 1) % 4]))) for t in g for a in range(4)})
    dropped = []
    db, _ = dssr.assign_brackets(pairs, 16, dropped=dropped)
    kept = parse(db)                                      # used to raise: '([{.([{.([{.)]}.'
    assert kept | set(dropped) == set(pairs) and not (kept & set(dropped))
    pos = [k for ij in kept for k in ij]
    assert len(pos) == len(set(pos))                      # one partner per nucleotide
    assert dropped, "a tetrad cannot fit in one character per G"


def test_fuzz_shared_nucleotides():
    rng = random.Random(0)
    for _ in range(2000):
        n = rng.randint(6, 60)
        pairs = set()
        for _ in range(rng.randint(1, n)):
            i, j = sorted(rng.sample(range(n), 2))
            if j - i > 1:
                pairs.add((i, j))
        dropped = []
        db, _ = dssr.assign_brackets(sorted(pairs), n, dropped=dropped)
        kept = parse(db)
        assert kept <= pairs and kept | set(dropped) == pairs, (pairs, db, dropped)
        pos = [k for ij in kept for k in ij]
        assert len(pos) == len(set(pos)), db


def test_out_of_range_raises():
    try:
        dssr.assign_brackets([(0, 9)], 5)
    except IndexError:
        return
    raise AssertionError("expected IndexError")


if __name__ == "__main__":
    for name, f in sorted(globals().items()):
        if name.startswith("test_"):
            f(); print("ok", name)
