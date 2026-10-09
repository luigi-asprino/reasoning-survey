# GraphDB reasoning report

Endpoint: `http://localhost:7200` · infer=True

| Repository | Ruleset |
|---|---|
| reasoning-test-owl-max | owl-max-optimized (disableSameAs=false) |
| reasoning-test-owl2-ql-opt | owl2-ql-optimized (disableSameAs=false) |
| reasoning-test-rdfs-plus-opt | rdfsplus-optimized (disableSameAs=false) |
| reasoning-test-rl-opt | owl2-rl-optimized (disableSameAs=false) |

## Q1 — [RDFS] types of alice (domain + subClassOf)

```sparql
SELECT ?t WHERE { ex:alice a ?t }
```

| Repository | #rows | Result |
|---|---|---|
| reasoning-test-owl-max | 6 | _:b, ex:Academic, ex:Docente, ex:Person, ex:Staff, ex:Supervisor |
| reasoning-test-owl2-ql-opt | 4 | ex:Academic, ex:Docente, ex:Person, owl:Thing |
| reasoning-test-rdfs-plus-opt | 0 | ∅ |
| reasoning-test-rl-opt | 7 | _:b, ex:Academic, ex:Docente, ex:Person, ex:Staff, ex:Supervisor, owl:Thing |

- **reasoning-test-owl-max** missing: owl:Thing
- **reasoning-test-owl2-ql-opt** missing: _:b, ex:Staff, ex:Supervisor
- **reasoning-test-rdfs-plus-opt** missing: _:b, ex:Academic, ex:Docente, ex:Person, ex:Staff, ex:Supervisor, owl:Thing

## Q2 — [RDFS] subPropertyOf + range -> kg101, kgLab (+ db201 via bruno in OWL-Horst)

```sparql
SELECT ?who ?c WHERE { ?who ex:teaches ?c . ?c a ex:Course }
```

| Repository | #rows | Result |
|---|---|---|
| reasoning-test-owl-max | 7 | (who=ex:a_rossi, c=ex:kg101); (who=ex:a_rossi, c=ex:kgLab); (who=ex:alice, c=ex:kg101); (who=ex:alice, c=ex:kgLab); (who=ex:bruno, c=ex:db201); (who=ex:profAlice, c=ex:kg101); (who=ex:profAlice, c=ex:kgLab) |
| reasoning-test-owl2-ql-opt | 3 | (who=ex:alice, c=ex:kg101); (who=ex:alice, c=ex:kgLab); (who=ex:bruno, c=ex:db201) |
| reasoning-test-rdfs-plus-opt | 0 | ∅ |
| reasoning-test-rl-opt | 7 | (who=ex:a_rossi, c=ex:kg101); (who=ex:a_rossi, c=ex:kgLab); (who=ex:alice, c=ex:kg101); (who=ex:alice, c=ex:kgLab); (who=ex:bruno, c=ex:db201); (who=ex:profAlice, c=ex:kg101); (who=ex:profAlice, c=ex:kgLab) |

- **reasoning-test-owl2-ql-opt** missing: (who=ex:a_rossi, c=ex:kg101); (who=ex:a_rossi, c=ex:kgLab); (who=ex:profAlice, c=ex:kg101); (who=ex:profAlice, c=ex:kgLab)
- **reasoning-test-rdfs-plus-opt** missing: (who=ex:a_rossi, c=ex:kg101); (who=ex:a_rossi, c=ex:kgLab); (who=ex:alice, c=ex:kg101); (who=ex:alice, c=ex:kgLab); (who=ex:bruno, c=ex:db201); (who=ex:profAlice, c=ex:kg101); (who=ex:profAlice, c=ex:kgLab)

## Q3 — [RDFS-Plus] inverse / symmetric / transitive

```sparql
SELECT * WHERE {
  { ex:carla ex:supervisedBy ?s }
  UNION { ex:bruno ex:collaboratesWith ?c }
  UNION { ex:kgGroup ex:partOf ?u }
}
```

| Repository | #rows | Result |
|---|---|---|
| reasoning-test-owl-max | 9 | (u=ex:dept); (u=ex:faculty); (u=ex:unibo); (c=ex:a_rossi); (c=ex:alice); (c=ex:profAlice); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice) |
| reasoning-test-owl2-ql-opt | 3 | (u=ex:dept); (c=ex:alice); (s=ex:alice) |
| reasoning-test-rdfs-plus-opt | 5 | (u=ex:dept); (u=ex:faculty); (u=ex:unibo); (c=ex:alice); (s=ex:alice) |
| reasoning-test-rl-opt | 9 | (u=ex:dept); (u=ex:faculty); (u=ex:unibo); (c=ex:a_rossi); (c=ex:alice); (c=ex:profAlice); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice) |

