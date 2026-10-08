#!/usr/bin/env python3
"""
List every disjointness violation in ECMO + DUL + case data, with derivations.

GraphDB stops at the first consistency rule that fires; this script computes
the type inferences of OWL 2 RL that matter for disjointness and reports all
violations at once, grouped by the ECMO -> DUL alignment axioms they rely on.

Rules applied (a subset of OWL 2 RL, enough for class disjointness):
  subClassOf / equivalentClass, subPropertyOf / equivalentProperty,
  inverseOf, symmetric and transitive properties, rdfs:domain, rdfs:range,
  allValuesFrom, someValuesFrom, hasValue, intersectionOf, unionOf,
  disjointWith and AllDisjointClasses.
Not applied: owl:sameAs, property chains, cardinalities, datatypes.

Usage:
  python check_disjointness.py                                   # defaults below
  python check_disjointness.py --dul ecmo-deps/DUL.owl --data my-case.ttl
  python check_disjointness.py --no-data                         # ontology only

Requires rdflib (pip install rdflib).
"""
import argparse
import glob
import logging
from collections import Counter, defaultdict, deque
from pathlib import Path

import rdflib
from rdflib import OWL, RDF, RDFS, BNode, Literal, URIRef
from rdflib.collection import Collection

HERE = Path(__file__).resolve().parent
DUL_NS = "http://www.ontologydesignpatterns.org/ont/"
CASES = ["ecmo-ebola-case.ttl", "ecmo-hantavirus-case.ttl",
         "ecmo-coreference-pattern-fixture.ttl", "ecmo-phsm-fixtures.ttl"]
SCHEMA = {RDF.type, RDFS.subClassOf, RDFS.subPropertyOf, RDFS.domain, RDFS.range, OWL.inverseOf,
          OWL.equivalentClass, OWL.equivalentProperty, OWL.onProperty, OWL.someValuesFrom,
          OWL.allValuesFrom, OWL.hasValue, OWL.disjointWith, OWL.intersectionOf, OWL.unionOf,
          OWL.propertyChainAxiom, OWL.members, RDF.first, RDF.rest, OWL.sameAs, OWL.imports}


def parse(g, path):
    for fmt in ("turtle", "xml"):
        try:
            g.parse(path, format=fmt)
            return
        except Exception:
            continue
    raise SystemExit(f"Cannot parse {path}")


