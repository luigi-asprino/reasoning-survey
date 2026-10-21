# Fuseki reasoning report

Endpoint: `http://localhost:3030` · data: `university.ttl`

| Dataset | Reasoner |
|---|---|
| none | – |
| transitive | http://jena.hpl.hp.com/2003/TransitiveReasoner |
| rdfs | http://jena.hpl.hp.com/2003/RDFSExptRuleReasoner |
| owl-micro | http://jena.hpl.hp.com/2003/OWLMicroFBRuleReasoner |
| owl-mini | http://jena.hpl.hp.com/2003/OWLMiniFBRuleReasoner |
| owl | http://jena.hpl.hp.com/2003/OWLFBRuleReasoner |

## Q1 — [RDFS] types of alice (domain + subClassOf)

```sparql
SELECT ?t WHERE { ex:alice a ?t }
```

| Dataset | #rows | Time (s) | Result |
|---|---|---|---|
| none | 0 | 0.03 | ∅ |
| transitive | 0 | 0.01 | ∅ |
| rdfs | 3 | 0.01 | ex:Academic, ex:Person, rdfs:Resource |
| owl-micro | 8 | 0.04 | _:b, ex:Academic, ex:Docente, ex:Person, ex:Staff, ex:Supervisor, owl:Thing, rdfs:Resource |
| owl-mini | 8 | 0.33 | _:b, ex:Academic, ex:Docente, ex:Person, ex:Staff, ex:Supervisor, owl:Thing, rdfs:Resource |
| owl | 8 | 0.35 | _:b, ex:Academic, ex:Docente, ex:Person, ex:Staff, ex:Supervisor, owl:Thing, rdfs:Resource |

- **none** missing: _:b, ex:Academic, ex:Docente, ex:Person, ex:Staff, ex:Supervisor, owl:Thing, rdfs:Resource
- **transitive** missing: _:b, ex:Academic, ex:Docente, ex:Person, ex:Staff, ex:Supervisor, owl:Thing, rdfs:Resource
- **rdfs** missing: _:b, ex:Docente, ex:Staff, ex:Supervisor, owl:Thing

## Q2 — [RDFS] subPropertyOf + range -> kg101, kgLab (+ db201 via bruno in OWL-Horst)

```sparql
SELECT ?who ?c WHERE { ?who ex:teaches ?c . ?c a ex:Course }
```

| Dataset | #rows | Time (s) | Result |
|---|---|---|---|
| none | 0 | 0.01 | ∅ |
| transitive | 0 | 0.01 | ∅ |
| rdfs | 2 | 0.01 | (who=ex:alice, c=ex:kg101); (who=ex:alice, c=ex:kgLab) |
| owl-micro | 3 | 0.04 | (who=ex:alice, c=ex:kg101); (who=ex:alice, c=ex:kgLab); (who=ex:bruno, c=ex:db201) |
| owl-mini | 7 | 0.03 | (who=ex:a_rossi, c=ex:kg101); (who=ex:a_rossi, c=ex:kgLab); (who=ex:alice, c=ex:kg101); (who=ex:alice, c=ex:kgLab); (who=ex:bruno, c=ex:db201); (who=ex:profAlice, c=ex:kg101); (who=ex:profAlice, c=ex:kgLab) |
| owl | 7 | 0.01 | (who=ex:a_rossi, c=ex:kg101); (who=ex:a_rossi, c=ex:kgLab); (who=ex:alice, c=ex:kg101); (who=ex:alice, c=ex:kgLab); (who=ex:bruno, c=ex:db201); (who=ex:profAlice, c=ex:kg101); (who=ex:profAlice, c=ex:kgLab) |

