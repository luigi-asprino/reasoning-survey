# Implicit triples: owl2-ql-optimized vs owl2-rl-optimized

Endpoint: `http://localhost:7200` · data: university.ttl · sameAs enabled

| Ruleset | Implicit triples |
|---|---|
| owl2-ql-optimized | 1557 |
| owl2-rl-optimized | 1210 |

## Implicit triples per predicate

| Predicate | owl2-ql-optimized | owl2-rl-optimized | owl2-ql-optimized − owl2-rl-optimized |
|---|---|---|---|
| rdf:type | 643 | 502 | 141 |
| rdfs:subClassOf | 367 | 157 | 210 |
| rdfs:domain | 138 | 114 | 24 |
| owl:sameAs | 0 | 212 | -212 |
| rdfs:range | 125 | 79 | 46 |
| rdfs:subPropertyOf | 90 | 51 | 39 |
| owl:equivalentClass | 100 | 25 | 75 |
| owl:equivalentProperty | 87 | 26 | 61 |
| ex:uni#affiliatedWith | 0 | 11 | -11 |
| ex:uni#insegna | 2 | 6 | -4 |
| ex:uni#teaches | 2 | 6 | -4 |
| ex:uni#collaboratesWith | 1 | 5 | -4 |
| ex:uni#supervisedBy | 1 | 3 | -2 |
| ex:uni#partOf | 0 | 3 | -3 |
| ex:uni#teachesLab | 0 | 2 | -2 |
| ex:uni#supervises | 0 | 2 | -2 |
| ex:uni#homepage | 0 | 2 | -2 |
| ex:uni#email | 0 | 1 | -1 |
| ex:uni#hIndex | 0 | 1 | -1 |
| ex:uni#hasMainSupervisor | 0 | 1 | -1 |
| ex:uni#hasTopic | 0 | 1 | -1 |
| owl:disjointWith | 1 | 0 | 1 |

## Implicit rdf:type triples per class

| Class | owl2-ql-optimized | owl2-rl-optimized | owl2-ql-optimized − owl2-rl-optimized |
|---|---|---|---|
| owl:Thing | 193 | 204 | -11 |
| rdfs:Class | 89 | 89 | 0 |
| rdf:Property | 86 | 90 | -4 |
| owl:ObjectProperty | 75 | 2 | 73 |
| owl:Class | 72 | 3 | 69 |
| rdfs:Datatype | 34 | 34 | 0 |
| owl:DataRange | 34 | 0 | 34 |
| owl:DatatypeProperty | 11 | 11 | 0 |
| owl:AnnotationProperty | 9 | 9 | 0 |
| ex:uni#Person | 6 | 9 | -3 |
| _:b | 4 | 10 | -6 |
| owl:OntologyProperty | 5 | 5 | 0 |
| ex:uni#OrgUnit | 4 | 4 | 0 |
| ex:uni#Course | 4 | 4 | 0 |
| ex:uni#Docente | 2 | 4 | -2 |
| ex:uni#Academic | 2 | 4 | -2 |
| ex:uni#Staff | 0 | 5 | -5 |
| ex:uni#Employee | 2 | 2 | 0 |
| ex:uni#Student | 2 | 2 | 0 |
| rdf:List | 2 | 2 | 0 |
| ex:uni#Supervisor | 0 | 3 | -3 |
| owl:SymmetricProperty | 3 | 0 | 3 |
| rdfs:ContainerMembershipProperty | 1 | 1 | 0 |
| ex:uni#WorkingStudent | 1 | 1 | 0 |
| rdf:ObjectProperty | 1 | 1 | 0 |
| rdfs:Resource | 1 | 1 | 0 |
| ex:uni#SemanticWebCourse | 0 | 1 | -1 |
| ex:uni#Researcher | 0 | 1 | -1 |

## Inferred only by owl2-ql-optimized (676 triples)

| Predicate | Triples |
|---|---|
| rdfs:subClassOf | 218 |
| rdf:type | 179 |
| owl:equivalentClass | 75 |
| owl:equivalentProperty | 61 |
| rdfs:range | 55 |
| rdfs:domain | 48 |
| rdfs:subPropertyOf | 39 |
| owl:disjointWith | 1 |