- **reasoning-test-owl2-ql-opt** missing: (u=ex:faculty); (u=ex:unibo); (c=ex:a_rossi); (c=ex:profAlice); (s=ex:a_rossi); (s=ex:profAlice)
- **reasoning-test-rdfs-plus-opt** missing: (c=ex:a_rossi); (c=ex:profAlice); (s=ex:a_rossi); (s=ex:profAlice)

## Q4 — [OWL-Horst] equivalentClass / equivalentProperty -> alice, bruno

```sparql
SELECT ?d WHERE { ?d a ex:Docente }
```

| Repository | #rows | Result |
|---|---|---|
| reasoning-test-owl-max | 4 | ex:a_rossi, ex:alice, ex:bruno, ex:profAlice |
| reasoning-test-owl2-ql-opt | 2 | ex:alice, ex:bruno |
| reasoning-test-rdfs-plus-opt | 0 | ∅ |
| reasoning-test-rl-opt | 4 | ex:a_rossi, ex:alice, ex:bruno, ex:profAlice |

- **reasoning-test-owl2-ql-opt** missing: ex:a_rossi, ex:profAlice
- **reasoning-test-rdfs-plus-opt** missing: ex:a_rossi, ex:alice, ex:bruno, ex:profAlice

## Q5 — [OWL-Horst] sameAs from IFP (a_rossi) and FunctionalProperty (profAlice)

```sparql
SELECT ?same ?hp WHERE {
  ex:alice owl:sameAs ?same .
  OPTIONAL { ex:alice ex:homepage ?hp }
}
```

| Repository | #rows | Result |
|---|---|---|
| reasoning-test-owl-max | 3 | (same=ex:a_rossi, hp=<http://example.org/~arossi>); (same=ex:alice, hp=<http://example.org/~arossi>); (same=ex:profAlice, hp=<http://example.org/~arossi>) |
| reasoning-test-owl2-ql-opt | 0 | ∅ |
| reasoning-test-rdfs-plus-opt | 0 | ∅ |
| reasoning-test-rl-opt | 3 | (same=ex:a_rossi, hp=<http://example.org/~arossi>); (same=ex:alice, hp=<http://example.org/~arossi>); (same=ex:profAlice, hp=<http://example.org/~arossi>) |

- **reasoning-test-owl2-ql-opt** missing: (same=ex:a_rossi, hp=<http://example.org/~arossi>); (same=ex:alice, hp=<http://example.org/~arossi>); (same=ex:profAlice, hp=<http://example.org/~arossi>)
- **reasoning-test-rdfs-plus-opt** missing: (same=ex:a_rossi, hp=<http://example.org/~arossi>); (same=ex:alice, hp=<http://example.org/~arossi>); (same=ex:profAlice, hp=<http://example.org/~arossi>)

## Q6 — [OWL-Horst] hasValue (both directions), someValuesFrom, allValuesFrom

```sparql
SELECT * WHERE {
  { ?c1 a ex:SemanticWebCourse }
  UNION { ex:sw301 ex:hasTopic ?topic }
  UNION { ?s a ex:Supervisor }
  UNION { ?r a ex:Researcher }
}
```

| Repository | #rows | Result |
|---|---|---|
| reasoning-test-owl-max | 7 | (r=ex:elena); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice); (topic=ex:SemanticWeb); (c1=ex:kg101); (c1=ex:sw301) |
| reasoning-test-owl2-ql-opt | 1 | (c1=ex:sw301) |
| reasoning-test-rdfs-plus-opt | 1 | (c1=ex:sw301) |
| reasoning-test-rl-opt | 7 | (r=ex:elena); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice); (topic=ex:SemanticWeb); (c1=ex:kg101); (c1=ex:sw301) |

- **reasoning-test-owl2-ql-opt** missing: (r=ex:elena); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice); (topic=ex:SemanticWeb); (c1=ex:kg101)
- **reasoning-test-rdfs-plus-opt** missing: (r=ex:elena); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice); (topic=ex:SemanticWeb); (c1=ex:kg101)

## Q7 — [OWL2-RL] intersection (both directions) and union

```sparql
SELECT * WHERE {
  { ?ws a ex:WorkingStudent }
  UNION { ex:giulia a ?gt }
  UNION { ?st a ex:Staff }
}
```

