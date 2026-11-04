#!/usr/bin/env python3
"""
Compile an OWL ontology into a Jena rule profile tailored to it.

Instead of the generic Jena OWL rule sets, which reason over the schema and the
data together (and run out of memory on ECMO + DUL), this script reads the
ontology once and writes one forward rule per axiom, with the classes and
properties already filled in:

    ecmo:affects rdfs:domain ecmo:Hazard   ->   [(?x ecmo:affects ?y) -> (?x rdf:type ecmo:Hazard)]

The rules only fire on instance data, so the reasoner never touches the schema
at run time. They are all forward rules (->), so Jena's GenericRuleReasoner
runs them with its RETE engine and materialises the inferences when the data
is loaded, like GraphDB. They cover the OWL 2 RL rules that apply to the
constructs found in the ontology:

  properties   subPropertyOf, equivalentProperty, inverseOf, domain, range,
               symmetric, transitive, propertyChainAxiom
  classes      subClassOf / equivalentClass between class expressions built from
               named classes, intersectionOf, unionOf (sub-class side),
               someValuesFrom (sub-class side), hasValue, allValuesFrom
               (super-class side)
  checks       disjointWith / AllDisjointClasses / complementOf (named classes),
               asymmetric and irreflexive properties: a violation is written as
               (?x <urn:jena-profile#violates> "...") so it can be found with SPARQL
  sameAs       only with --sameas: functional and inverse-functional properties,
               hasKey, and owl:sameAs symmetry, transitivity and replacement

What is left out, and why, is listed in the report (--report): existentials and
cardinalities on the super-class side (they create new individuals), oneOf,
datatype restrictions, and every axiom built on them.

The rules are compiled from the schema, so they must be regenerated when the
ontology changes; instance data can be added and removed freely.

Usage:
  python compile_rules.py ONTO.ttl [ONTO2.ttl ...] -o ecmo.rules
  python compile_rules.py onto/*.ttl --no-transitive dul:isPartOf dul:hasPart -o ecmo.rules
  python compile_rules.py onto/*.ttl --sameas --schema-closure tbox-closure.ttl -o ecmo.rules

Needs rdflib.
"""
import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS, XSD

VIOLATES = URIRef("urn:jena-profile#violates")
X = "?x"
PREFIXES = {
    "dul": "http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#",
    "owl": str(OWL), "rdf": str(RDF), "rdfs": str(RDFS), "xsd": str(XSD),
}
DATATYPE_NS = (str(XSD), str(RDFS.Literal), str(RDF.PlainLiteral), str(RDF.langString),
               "http://www.w3.org/2000/01/rdf-schema#Datatype")


class Unsupported(Exception):
    pass


# ------------------------------------------------------------------ loading
def load(files):
    g = Graph()
    for f in files:
        fmt = "xml" if f.suffix in (".owl", ".rdf", ".xml") else None
        try:
            g.parse(f, format=fmt)
        except Exception:
            g.parse(f, format="turtle")      # DUL.owl is Turtle despite the extension
    return g


def expand(term):
    if ":" in term and not term.startswith("http"):
        p, local = term.split(":", 1)
        if p in PREFIXES:
            return URIRef(PREFIXES[p] + local)
    return URIRef(term)


