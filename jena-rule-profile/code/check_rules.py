#!/usr/bin/env python3
"""
Dry run of a compiled rule profile without Jena: compiles the rules from the
ontology (as compile_rules.py does), applies them to ontology + data with a
small forward chainer, and reports how many triples are inferred, by predicate,
and which consistency checks fire.

Use it to see what a profile does before deploying it in Fuseki, or to produce
the materialised closure as N-Triples (--closure) for loading into any store
with reasoning switched off.

Usage:
  python check_rules.py --ontology onto/*.ttl --data data/*.ttl
  python check_rules.py --ontology onto/*.ttl --data data/*.ttl --sameas --closure closure.nt
  python check_rules.py --ontology DUL.owl d0.owl onto/*.ttl --no-transitive dul:associatedWith \
                        --no-symmetric dul:associatedWith

Needs rdflib. Pure Python: fine for an ontology plus test data (ECMO + DUL +
case fixtures: about a minute), not for production-size data.
"""
import argparse
import time
from collections import Counter, defaultdict
from pathlib import Path

from rdflib import Literal

from compile_rules import VIOLATES, Compiler, load


def isvar(t):
    return isinstance(t, str) and t.startswith("?")


class Store:
    def __init__(self):
        self.spo = defaultdict(lambda: defaultdict(set))   # p -> s -> {o}
        self.pos = defaultdict(lambda: defaultdict(set))   # p -> o -> {s}
        self.size = 0

    def add(self, t):
        s, p, o = t
        if o in self.spo[p][s]:
            return False
        self.spo[p][s].add(o)
        self.pos[p][o].add(s)
        self.size += 1
        return True

    def match(self, pat, b):
        s, p, o = (b.get(x, x) if isvar(x) else x for x in pat)
        for pp in (list(self.spo) if isvar(p) else [p]):
            idx = self.spo.get(pp)
            if not idx:
                continue
            ext = {p: pp} if isvar(p) else {}
            if not isvar(s):
                objs = idx.get(s, ())
                if not isvar(o):
                    if o in objs:
                        yield {**b, **ext}
                else:
                    for oo in list(objs):
                        yield {**b, o: oo, **ext}
            elif not isvar(o):
                for ss in list(self.pos[pp].get(o, ())):
                    yield {**b, s: ss, **ext}
            else:
                for ss, objs in list(idx.items()):
                    for oo in list(objs):
                        if s == o and ss != oo:
                            continue
                        yield {**b, s: ss, o: oo, **ext}

    def triples(self):
        for p, idx in self.spo.items():
            for s, objs in idx.items():
                for o in objs:
                    yield s, p, o


def join(store, body, b):
    if not body:
        yield b
        return
    first, rest = body[0], body[1:]
    if first[0] == "notEqual":
        if b.get(first[1], first[1]) != b.get(first[2], first[2]):
            yield from join(store, rest, b)
        return
    for b2 in store.match(first, b):
        yield from join(store, rest, b2)


def forward_chain(rules, triples):
    """Semi-naive evaluation: each round only joins the triples derived in the previous one."""
    store, delta = Store(), []
    for t in triples:
        if store.add(t):
            delta.append(t)
    by_pred = defaultdict(list)
    for r in rules:
        for i, c in enumerate(r[1]):
            if c[0] != "notEqual":
                by_pred["*" if isvar(c[1]) else c[1]].append((r, i))
    rounds = 0
    while delta:
        rounds += 1
        new = []
        for t in delta:
            for r, i in by_pred.get(t[1], []) + by_pred.get("*", []):
                b, ok = {}, True
                for x, v in zip(r[1][i], t):
                    if isvar(x):
                        if b.setdefault(x, v) != v:
                            ok = False
                            break
                    elif x != v:
                        ok = False
                        break
                if not ok:
                    continue
                for b2 in join(store, r[1][:i] + r[1][i + 1:], b):
                    for h in r[2]:
                        ht = tuple(b2.get(x, x) if isvar(x) else x for x in h)
                        if not isinstance(ht[0], Literal) and store.add(ht):
                            new.append(ht)
        delta = new
    return store, rounds


def short(u):
    u = str(u)
    return u.rsplit("#", 1)[-1] if "#" in u else u.rsplit("/", 1)[-1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ontology", nargs="+", type=Path, required=True)
    ap.add_argument("--data", nargs="*", type=Path, default=[])
    ap.add_argument("--no-transitive", nargs="*", default=[], metavar="PROP")
    ap.add_argument("--no-symmetric", nargs="*", default=[], metavar="PROP")
    ap.add_argument("--sameas", action="store_true")
    ap.add_argument("--no-checks", action="store_true")
    ap.add_argument("--top", type=int, default=15, help="predicates to list")
    ap.add_argument("--closure", help="write ontology + data + inferences as N-Triples")
    args = ap.parse_args()

    t0 = time.time()
    g = load(args.ontology)
    rules = Compiler(g, args).compile().rules
    triples = set(g)
    if args.data:
        triples |= set(load(args.data))
    print(f"{len(rules):,} rules compiled from {len(g):,} ontology triples ({time.time() - t0:.1f} s)")

    t0 = time.time()
    store, rounds = forward_chain(rules, triples)
    inferred = store.size - len(triples)
    print(f"explicit {len(triples):,}  inferred {inferred:,}  total {store.size:,}  "
          f"({rounds} rounds, {time.time() - t0:.1f} s)")

    per_pred = Counter()
    for s, p, o in store.triples():
        if (s, p, o) not in triples:
            per_pred[p] += 1
    print(f"\nInferred triples per predicate (top {args.top}):")
    for p, n in per_pred.most_common(args.top):
        print(f"  {n:>9,}  {p}")

    viol = [(s, o) for s, objs in store.spo.get(VIOLATES, {}).items() for o in objs]
    print(f"\nConsistency checks fired: {len(viol)}")
    for what, n in Counter(str(o) for _, o in viol).most_common():
        ex = ", ".join(short(s) for s, o in viol if str(o) == what)[:200]
        print(f"  {n:>5}  {what}\n         e.g. {ex}")

    if args.closure:
        with open(args.closure, "w", encoding="utf-8") as fh:
            for t in store.triples():
                fh.write(" ".join(x.n3() for x in t) + " .\n")
        print(f"\nClosure written to {args.closure}")


if __name__ == "__main__":
    main()
