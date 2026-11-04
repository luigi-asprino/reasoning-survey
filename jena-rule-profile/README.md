# A Jena rule profile compiled from the ontology

Jena's built-in OWL reasoners (`owl-micro`, `owl-mini`, `owl`) fail on ECMO +
DUL: they run out of memory or don't finish (see the
[Fuseki loading-time findings](../loading-time-test/fuseki/README.md#findings-so-far)).
They reason over the schema and the data together, with a mix of forward and
backward rules, at query time.

This folder takes the approach GraphDB's `-optimized` rulesets take, pushed
one step further: the ontology is compiled once into a set of **forward rules
specialised to its axioms**, one rule per axiom with the classes and
properties filled in (examples from the test KG, prefixes shortened):

```
ex:teaches rdfs:domain ex:Academic
  ->  [prp-dom-26: (?x ex:teaches ?y) -> (?x rdf:type ex:Academic)]

ex:Supervisor owl:equivalentClass [ owl:onProperty ex:supervises ; owl:someValuesFrom ex:PhDStudent ]
  ->  [cax-15: (?x ex:supervises ?v) (?v rdf:type ex:PhDStudent) -> (?x rdf:type ex:Supervisor)]
```

Jena's `GenericRuleReasoner` runs these with its RETE engine and materialises
the inferences when the data is loaded, so queries just read them. The rules
only fire on instance data; the schema is never reasoned over at run time.

## What the profile covers

The OWL 2 RL rules that apply to the constructs in the ontology:

| Group | Constructs | OWL 2 RL rules |
|---|---|---|
| Properties | subPropertyOf, equivalentProperty, inverseOf, domain, range, symmetric, transitive, propertyChainAxiom | prp-spo1, prp-eqp, prp-inv, prp-dom, prp-rng, prp-symp, prp-trp, prp-spo2 |
| Classes | subClassOf / equivalentClass between expressions built from named classes, intersectionOf, unionOf (sub-class side), someValuesFrom (sub-class side), hasValue, allValuesFrom (super-class side) | cax-sco, cax-eqc, cls-int1/2, cls-uni, cls-svf1/2, cls-hv1/2, cls-avf |
| Consistency | disjointWith, AllDisjointClasses, complementOf (named classes), asymmetric and irreflexive properties | cax-dw, prp-asyp, prp-irp |
| sameAs (`--sameas`) | functional and inverse-functional properties, hasKey, owl:sameAs symmetry, transitivity, replacement | prp-fp, prp-ifp, prp-key, eq-sym, eq-trans, eq-rep-s/o |

A violated consistency check is written as a triple
`?x <urn:jena-profile#violates> "disjoint classes A B"`, so it can be found
with SPARQL from the endpoint (Jena's `validate()` is not exposed by Fuseki):

```sparql
SELECT ?x ?why WHERE { ?x <urn:jena-profile#violates> ?why }
```

Left out, as in OWL 2 RL: existentials, unions and cardinalities on the
super-class side (they would create new individuals or need case analysis),
`oneOf`, and datatype reasoning. The compiler lists every skipped axiom
with the reason (`--report`).

Options to keep the closure small:

- `--no-transitive PROP…`, `--no-symmetric PROP…` drop transitivity or symmetry
  (including a self-inverse declaration) for the given properties. With the
  original DUL, `--no-transitive dul:associatedWith --no-symmetric dul:associatedWith`
  gives exactly the same inferences as DUL-lite, without editing DUL.
- `owl:sameAs` rules are off by default, as in the GraphDB benchmark settings.
  ECMO has 3.7k `owl:sameAs` links, and the replacement rules copy every
  statement across each sameAs clique (about 2.5× the inferences on ECMO).

The rules are derived from the schema, so **regenerate them whenever the
ontology changes**. Instance data can be added and removed freely.

## Contents

| Path | Description |
|---|---|
| `code/compile_rules.py` | Compiles ontology files into a Jena rules file (needs rdflib). |
| `code/check_rules.py` | Dry run without Jena: compiles the rules, applies them with a small Python forward chainer, reports inferences per predicate and violated checks; `--closure` writes the materialised graph as N-Triples. |
| `rules/ecmo-0.3.1_dul-lite.rules` (+ `.md`) | Profile for ECMO 0.3.1 + DUL-lite + d0, without sameAs; the report lists what was skipped. |
| `rules/ecmo-0.3.1_dul-lite_sameas.rules` (+ `.md`) | Same, with the sameAs rules. |
| `results/check_*.txt` | Output of `check_rules.py` on ECMO + DUL-lite + d0, with and without the case fixtures. |

## Results of the dry run (Python, before trying Jena)

ECMO 0.3.1 + DUL-lite + d0 (41.6k triples): 2,643 rules (2,656 with sameAs).

| Workload | Explicit | Inferred | GraphDB owl2-rl (setting 3) |
|---|---|---|---|
| ontology only | 41,632 | 68,291 | 220,138 inferred in 47 s |
| + 4 case fixtures | 43,082 | 73,969 | – |
| + 4 case fixtures, with sameAs | 43,082 | 185,541 | – |

The plain Python forward chainer computes these in 30–80 s; Jena's RETE engine
should be faster (see the benchmark below). The closure is smaller than
GraphDB's because GraphDB also materialises schema-level triples (sub-class and
sub-property closure, `owl:Thing` types, reflexive axioms); `compile_rules.py
--schema-closure FILE` writes the sub-class / sub-property closure if queries
need it.

On the four case fixtures, the profile reports two individuals that are both a
`dul:Event` and a `dul:Object` (`EWS_Warning_16Apr`, `CruiseShipHantavirusEvent`).

On the test KG (`university.ttl`), the profile with `--sameas` returns the same
answers as GraphDB `owl2-rl` on Q1–Q9, including property chains and keys,
apart from vocabulary-level types (`owl:Thing`) and reflexive `owl:sameAs`.

## Usage

```bash
# compile (options after the files)
python code/compile_rules.py ONTO1.ttl ONTO2.ttl ... -o my.rules --report my.md
python code/compile_rules.py DUL.owl d0.owl ecmo/*.ttl -o ecmo.rules \
       --no-transitive dul:associatedWith --no-symmetric dul:associatedWith

# dry run
python code/check_rules.py --ontology DUL-lite.ttl d0.owl ecmo/*.ttl --data case.ttl
```

### In Fuseki

```turtle
PREFIX fuseki: <http://jena.apache.org/fuseki#>
PREFIX ja:     <http://jena.hpl.hp.com/2005/11/Assembler#>
PREFIX tdb2:   <http://jena.apache.org/2016/tdb#>

<#service> a fuseki:Service ;
    fuseki:name "ecmo" ;
    fuseki:endpoint [ fuseki:operation fuseki:query ; fuseki:name "sparql" ] ;
    fuseki:endpoint [ fuseki:operation fuseki:update ; fuseki:name "update" ] ;
    fuseki:dataset <#dataset> .

<#dataset> a ja:RDFDataset ;
    ja:defaultGraph <#inf> .

<#inf> a ja:InfModel ;
    ja:baseModel <#tdbGraph> ;          # or an in-memory ja:MemoryModel with ja:content
    ja:reasoner [
        ja:reasonerURL <http://jena.hpl.hp.com/2003/GenericRuleReasoner> ;
        ja:rulesFrom <file:///path/to/jena-rule-profile/rules/ecmo-0.3.1_dul-lite.rules>
    ] .

<#tdbGraph> a tdb2:GraphTDB2 ;
    tdb2:dataset [ a tdb2:DatasetTDB2 ; tdb2:location "/path/to/tdb2-ecmo" ] .
```

The explicit data stays in TDB2; the inferences are kept in memory and
recomputed when Fuseki starts. Load the ontology (with DUL-lite and d0) and the
data into the same graph. An alternative that needs no reasoner at run time is
to materialise once (`check_rules.py --closure`, or the Jena benchmark) and load
the result into a plain TDB2 dataset.

### Testing it with the existing harnesses

```bash
# query suite on the test KG, alongside the built-in reasoners
python ../reasoning-capability-test/fuseki/code/run_fuseki_tests.py --fuseki <fuseki-dir>/fuseki-server

# loading time on ECMO + DUL-lite (settings 3 and 4)
python ../loading-time-test/fuseki/code/benchmark_reasoners.py --ecmo-workload --no-data --dul-lite \
       --reasoners none rdfs compiled
python ../loading-time-test/fuseki/code/benchmark_reasoners.py --ecmo-workload --no-data --dul-lite \
       --reasoners compiled --consistency

# full DUL, dropping associatedWith transitivity and symmetry in the profile
python ../loading-time-test/fuseki/code/benchmark_reasoners.py --ecmo-workload --no-data --dul \
       --reasoners compiled --profile-args="--no-transitive dul:associatedWith --no-symmetric dul:associatedWith"
```