- **none** missing: (who=ex:a_rossi, c=ex:kg101); (who=ex:a_rossi, c=ex:kgLab); (who=ex:alice, c=ex:kg101); (who=ex:alice, c=ex:kgLab); (who=ex:bruno, c=ex:db201); (who=ex:profAlice, c=ex:kg101); (who=ex:profAlice, c=ex:kgLab)
- **transitive** missing: (who=ex:a_rossi, c=ex:kg101); (who=ex:a_rossi, c=ex:kgLab); (who=ex:alice, c=ex:kg101); (who=ex:alice, c=ex:kgLab); (who=ex:bruno, c=ex:db201); (who=ex:profAlice, c=ex:kg101); (who=ex:profAlice, c=ex:kgLab)
- **rdfs** missing: (who=ex:a_rossi, c=ex:kg101); (who=ex:a_rossi, c=ex:kgLab); (who=ex:bruno, c=ex:db201); (who=ex:profAlice, c=ex:kg101); (who=ex:profAlice, c=ex:kgLab)
- **owl-micro** missing: (who=ex:a_rossi, c=ex:kg101); (who=ex:a_rossi, c=ex:kgLab); (who=ex:profAlice, c=ex:kg101); (who=ex:profAlice, c=ex:kgLab)

## Q3 — [RDFS-Plus] inverse / symmetric / transitive

```sparql
SELECT * WHERE {
  { ex:carla ex:supervisedBy ?s }
  UNION { ex:bruno ex:collaboratesWith ?c }
  UNION { ex:kgGroup ex:partOf ?u }
}
```

| Dataset | #rows | Time (s) | Result |
|---|---|---|---|
| none | 1 | 0.01 | (u=ex:dept) |
| transitive | 1 | 0.01 | (u=ex:dept) |
| rdfs | 1 | 0.01 | (u=ex:dept) |
| owl-micro | 5 | 0.01 | (u=ex:dept); (u=ex:faculty); (u=ex:unibo); (c=ex:alice); (s=ex:alice) |
| owl-mini | 9 | 0.01 | (u=ex:dept); (u=ex:faculty); (u=ex:unibo); (c=ex:a_rossi); (c=ex:alice); (c=ex:profAlice); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice) |
| owl | 9 | 0.01 | (u=ex:dept); (u=ex:faculty); (u=ex:unibo); (c=ex:a_rossi); (c=ex:alice); (c=ex:profAlice); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice) |

- **none** missing: (u=ex:faculty); (u=ex:unibo); (c=ex:a_rossi); (c=ex:alice); (c=ex:profAlice); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice)
- **transitive** missing: (u=ex:faculty); (u=ex:unibo); (c=ex:a_rossi); (c=ex:alice); (c=ex:profAlice); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice)
- **rdfs** missing: (u=ex:faculty); (u=ex:unibo); (c=ex:a_rossi); (c=ex:alice); (c=ex:profAlice); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice)
- **owl-micro** missing: (c=ex:a_rossi); (c=ex:profAlice); (s=ex:a_rossi); (s=ex:profAlice)

## Q4 — [OWL-Horst] equivalentClass / equivalentProperty -> alice, bruno

```sparql
SELECT ?d WHERE { ?d a ex:Docente }
```

| Dataset | #rows | Time (s) | Result |
|---|---|---|---|
| none | 0 | 0.01 | ∅ |
| transitive | 0 | 0.01 | ∅ |
| rdfs | 0 | 0.01 | ∅ |
| owl-micro | 2 | 0.01 | ex:alice, ex:bruno |
| owl-mini | 4 | 0.01 | ex:a_rossi, ex:alice, ex:bruno, ex:profAlice |
| owl | 4 | 0.01 | ex:a_rossi, ex:alice, ex:bruno, ex:profAlice |

- **none** missing: ex:a_rossi, ex:alice, ex:bruno, ex:profAlice
- **transitive** missing: ex:a_rossi, ex:alice, ex:bruno, ex:profAlice
- **rdfs** missing: ex:a_rossi, ex:alice, ex:bruno, ex:profAlice
- **owl-micro** missing: ex:a_rossi, ex:profAlice

## Q5 — [OWL-Horst] sameAs from IFP (a_rossi) and FunctionalProperty (profAlice)

```sparql
SELECT ?same ?hp WHERE {
  ex:alice owl:sameAs ?same .
  OPTIONAL { ex:alice ex:homepage ?hp }
}
```