class Reasoner:
    def __init__(self, g):
        self.g = g
        self.nm = g.namespace_manager
        self._schema()
        self.types = defaultdict(dict)   # x -> {class: reason}
        self.edges = defaultdict(dict)   # (x, p) -> {y: reason}
        self.out = defaultdict(set)
        self.inn = defaultdict(set)
        self.queue = deque()

    def n(self, x):
        if isinstance(x, URIRef):
            return x.n3(self.nm)
        return "[restriction]" if (x, OWL.onProperty, None) in self.g else "[blank node]"

    def _list(self, head):
        try:
            return list(Collection(self.g, head))
        except Exception:
            return []

    def _schema(self):
        g = self.g
        self.subc = defaultdict(set)
        for a, b in g.subject_objects(RDFS.subClassOf):
            self.subc[a].add(b)
        for a, b in g.subject_objects(OWL.equivalentClass):
            self.subc[a].add(b)
            self.subc[b].add(a)
        self.subp = defaultdict(set)
        for a, b in g.subject_objects(RDFS.subPropertyOf):
            self.subp[a].add(b)
        for a, b in g.subject_objects(OWL.equivalentProperty):
            self.subp[a].add(b)
            self.subp[b].add(a)
        self.inv = defaultdict(set)
        for a, b in g.subject_objects(OWL.inverseOf):
            self.inv[a].add(b)
            self.inv[b].add(a)
        for p in g.subjects(RDF.type, OWL.SymmetricProperty):
            self.inv[p].add(p)
        self.trans = set(g.subjects(RDF.type, OWL.TransitiveProperty))
        self.dom, self.rng = defaultdict(set), defaultdict(set)
        for p, c in g.subject_objects(RDFS.domain):
            self.dom[p].add(c)
        for p, c in g.subject_objects(RDFS.range):
            self.rng[p].add(c)
        self.avf, self.svf, self.hv, self.hv_r = defaultdict(list), defaultdict(list), defaultdict(list), {}
        for r in g.subjects(OWL.onProperty, None):
            p = g.value(r, OWL.onProperty)
            if (f := g.value(r, OWL.allValuesFrom)) is not None:
                self.avf[r].append((p, f))
            if (f := g.value(r, OWL.someValuesFrom)) is not None:
                self.svf[p].append((f, r))
            if (v := g.value(r, OWL.hasValue)) is not None:
                self.hv[p].append((v, r))
                self.hv_r[r] = (p, v)
        self.inter, self.inter_of = {}, defaultdict(list)
        for c, h in g.subject_objects(OWL.intersectionOf):
            ms = self._list(h)
            self.inter[c] = ms
            for m in ms:
                self.inter_of[m].append(c)
        for c, h in g.subject_objects(OWL.unionOf):
            for m in self._list(h):
                self.subc[m].add(c)
        self.disjoint = set(g.subject_objects(OWL.disjointWith))
        for h in g.objects(None, OWL.members):
            ms = self._list(h)
            self.disjoint |= {(ms[i], ms[j]) for i in range(len(ms)) for j in range(i + 1, len(ms))}

    def add_type(self, x, c, why):
        if c not in self.types[x]:
            self.types[x][c] = why
            self.queue.append(("t", x, c))

    def add_edge(self, x, p, y, why):
        if y not in self.edges[(x, p)]:
            self.edges[(x, p)][y] = why
            self.out[x].add((p, y))
            self.inn[y].add((x, p))
            self.queue.append(("e", x, p, y))

    def run(self):
        g = self.g
        for x, c in g.subject_objects(RDF.type):
            if not str(c).startswith(str(OWL)):
                self.add_type(x, c, ("asserted",))
        for x, p, y in g:
            if p not in SCHEMA and not isinstance(y, Literal) and not str(p).startswith(str(RDFS)):
                self.add_edge(x, p, y, ("asserted",))
        while self.queue:
            item = self.queue.popleft()
            if item[0] == "t":
                self._type_rules(*item[1:])
            else:
                self._edge_rules(*item[1:])

    def _type_rules(self, x, c):
        for d in self.subc.get(c, ()):
            self.add_type(x, d, ("subClassOf", c))
        for p, f in self.avf.get(c, ()):
            for y in list(self.edges.get((x, p), {})):
                self.add_type(y, f, ("allValuesFrom", x, c, p))
        if c in self.hv_r:
            p, v = self.hv_r[c]
            self.add_edge(x, p, v, ("hasValue", c))
        for ic in self.inter_of.get(c, ()):
            if all(m in self.types[x] for m in self.inter[ic]):
                self.add_type(x, ic, ("intersectionOf",))
        for m in self.inter.get(c, ()):
            self.add_type(x, m, ("intersectionOf",))
        for s, p in list(self.inn.get(x, ())):
            for f, r in self.svf.get(p, ()):
                if f == c:
                    self.add_type(s, r, ("someValuesFrom",))

    def _edge_rules(self, x, p, y):
        for sp in self.subp.get(p, ()):
            self.add_edge(x, sp, y, ("subPropertyOf", p))
        for ip in self.inv.get(p, ()):
            self.add_edge(y, ip, x, ("inverseOf", p))
        for c in self.dom.get(p, ()):
            self.add_type(x, c, ("domain", p, y))
        for c in self.rng.get(p, ()):
            self.add_type(y, c, ("range", x, p))
        for c in list(self.types.get(x, {})):
            for pp, f in self.avf.get(c, ()):
                if pp == p:
                    self.add_type(y, f, ("allValuesFrom", x, c, p))
        for f, r in self.svf.get(p, ()):
            if f in self.types.get(y, {}) or f == OWL.Thing:
                self.add_type(x, r, ("someValuesFrom",))
        for v, r in self.hv.get(p, ()):
            if v == y:
                self.add_type(x, r, ("hasValue",))
        if p in self.trans:
            for p2, z in list(self.out.get(y, ())):
                if p2 == p:
                    self.add_edge(x, p, z, ("transitive", y))
            for w, p2 in list(self.inn.get(x, ())):
                if p2 == p:
                    self.add_edge(w, p, y, ("transitive", x))

    # ---------------------------------------------------------------- explanations
    def explain_type(self, x, c, causes, depth=0, seen=None):
        seen = seen if seen is not None else set()
        if (x, c) in seen or depth > 15:
            return []
        seen.add((x, c))
        why = self.types[x].get(c, ("?",))
        n = self.n
        if why[0] == "asserted":
            return [f"{n(x)} a {n(c)}   (asserted)"]
        if why[0] == "subClassOf":
            return self.explain_type(x, why[1], causes, depth + 1, seen) + [f"  {n(why[1])} ⊑ {n(c)}"]
        if why[0] == "domain":
            p, y = why[1], why[2]
            return self.explain_edge(x, p, y, causes, depth, seen) + [f"  domain({n(p)}) = {n(c)}  ⇒  {n(x)} a {n(c)}"]
        if why[0] == "range":
            s, p = why[1], why[2]
            return self.explain_edge(s, p, x, causes, depth, seen) + [f"  range({n(p)}) = {n(c)}  ⇒  {n(x)} a {n(c)}"]
        if why[0] == "allValuesFrom":
            s, rc, p = why[1], why[2], why[3]
            owner = next((a for a in self.types[s] if rc in self.subc.get(a, ()) and isinstance(a, URIRef)), None)
            lines = self.explain_type(s, rc, causes, depth + 1, seen) + self.explain_edge(s, p, x, causes, depth, seen)
            return lines + [f"  {n(owner) if owner else n(rc)} ⊑ ∀{n(p)}.{n(c)}  ⇒  {n(x)} a {n(c)}"]
        return [f"{n(x)} a {n(c)}   ({why[0]})"]

    def explain_edge(self, x, p, y, causes, depth, seen):
        chain, why = [p], self.edges[(x, p)].get(y, ("?",))
        while why[0] == "subPropertyOf":
            chain.insert(0, why[1])
            why = self.edges[(x, why[1])].get(y, ("?",))
        for a, b in zip(chain, chain[1:]):
            if DUL_NS not in str(a) and DUL_NS in str(b):
                causes.add(f"{self.n(a)} ⊑ {self.n(b)}")
        n = self.n
        lines = []
        if why[0] == "hasValue":
            lines.append(f"{n(x)} {n(chain[0])} {n(y)}   (from a hasValue restriction on a class of {n(x)})")
        elif why[0] == "inverseOf":
            src = why[1]
            lines += self.explain_edge(y, src, x, causes, depth + 1, seen)
            lines.append(f"  inverse  ⇒  {n(x)} {n(chain[0])} {n(y)}")
        elif why[0] == "transitive":
            mid = why[1]
            for a, b in ((x, mid), (mid, y)):
                if b in self.edges.get((a, chain[0]), {}):
                    lines += self.explain_edge(a, chain[0], b, causes, depth + 1, seen)
            lines.append(f"  transitivity of {n(chain[0])}  ⇒  {n(x)} {n(chain[0])} {n(y)}")
        else:
            lines.append(f"{n(x)} {n(chain[0])} {n(y)}   ({why[0]})")
        if len(chain) > 1:
            lines.append("  " + " ⊑ ".join(n(c) for c in chain))
        return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ecmo", default=str(HERE.parent / "ecmo-0.3.1-dl42-patched"))
    ap.add_argument("--dul", default=str(HERE / "dul-variants" / "DUL-lite.ttl"),
                    help="DUL file (default: DUL-lite; the disjointness results are the same as full DUL)")
    ap.add_argument("--d0", default=str(HERE / "ecmo-deps" / "d0.owl"))
    ap.add_argument("--data", nargs="*", help="data files (default: the ECMO case fixtures)")
    ap.add_argument("--no-data", action="store_true")
    ap.add_argument("--examples", type=int, default=1, help="derivations shown per group (default 1)")
    args = ap.parse_args()
    logging.getLogger("rdflib").setLevel(logging.ERROR)

    ecmo = Path(args.ecmo)
    onto = sorted(glob.glob(str(ecmo / "ecmo-*.ttl"))) + sorted(glob.glob(str(ecmo / "0.3.1-alignments" / "*.ttl")))
    data = [] if args.no_data else (args.data if args.data is not None
                                    else [str(ecmo / "0.3.1-unittests" / f) for f in CASES])
    files = onto + [args.dul] + ([args.d0] if Path(args.d0).exists() else []) + data
    g = rdflib.Graph()
    for f in files:
        parse(g, f)
    for prefix, ns in (("dul", DUL_NS + "dul/DUL.owl#"), ("ebola", "http://data.europa.eu/h8v/ecmo/examples/ebola/"),
                       ("hondius", "http://data.europa.eu/h8v/ecmo/examples/hondius/")):
        g.bind(prefix, ns, override=True, replace=True)
    print(f"Loaded {len(files)} files ({len(onto)} ECMO modules/alignments, DUL: {Path(args.dul).name}, "
          f"{len(data)} data files), {len(g):,} triples")

    r = Reasoner(g)
    r.run()
    violations = [(x, a, b) for x, ts in r.types.items() for a, b in r.disjoint if a in ts and b in ts]
    print(f"Disjointness violations: {len(violations)}\n")
    if not violations:
        return

    groups, examples = defaultdict(list), {}
    for x, a, b in violations:
        causes, lines = set(), []
        for c in (a, b):
            lines += r.explain_type(x, c, causes)
        key = (f"{r.n(a)} ⊓ {r.n(b)}", tuple(sorted(causes)))
        groups[key].append(r.n(x))
        examples.setdefault(key, []).append((r.n(x), lines))

    for (clash, causes), xs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print("=" * 100)
        print(f"{len(xs)} individual(s) in {clash}")
        print(f"  ECMO → DUL alignments involved: {', '.join(causes) or '(none: class axioms only)'}")
        print(f"  individuals: {', '.join(sorted(xs))}")
        for name, lines in examples[(clash, causes)][:args.examples]:
            print(f"\n  derivation for {name}:")
            seen = set()
            for line in lines:
                if line not in seen:
                    seen.add(line)
                    print("    " + line)
        print()
    print("Summary:", dict(Counter(k[0] for k in groups for _ in groups[k])))


if __name__ == "__main__":
    main()