# --------------------------------------------------------- class expressions
class Compiler:
    def __init__(self, g, args):
        self.g = g
        self.args = args
        self.rules = []          # (kind, body, head)
        self.skipped = Counter()
        self.skipped_examples = defaultdict(list)
        self.n = 0

    def fresh(self):
        self.n += 1
        return f"?v{self.n}"

    def lst(self, node):
        return list(Collection(self.g, node))

    def is_datatype(self, c):
        return isinstance(c, URIRef) and str(c).startswith(DATATYPE_NS) or \
            (c, RDF.type, RDFS.Datatype) in self.g

    def skip(self, why, what):
        self.skipped[why] += 1
        if len(self.skipped_examples[why]) < 3:
            self.skipped_examples[why].append(what)

    def cond(self, c, v):
        """Alternatives of body patterns meaning 'v is an instance of c' (sub-class side)."""
        g = self.g
        if isinstance(c, URIRef):
            if c == OWL.Thing:
                return [[]]
            if self.is_datatype(c):
                raise Unsupported("datatype")
            return [[(v, RDF.type, c)]]
        if (c, OWL.intersectionOf, None) in g:
            alts = [[]]
            for m in self.lst(g.value(c, OWL.intersectionOf)):
                alts = [a + b for a in alts for b in self.cond(m, v)]
            return alts
        if (c, OWL.unionOf, None) in g:
            return [a for m in self.lst(g.value(c, OWL.unionOf)) for a in self.cond(m, v)]
        p = g.value(c, OWL.onProperty)
        if p is not None:
            p = self.prop(p)
            if (c, OWL.hasValue, None) in g:
                return [[self.triple(v, p, g.value(c, OWL.hasValue))]]
            filler = g.value(c, OWL.someValuesFrom)
            if filler is None and str(g.value(c, OWL.minQualifiedCardinality) or "") == "1":
                filler = g.value(c, OWL.onClass)
            if filler is None and str(g.value(c, OWL.minCardinality) or "") == "1":
                filler = OWL.Thing
            if filler is not None:
                y = self.fresh()
                if self.is_datatype(filler):
                    return [[self.triple(v, p, y)]]
                return [[self.triple(v, p, y)] + a for a in self.cond(filler, y)]
            raise Unsupported("restriction on the sub-class side (" + self.kind(c) + ")")
        if (c, OWL.complementOf, None) in g:
            raise Unsupported("complementOf on the sub-class side")
        if (c, OWL.oneOf, None) in g:
            raise Unsupported("oneOf")
        raise Unsupported("unknown class expression")

    def heads(self, c, v):
        """List of (extra body, head) meaning 'v is an instance of c' (super-class side)."""
        g = self.g
        if isinstance(c, URIRef):
            if c == OWL.Thing:
                return []
            return [([], [(v, RDF.type, c)])]
        if (c, OWL.intersectionOf, None) in g:
            return [h for m in self.lst(g.value(c, OWL.intersectionOf)) for h in self.heads(m, v)]
        p = g.value(c, OWL.onProperty)
        if p is not None:
            p = self.prop(p)
            if (c, OWL.hasValue, None) in g:
                return [([], [self.triple(v, p, g.value(c, OWL.hasValue))])]
            filler = g.value(c, OWL.allValuesFrom)
            if filler is not None:
                if self.is_datatype(filler):
                    return []
                y = self.fresh()
                return [([self.triple(v, p, y)] + b, h) for b, h in self.heads(filler, y)]
            raise Unsupported("restriction on the super-class side (" + self.kind(c) + ")")
        if (c, OWL.unionOf, None) in g:
            raise Unsupported("unionOf on the super-class side")
        if (c, OWL.complementOf, None) in g:
            raise Unsupported("complementOf on the super-class side")
        raise Unsupported("unknown class expression")

    def kind(self, c):
        for k in (OWL.someValuesFrom, OWL.allValuesFrom, OWL.minCardinality, OWL.maxCardinality,
                  OWL.cardinality, OWL.minQualifiedCardinality, OWL.maxQualifiedCardinality,
                  OWL.qualifiedCardinality, OWL.hasSelf):
            if (c, k, None) in self.g:
                return k.split("#")[1]
        return "?"

    def prop(self, p):
        """A property expression: a named property or (inverse p) -> ('inv', p)."""
        if isinstance(p, BNode):
            q = self.g.value(p, OWL.inverseOf)
            if q is None:
                raise Unsupported("property expression")
            return ("inv", q)
        return p

    @staticmethod
    def triple(s, p, o):
        if isinstance(p, tuple):
            return (o, p[1], s)
        return (s, p, o)

    # ------------------------------------------------------------------ rules
    def add(self, kind, body, head):
        if not body:
            self.skip("rule with an empty body (sub-class is owl:Thing)", head)
            return
        head = [h for h in head if h not in body]
        if head:
            self.rules.append((kind, body, head))

    def subsumption(self, sub, sup, what):
        try:
            alts = self.cond(sub, X)
            hs = self.heads(sup, X)
        except Unsupported as e:
            self.skip(str(e), what)
            return
        for a in alts:
            for extra, head in hs:
                self.add("cax", a + extra, head)

    def compile(self):
        g, args = self.g, self.args
        # class axioms
        for s, o in g.subject_objects(RDFS.subClassOf):
            self.subsumption(s, o, f"{s} subClassOf {o}")
        for s, o in g.subject_objects(OWL.equivalentClass):
            self.subsumption(s, o, f"{s} equivalentClass {o}")
            self.subsumption(o, s, f"{o} equivalentClass {s}")
        # property axioms
        for p, q in g.subject_objects(RDFS.subPropertyOf):
            self.add("prp-spo1", [(X, p, "?y")], [(X, q, "?y")])
        for p, q in g.subject_objects(OWL.equivalentProperty):
            self.add("prp-eqp", [(X, p, "?y")], [(X, q, "?y")])
            self.add("prp-eqp", [(X, q, "?y")], [(X, p, "?y")])
        no_trans = {expand(t) for t in args.no_transitive}
        no_sym = {expand(t) for t in args.no_symmetric}
        for p, q in g.subject_objects(OWL.inverseOf):
            if isinstance(p, BNode) or isinstance(q, BNode):
                continue
            if p == q and p in no_sym:       # a self-inverse property is symmetric
                self.skip("symmetric property excluded by --no-symmetric", f"{p} inverseOf itself")
                continue
            self.add("prp-inv", [(X, p, "?y")], [("?y", q, X)])
            self.add("prp-inv", [(X, q, "?y")], [("?y", p, X)])
        for p, d in g.subject_objects(RDFS.domain):
            try:
                for extra, head in self.heads(d, X):
                    self.add("prp-dom", [(X, p, "?y")] + extra, head)
            except Unsupported as e:
                self.skip(str(e), f"{p} domain")
        for p, r in g.subject_objects(RDFS.range):
            if self.is_datatype(r):
                continue
            try:
                for extra, head in self.heads(r, "?y"):
                    self.add("prp-rng", [(X, p, "?y")] + extra, head)
            except Unsupported as e:
                self.skip(str(e), f"{p} range")
        for p in g.subjects(RDF.type, OWL.SymmetricProperty):
            if p in no_sym:
                self.skip("symmetric property excluded by --no-symmetric", p)
            else:
                self.add("prp-symp", [(X, p, "?y")], [("?y", p, X)])
        for p in g.subjects(RDF.type, OWL.TransitiveProperty):
            if p in no_trans:
                self.skip("transitive property excluded by --no-transitive", p)
            else:
                self.add("prp-trp", [(X, p, "?y"), ("?y", p, "?z")], [(X, p, "?z")])
        for p, chain in g.subject_objects(OWL.propertyChainAxiom):
            try:
                steps = [self.prop(s) for s in self.lst(chain)]
            except Unsupported as e:
                self.skip(str(e), f"{p} propertyChainAxiom")
                continue
            vs = [X] + [f"?c{i}" for i in range(1, len(steps))] + ["?y"]
            body = [self.triple(vs[i], s, vs[i + 1]) for i, s in enumerate(steps)]
            self.add("prp-spo2", body, [(X, p, "?y")])
        # consistency checks
        if not args.no_checks:
            pairs = set()
            for a, b in g.subject_objects(OWL.disjointWith):
                pairs.add((a, b))
            for d in g.subjects(RDF.type, OWL.AllDisjointClasses):
                ms = self.lst(g.value(d, OWL.members))
                pairs |= {(a, b) for i, a in enumerate(ms) for b in ms[i + 1:]}
            for a, b in g.subject_objects(OWL.complementOf):
                pairs.add((a, b))
            for a, b in sorted(pairs):
                if isinstance(a, URIRef) and isinstance(b, URIRef):
                    self.add("cax-dw", [(X, RDF.type, a), (X, RDF.type, b)],
                             [(X, VIOLATES, Literal(f"disjoint classes {a} {b}"))])
                else:
                    self.skip("disjointness with a class expression", (a, b))
            for p in g.subjects(RDF.type, OWL.AsymmetricProperty):
                self.add("prp-asyp", [(X, p, "?y"), ("?y", p, X)],
                         [(X, VIOLATES, Literal(f"asymmetric property {p}"))])
            for p in g.subjects(RDF.type, OWL.IrreflexiveProperty):
                self.add("prp-irp", [(X, p, X)], [(X, VIOLATES, Literal(f"irreflexive property {p}"))])
        # sameAs
        if args.sameas:
            for p in g.subjects(RDF.type, OWL.FunctionalProperty):
                self.add("prp-fp", [("?z", p, X), ("?z", p, "?y"), ("notEqual", X, "?y")], [(X, OWL.sameAs, "?y")])
            for p in g.subjects(RDF.type, OWL.InverseFunctionalProperty):
                self.add("prp-ifp", [(X, p, "?z"), ("?y", p, "?z"), ("notEqual", X, "?y")], [(X, OWL.sameAs, "?y")])
            for c, keys in g.subject_objects(OWL.hasKey):
                ks = self.lst(keys)
                body = [(X, RDF.type, c), ("?y", RDF.type, c)]
                for i, k in enumerate(ks):
                    body += [(X, k, f"?k{i}"), ("?y", k, f"?k{i}")]
                self.add("prp-key", body + [("notEqual", X, "?y")], [(X, OWL.sameAs, "?y")])
            self.add("eq-sym", [(X, OWL.sameAs, "?y")], [("?y", OWL.sameAs, X)])
            self.add("eq-trans", [(X, OWL.sameAs, "?y"), ("?y", OWL.sameAs, "?z")], [(X, OWL.sameAs, "?z")])
            self.add("eq-rep-s", [(X, OWL.sameAs, "?y"), (X, "?p", "?o")], [("?y", "?p", "?o")])
            self.add("eq-rep-o", [(X, OWL.sameAs, "?y"), ("?s", "?p", X)], [("?s", "?p", "?y")])
        else:
            for t in (OWL.FunctionalProperty, OWL.InverseFunctionalProperty):
                for p in g.subjects(RDF.type, t):
                    self.skip("owl:sameAs inference (enable with --sameas)", p)
            for c in g.subjects(OWL.hasKey):
                self.skip("owl:sameAs inference (enable with --sameas)", f"{c} hasKey")
        # dedup, keeping the first occurrence
        seen, out = set(), []
        for r in self.rules:
            key = (tuple(r[1]), tuple(r[2]))
            if key not in seen:
                seen.add(key)
                out.append(r)
        self.rules = out
        return self

    # ------------------------------------------------------------- schema closure
    def schema_closure(self):
        """Sub-class / sub-property closure as triples, for queries over the schema."""
        g = self.g
        out = Graph()

        def closure(pred, eq):
            up = defaultdict(set)
            for s, o in g.subject_objects(pred):
                if isinstance(s, URIRef) and isinstance(o, URIRef):
                    up[s].add(o)
            for s, o in g.subject_objects(eq):
                if isinstance(s, URIRef) and isinstance(o, URIRef):
                    up[s].add(o)
                    up[o].add(s)
            for s in list(up):
                seen, todo = set(), list(up[s])
                while todo:
                    c = todo.pop()
                    if c not in seen:
                        seen.add(c)
                        todo += up.get(c, ())
                for c in seen:
                    if c != s:
                        out.add((s, pred, c))
        closure(RDFS.subClassOf, OWL.equivalentClass)
        closure(RDFS.subPropertyOf, OWL.equivalentProperty)
        return out