| Dataset | #rows | Time (s) | Result |
|---|---|---|---|
| none | 0 | 0.01 | ∅ |
| transitive | 0 | 0.01 | ∅ |
| rdfs | 0 | 0.01 | ∅ |
| owl-micro | 0 | 0.01 | ∅ |
| owl-mini | 3 | 0.01 | (same=ex:a_rossi, hp=<http://example.org/~arossi>); (same=ex:alice, hp=<http://example.org/~arossi>); (same=ex:profAlice, hp=<http://example.org/~arossi>) |
| owl | 3 | 0.01 | (same=ex:a_rossi, hp=<http://example.org/~arossi>); (same=ex:alice, hp=<http://example.org/~arossi>); (same=ex:profAlice, hp=<http://example.org/~arossi>) |

- **none** missing: (same=ex:a_rossi, hp=<http://example.org/~arossi>); (same=ex:alice, hp=<http://example.org/~arossi>); (same=ex:profAlice, hp=<http://example.org/~arossi>)
- **transitive** missing: (same=ex:a_rossi, hp=<http://example.org/~arossi>); (same=ex:alice, hp=<http://example.org/~arossi>); (same=ex:profAlice, hp=<http://example.org/~arossi>)
- **rdfs** missing: (same=ex:a_rossi, hp=<http://example.org/~arossi>); (same=ex:alice, hp=<http://example.org/~arossi>); (same=ex:profAlice, hp=<http://example.org/~arossi>)
- **owl-micro** missing: (same=ex:a_rossi, hp=<http://example.org/~arossi>); (same=ex:alice, hp=<http://example.org/~arossi>); (same=ex:profAlice, hp=<http://example.org/~arossi>)

## Q6 — [OWL-Horst] hasValue (both directions), someValuesFrom, allValuesFrom

```sparql
SELECT * WHERE {
  { ?c1 a ex:SemanticWebCourse }
  UNION { ex:sw301 ex:hasTopic ?topic }
  UNION { ?s a ex:Supervisor }
  UNION { ?r a ex:Researcher }
}
```

| Dataset | #rows | Time (s) | Result |
|---|---|---|---|
| none | 1 | 0.01 | (c1=ex:sw301) |
| transitive | 1 | 0.01 | (c1=ex:sw301) |
| rdfs | 1 | 0.01 | (c1=ex:sw301) |
| owl-micro | 4 | 0.01 | (s=ex:alice); (topic=ex:SemanticWeb); (c1=ex:kg101); (c1=ex:sw301) |
| owl-mini | 7 | 0.02 | (r=ex:elena); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice); (topic=ex:SemanticWeb); (c1=ex:kg101); (c1=ex:sw301) |
| owl | 7 | 0.02 | (r=ex:elena); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice); (topic=ex:SemanticWeb); (c1=ex:kg101); (c1=ex:sw301) |

- **none** missing: (r=ex:elena); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice); (topic=ex:SemanticWeb); (c1=ex:kg101)
- **transitive** missing: (r=ex:elena); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice); (topic=ex:SemanticWeb); (c1=ex:kg101)
- **rdfs** missing: (r=ex:elena); (s=ex:a_rossi); (s=ex:alice); (s=ex:profAlice); (topic=ex:SemanticWeb); (c1=ex:kg101)
- **owl-micro** missing: (r=ex:elena); (s=ex:a_rossi); (s=ex:profAlice)

## Q7 — [OWL2-RL] intersection (both directions) and union

```sparql
SELECT * WHERE {
  { ?ws a ex:WorkingStudent }
  UNION { ex:giulia a ?gt }
  UNION { ?st a ex:Staff }
}
```

| Dataset | #rows | Time (s) | Result |
|---|---|---|---|
| none | 2 | 0.01 | (gt=ex:WorkingStudent); (ws=ex:giulia) |
| transitive | 2 | 0.01 | (gt=ex:WorkingStudent); (ws=ex:giulia) |
| rdfs | 2 | 0.01 | (gt=ex:WorkingStudent); (ws=ex:giulia) |
| owl-micro | 12 | 0.01 | (st=ex:alice); (st=ex:bruno); (st=ex:hugo); (gt=_:b); (gt=ex:Employee); (gt=ex:Person); (gt=ex:Student); (gt=ex:WorkingStudent); (gt=owl:Thing); (gt=rdfs:Resource); (ws=ex:franco); (ws=ex:giulia) |
| owl-mini | 14 | 0.02 | (st=ex:a_rossi); (st=ex:alice); (st=ex:bruno); (st=ex:hugo); (st=ex:profAlice); (gt=_:b); (gt=ex:Employee); (gt=ex:Person); (gt=ex:Student); (gt=ex:WorkingStudent); (gt=owl:Thing); (gt=rdfs:Resource); (ws=ex:franco); (ws=ex:giulia) |
| owl | 14 | 0.02 | (st=ex:a_rossi); (st=ex:alice); (st=ex:bruno); (st=ex:hugo); (st=ex:profAlice); (gt=_:b); (gt=ex:Employee); (gt=ex:Person); (gt=ex:Student); (gt=ex:WorkingStudent); (gt=owl:Thing); (gt=rdfs:Resource); (ws=ex:franco); (ws=ex:giulia) |

- **none** missing: (st=ex:a_rossi); (st=ex:alice); (st=ex:bruno); (st=ex:hugo); (st=ex:profAlice); (gt=_:b); (gt=ex:Employee); (gt=ex:Person); (gt=ex:Student); (gt=owl:Thing); (gt=rdfs:Resource); (ws=ex:franco)
- **transitive** missing: (st=ex:a_rossi); (st=ex:alice); (st=ex:bruno); (st=ex:hugo); (st=ex:profAlice); (gt=_:b); (gt=ex:Employee); (gt=ex:Person); (gt=ex:Student); (gt=owl:Thing); (gt=rdfs:Resource); (ws=ex:franco)
- **rdfs** missing: (st=ex:a_rossi); (st=ex:alice); (st=ex:bruno); (st=ex:hugo); (st=ex:profAlice); (gt=_:b); (gt=ex:Employee); (gt=ex:Person); (gt=ex:Student); (gt=owl:Thing); (gt=rdfs:Resource); (ws=ex:franco)
- **owl-micro** missing: (st=ex:a_rossi); (st=ex:profAlice)

## Q8 — [OWL2-RL] property chain -> kgGroup, dept, faculty, unibo

```sparql
SELECT ?org WHERE { ex:alice ex:affiliatedWith ?org }
```

| Dataset | #rows | Time (s) | Result |
|---|---|---|---|
| none | 1 | 0.01 | ex:kgGroup |
| transitive | 1 | 0.01 | ex:kgGroup |
| rdfs | 1 | 0.01 | ex:kgGroup |
| owl-micro | 1 | 0.00 | ex:kgGroup |
| owl-mini | 1 | 0.01 | ex:kgGroup |
| owl | 1 | 0.01 | ex:kgGroup |


## Q9 — [OWL2-RL] hasKey -> dario owl:sameAs d_verdi ; dario hIndex 13

```sparql
SELECT ?x ?h WHERE { ex:dario owl:sameAs ?x . OPTIONAL { ex:dario ex:hIndex ?h } }
```

| Dataset | #rows | Time (s) | Result |
|---|---|---|---|
| none | 0 | 0.01 | ∅ |
| transitive | 0 | 0.01 | ∅ |
| rdfs | 0 | 0.01 | ∅ |
| owl-micro | 0 | 0.01 | ∅ |
| owl-mini | 1 | 0.02 | (x=ex:dario) |
| owl | 1 | 0.02 | (x=ex:dario) |

- **none** missing: (x=ex:dario)
- **transitive** missing: (x=ex:dario)
- **rdfs** missing: (x=ex:dario)
- **owl-micro** missing: (x=ex:dario)

The first query against each dataset includes the reasoner's start-up (rule engine preparation), so its time is not comparable with the others.