| Repository | #rows | Result |
|---|---|---|
| reasoning-test-owl-max | 12 | (st=ex:a_rossi); (st=ex:alice); (st=ex:bruno); (st=ex:hugo); (st=ex:profAlice); (gt=_:b); (gt=ex:Employee); (gt=ex:Person); (gt=ex:Student); (gt=ex:WorkingStudent); (ws=ex:franco); (ws=ex:giulia) |
| reasoning-test-owl2-ql-opt | 8 | (gt=_:b); (gt=ex:Employee); (gt=ex:Person); (gt=ex:Student); (gt=ex:WorkingStudent); (gt=owl:Thing); (ws=ex:franco); (ws=ex:giulia) |
| reasoning-test-rdfs-plus-opt | 3 | (gt=_:b); (gt=ex:WorkingStudent); (ws=ex:giulia) |
| reasoning-test-rl-opt | 13 | (st=ex:a_rossi); (st=ex:alice); (st=ex:bruno); (st=ex:hugo); (st=ex:profAlice); (gt=_:b); (gt=ex:Employee); (gt=ex:Person); (gt=ex:Student); (gt=ex:WorkingStudent); (gt=owl:Thing); (ws=ex:franco); (ws=ex:giulia) |

- **reasoning-test-owl-max** missing: (gt=owl:Thing)
- **reasoning-test-owl2-ql-opt** missing: (st=ex:a_rossi); (st=ex:alice); (st=ex:bruno); (st=ex:hugo); (st=ex:profAlice)
- **reasoning-test-rdfs-plus-opt** missing: (st=ex:a_rossi); (st=ex:alice); (st=ex:bruno); (st=ex:hugo); (st=ex:profAlice); (gt=ex:Employee); (gt=ex:Person); (gt=ex:Student); (gt=owl:Thing); (ws=ex:franco)

## Q8 — [OWL2-RL] property chain -> kgGroup, dept, faculty, unibo

```sparql
SELECT ?org WHERE { ex:alice ex:affiliatedWith ?org }
```

| Repository | #rows | Result |
|---|---|---|
| reasoning-test-owl-max | 1 | ex:kgGroup |
| reasoning-test-owl2-ql-opt | 1 | ex:kgGroup |
| reasoning-test-rdfs-plus-opt | 1 | ex:kgGroup |
| reasoning-test-rl-opt | 4 | ex:dept, ex:faculty, ex:kgGroup, ex:unibo |

- **reasoning-test-owl-max** missing: ex:dept, ex:faculty, ex:unibo
- **reasoning-test-owl2-ql-opt** missing: ex:dept, ex:faculty, ex:unibo
- **reasoning-test-rdfs-plus-opt** missing: ex:dept, ex:faculty, ex:unibo

## Q9 — [OWL2-RL] hasKey -> dario owl:sameAs d_verdi ; dario hIndex 13

```sparql
SELECT ?x ?h WHERE { ex:dario owl:sameAs ?x . OPTIONAL { ex:dario ex:hIndex ?h } }
```

| Repository | #rows | Result |
|---|---|---|
| reasoning-test-owl-max | 0 | ∅ |
| reasoning-test-owl2-ql-opt | 0 | ∅ |
| reasoning-test-rdfs-plus-opt | 0 | ∅ |
| reasoning-test-rl-opt | 2 | (x=ex:d_verdi, h="13"); (x=ex:dario, h="13") |

- **reasoning-test-owl-max** missing: (x=ex:d_verdi, h="13"); (x=ex:dario, h="13")
- **reasoning-test-owl2-ql-opt** missing: (x=ex:d_verdi, h="13"); (x=ex:dario, h="13")
- **reasoning-test-rdfs-plus-opt** missing: (x=ex:d_verdi, h="13"); (x=ex:dario, h="13")

## Q10 — inferred-only statements (GraphDB pseudo-graph); swap for

```sparql
SELECT (COUNT(*) AS ?n) FROM onto:implicit WHERE { ?s ?p ?o }
```

| Repository | #rows | Result |
|---|---|---|
| reasoning-test-owl-max | 1 | "361" |
| reasoning-test-owl2-ql-opt | 1 | "1596" |
| reasoning-test-rdfs-plus-opt | 1 | "193" |
| reasoning-test-rl-opt | 1 | "1263" |

- **reasoning-test-owl-max** missing: "1263", "1596", "193"
- **reasoning-test-owl2-ql-opt** missing: "1263", "193", "361"
- **reasoning-test-rdfs-plus-opt** missing: "1263", "1596", "361"
- **reasoning-test-rl-opt** missing: "1596", "193", "361"