# --------------------------------------------------------------- serialisation
def node(t):
    if isinstance(t, str) and t.startswith("?"):
        return t
    if isinstance(t, URIRef):
        return f"<{t}>"
    if isinstance(t, Literal):
        lex = str(t).replace("\\", "\\\\").replace("'", "\\'")
        if t.language:
            return f"'{lex}'@{t.language}"
        if t.datatype:
            dt = str(t.datatype)
            dt = "xsd:" + dt[len(str(XSD)):] if dt.startswith(str(XSD)) else f"<{dt}>"
            return f"'{lex}'^^{dt}"
        return f"'{lex}'"
    raise ValueError(f"cannot write {t!r} in a rule")


def clause(t):
    if t[0] == "notEqual":
        return f"notEqual({t[1]}, {t[2]})"
    return f"({node(t[0])} {node(t[1])} {node(t[2])})"


def write_rules(rules, path, header):
    lines = [f"# {l}" if l else "#" for l in header] + ["", f"@prefix xsd: <{XSD}>.", ""]
    for i, (kind, body, head) in enumerate(rules, 1):
        lines.append(f"[{kind}-{i}: " + " ".join(clause(b) for b in body) + " -> "
                     + " ".join(clause(h) for h in head) + "]")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ontology", nargs="+", type=Path, help="schema files (Turtle, or RDF/XML for .owl/.rdf)")
    ap.add_argument("-o", "--output", required=True, help="rules file to write")
    ap.add_argument("--no-transitive", nargs="*", default=[], metavar="PROP",
                    help="do not compile transitivity for these properties (full IRIs or dul:/owl: prefixed)")
    ap.add_argument("--no-symmetric", nargs="*", default=[], metavar="PROP")
    ap.add_argument("--sameas", action="store_true", help="also compile the owl:sameAs rules")
    ap.add_argument("--no-checks", action="store_true", help="do not compile the consistency-check rules")
    ap.add_argument("--schema-closure", help="also write the sub-class / sub-property closure to this Turtle file")
    ap.add_argument("--report", help="write a Markdown report of what was compiled and skipped")
    args = ap.parse_args()

    g = load(args.ontology)
    c = Compiler(g, args).compile()
    kinds = Counter(k for k, _, _ in c.rules)
    header = ["Jena rule profile compiled by compile_rules.py from:"]
    header += [f"  {f.name}" for f in args.ontology]
    header += [f"{len(c.rules)} rules: " + ", ".join(f"{k} {n}" for k, n in sorted(kinds.items()))]
    write_rules(c.rules, args.output, header)
    print(f"{len(g):,} schema triples -> {len(c.rules):,} rules in {args.output}")
    for k, n in sorted(kinds.items()):
        print(f"  {k:<10} {n:>6}")
    if c.skipped:
        print("Skipped:")
        for why, n in c.skipped.most_common():
            print(f"  {n:>5}  {why}")
    if args.schema_closure:
        sc = c.schema_closure()
        sc.serialize(args.schema_closure, format="turtle")
        print(f"{len(sc):,} schema-closure triples in {args.schema_closure}")
    if args.report:
        md = ["# Compiled rule profile\n", f"Rules file: `{args.output}` · {len(c.rules)} rules\n",
              "| Rule type | Rules |", "|---|---|"] + [f"| {k} | {n} |" for k, n in sorted(kinds.items())]
        md += ["\n## Skipped axioms\n", "| Reason | Axioms | Examples |", "|---|---|---|"]
        for why, n in c.skipped.most_common():
            ex = "; ".join(str(e)[:120] for e in c.skipped_examples[why])
            md.append(f"| {why} | {n} | {ex.replace('|', '/')} |")
        Path(args.report).write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