**rdfs:subClassOf**, examples:

```
rdf:Alt rdfs:subClassOf rdf:Alt
rdf:Alt rdfs:subClassOf owl:Thing
rdf:Bag rdfs:subClassOf rdf:Bag
rdf:Bag rdfs:subClassOf owl:Thing
rdf:List rdfs:subClassOf rdf:List
```

**rdf:type**, examples:

```
ex:uni#hIndex rdf:type owl:ObjectProperty
ex:uni#homepage rdf:type owl:ObjectProperty
ex:uni#orcid rdf:type owl:ObjectProperty
rdf:Alt rdf:type owl:Class
rdf:Bag rdf:type owl:Class
```

**owl:equivalentClass**, examples:

```
rdf:Alt owl:equivalentClass rdf:Alt
rdf:Bag owl:equivalentClass rdf:Bag
rdf:List owl:equivalentClass rdf:List
rdf:PlainLiteral owl:equivalentClass rdf:PlainLiteral
rdf:Property owl:equivalentClass rdf:Property
```

**owl:equivalentProperty**, examples:

```
ex:uni#hIndex owl:equivalentProperty ex:uni#hIndex
ex:uni#homepage owl:equivalentProperty ex:uni#homepage
rdf:_1 owl:equivalentProperty rdf:_1
rdf:first owl:equivalentProperty rdf:first
rdf:object owl:equivalentProperty rdf:object
```

**rdfs:range**, examples:

```
rdf:langRange rdfs:range owl:Thing
rdf:rest rdfs:range owl:Thing
rdfs:comment rdfs:range owl:Thing
rdfs:domain rdfs:range owl:Class
rdfs:domain rdfs:range owl:Thing
```

**rdfs:domain**, examples:

```
rdf:first rdfs:domain owl:Thing
rdf:object rdfs:domain owl:Thing
rdf:predicate rdfs:domain owl:Thing
rdf:rest rdfs:domain owl:Thing
rdf:subject rdfs:domain owl:Thing
```

**rdfs:subPropertyOf**, examples:

```
rdf:_1 rdfs:subPropertyOf rdf:_1
rdf:object rdfs:subPropertyOf rdf:object
rdf:predicate rdfs:subPropertyOf rdf:predicate
rdf:subject rdfs:subPropertyOf rdf:subject
rdf:value rdfs:subPropertyOf rdf:value
```

**owl:disjointWith**, examples:

```
ex:uni#Course owl:disjointWith ex:uni#Person
```

## Inferred only by owl2-rl-optimized (329 triples)

| Predicate | Triples |
|---|---|
| owl:sameAs | 212 |
| rdf:type | 38 |
| rdfs:domain | 24 |
| ex:uni#affiliatedWith | 11 |
| rdfs:range | 9 |
| rdfs:subClassOf | 8 |
| ex:uni#collaboratesWith | 4 |
| ex:uni#teaches | 4 |
| ex:uni#insegna | 4 |
| ex:uni#partOf | 3 |
| ex:uni#homepage | 2 |
| ex:uni#supervisedBy | 2 |
| ex:uni#supervises | 2 |
| ex:uni#teachesLab | 2 |
| ex:uni#email | 1 |
| ex:uni#hasMainSupervisor | 1 |
| ex:uni#hIndex | 1 |
| ex:uni#hasTopic | 1 |

**owl:sameAs**, examples:

```
_:b owl:sameAs _:b
ex:uni owl:sameAs ex:uni
ex:uni#Academic owl:sameAs ex:uni#Academic
ex:uni#Course owl:sameAs ex:uni#Course
ex:uni#Docente owl:sameAs ex:uni#Docente
```

**rdf:type**, examples:

```
ex:uni#SemanticWeb rdf:type owl:Thing
ex:uni#a_rossi rdf:type _:b
ex:uni#a_rossi rdf:type ex:uni#Academic
ex:uni#a_rossi rdf:type ex:uni#Docente
ex:uni#a_rossi rdf:type ex:uni#Person
```

**rdfs:domain**, examples:

```
ex:uni#insegna rdfs:domain _:b
ex:uni#insegna rdfs:domain ex:uni#Staff
ex:uni#teaches rdfs:domain _:b
ex:uni#teaches rdfs:domain ex:uni#Staff
ex:uni#teachesLab rdfs:domain _:b
```

**ex:uni#affiliatedWith**, examples:

```
ex:uni#a_rossi ex:uni#affiliatedWith ex:uni#dept
ex:uni#a_rossi ex:uni#affiliatedWith ex:uni#faculty
ex:uni#a_rossi ex:uni#affiliatedWith ex:uni#kgGroup
ex:uni#a_rossi ex:uni#affiliatedWith ex:uni#unibo
ex:uni#alice ex:uni#affiliatedWith ex:uni#dept
```

**rdfs:range**, examples:

```
owl:allValuesFrom rdfs:range rdfs:Class
owl:maxCardinality rdfs:range rdfs:Literal
owl:maxCardinality rdfs:range xsd:nonNegativeInteger
owl:maxQualifiedCardinality rdfs:range rdfs:Literal
owl:maxQualifiedCardinality rdfs:range xsd:nonNegativeInteger
```

**rdfs:subClassOf**, examples:

```
ex:uni#Academic rdfs:subClassOf _:b
ex:uni#Academic rdfs:subClassOf ex:uni#Staff
ex:uni#Docente rdfs:subClassOf _:b
ex:uni#Docente rdfs:subClassOf ex:uni#Staff
ex:uni#Professor rdfs:subClassOf _:b
```

**ex:uni#collaboratesWith**, examples:

```
ex:uni#a_rossi ex:uni#collaboratesWith ex:uni#bruno
ex:uni#bruno ex:uni#collaboratesWith ex:uni#a_rossi
ex:uni#bruno ex:uni#collaboratesWith ex:uni#profAlice
ex:uni#profAlice ex:uni#collaboratesWith ex:uni#bruno
```

**ex:uni#teaches**, examples:

```
ex:uni#a_rossi ex:uni#teaches ex:uni#kg101
ex:uni#a_rossi ex:uni#teaches ex:uni#kgLab
ex:uni#profAlice ex:uni#teaches ex:uni#kg101
ex:uni#profAlice ex:uni#teaches ex:uni#kgLab
```

**ex:uni#insegna**, examples:

```
ex:uni#a_rossi ex:uni#insegna ex:uni#kg101
ex:uni#a_rossi ex:uni#insegna ex:uni#kgLab
ex:uni#profAlice ex:uni#insegna ex:uni#kg101
ex:uni#profAlice ex:uni#insegna ex:uni#kgLab
```

**ex:uni#partOf**, examples:

```
ex:uni#dept ex:uni#partOf ex:uni#unibo
ex:uni#kgGroup ex:uni#partOf ex:uni#faculty
ex:uni#kgGroup ex:uni#partOf ex:uni#unibo
```

**ex:uni#homepage**, examples:

```
ex:uni#alice ex:uni#homepage ex:~arossi
ex:uni#profAlice ex:uni#homepage ex:~arossi
```

**ex:uni#supervisedBy**, examples:

```
ex:uni#carla ex:uni#supervisedBy ex:uni#a_rossi
ex:uni#carla ex:uni#supervisedBy ex:uni#profAlice
```

**ex:uni#supervises**, examples:

```
ex:uni#a_rossi ex:uni#supervises ex:uni#carla
ex:uni#profAlice ex:uni#supervises ex:uni#carla
```

**ex:uni#teachesLab**, examples:

```
ex:uni#a_rossi ex:uni#teachesLab ex:uni#kgLab
ex:uni#profAlice ex:uni#teachesLab ex:uni#kgLab
```

**ex:uni#email**, examples:

```
ex:uni#profAlice ex:uni#email "alice@example.org"
```

**ex:uni#hasMainSupervisor**, examples:

```
ex:uni#carla ex:uni#hasMainSupervisor ex:uni#a_rossi
```

**ex:uni#hIndex**, examples:

```
ex:uni#dario ex:uni#hIndex "13"
```

**ex:uni#hasTopic**, examples:

```
ex:uni#sw301 ex:uni#hasTopic ex:uni#SemanticWeb
```

