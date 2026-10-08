# ECMO 0.3.1: inconsistencies with DUL

## Summary

ECMO 0.3.1 (`ecmo-0.3.1-dl42-patched`) is consistent on its own. Loaded together
with DUL and the case fixtures (Ebola and Hondius/Hantavirus), it is
**inconsistent**: 31 individuals end up in two classes that DUL declares
disjoint.

| Disjoint pair | Individuals |
|---|---|
| `dul:Event` ⊓ `dul:Object` | 17 |
| `dul:Object` ⊓ `dul:Quality` | 14 |

None of these come from errors in the case data. All 31 follow from five groups
of ECMO → DUL alignment axioms in `ecmo-property-alignments.ttl`, each combined
with a DUL axiom that ECMO's usage contradicts:

| # | ECMO alignment | DUL axiom it collides with | Individuals |
|---|---|---|---|
| A | `capacity:includesInstitution/Resource/Knowledge ⊑ dul:hasPart` | `dul:Quality ⊑ ∀dul:hasPart.dul:Quality` | 11 |
| B | `risk:hasCapacityDeterminant ⊑ dul:hasComponent` | `dul:Object ⊑ ∀dul:hasPart.dul:Object` | 3 (+ part of A) |
| C | `foundation:hasTemporalValidity ⊑ dul:hasTimeInterval` | domain of `dul:hasTimeInterval` is `dul:Event` | 13 |
| D | category properties `⊑ dul:isClassifiedBy` (e.g. `hazard:hasHazardCategory`) | `dul:Object ⊑ ∀dul:isClassifiedBy.dul:Role`, `dul:Role ⊑ ∀dul:classifies.dul:Object` | 3 |
| E | `foundation:hasQualitativeAssessment ⊑ dul:isAbout` | domain of `dul:isAbout` is `dul:InformationObject` | 1 |

The fixes proposed below were applied to an in-memory copy of ECMO and
re-checked: after applying them, no disjointness violation remains.

## How it was found

1. GraphDB, with consistency checks on
   (`./ecmo-graphdb-benchmark.sh --dul-lite --consistency --rulesets owl2-ql-optimized owl2-rl-optimized`).
   It rejects the load of `ecmo-ebola-case.ttl` with rule `cax_dw_1`
   (OWL 2 RL cax-dw: an individual in two disjoint classes). GraphDB stops at the
   first violation, so each ruleset reports only one:
   - owl2-rl: `agency:ECRC` is a `dul:Object` and a `dul:Quality` (group A);
   - owl2-ql: `ebola:s_nadira_initial` is a `dul:Object` and a `dul:Event` (group C).
2. `check_disjointness.py`, which computes the relevant OWL 2 RL type inferences
   and lists **all** violations with their derivations, grouped by the
   alignments involved.

The violations do not depend on the DUL variant. `DUL-lite` and `DUL-flat`
give the same 31. The original DUL only adds transitivity and symmetry of
`dul:associatedWith`, and no restriction, property chain, or domain/range other
than `dul:Entity` refers to that property, so it cannot change any type. The
violations come from domains, ranges and `allValuesFrom` restrictions, which
all three variants keep.

## A. Capacities are qualities, but "include" objects

```
capacity:CopingCapacity ⊑ dul:Quality                           (ecmo-capacity.ttl)
capacity:includesInstitution ⊑ dul:hasPart                      (ecmo-property-alignments.ttl:135)
capacity:includesResource    ⊑ dul:hasPart                      (:134)
capacity:includesKnowledge   ⊑ dul:hasPart                      (:136)
dul:Quality ⊑ ∀dul:hasPart.dul:Quality                          (DUL: every part of a quality is a quality)
```

Example from the Ebola case:

```
ebola:EU_HumanitarianCapacity a capacity:CopingCapacity              ⇒ a dul:Quality
ebola:EU_HumanitarianCapacity capacity:includesInstitution agency:ECRC
  includesInstitution ⊑ dul:hasPart                                   ⇒ agency:ECRC a dul:Quality
agency:ECRC a governance:Institution ⊑ dul:Agent ⊑ dul:Object        ✗ Object ⊓ Quality
```

Affected individuals (11):
- institutions: `agency:ECRC`, `agency:ECDC`, `agency:HERA`, `agency:WHO`;
- resources: `ebola:ETU_FieldKit`, `ebola:MonoclonalStockpile`,
  `ebola:rVSV_VaccineStockpile`, `hondius:EU_PCR_Lab_Capacity`, `hondius:EU_MaritimeMedEvac`;
- knowledge: `ebola:EVDClinicalKnowledge`, `hondius:HantavirusClinicalKnowledge`.

The inverses are aligned the same way (`capacity:isResourceOf ⊑ dul:isPartOf`,
line 515; `capacity:isKnowledgeOf ⊑ dul:isPartOf`, line 514), so they produce
the same `dul:hasPart` links.

`capacity:includesCollectiveAttribute ⊑ dul:hasPart` (line 508) is fine on its
own, because collective attributes are qualities. It contributes only through
group B.

**Fix.** Align `includesInstitution`, `includesResource`, `includesKnowledge`
and the inverses `isResourceOf`, `isKnowledgeOf` to a non-parthood relation,
for example `dul:associatedWith` / its inverse.

Remodelling capacities as `dul:Collection` (with `dul:hasMember`) instead of
`dul:Quality` was also tested, and it does **not** work on its own: capacities
are also subjects of `capacity:preservesFunction`, whose domain is
`capacity:Resilience ⊑ dul:Quality`, so they would again be both an Object and
a Quality.

## B. Risks (descriptions) have capacities (qualities) as components

```
risk:Risk ⊑ dul:Description ⊑ dul:SocialObject ⊑ dul:Object
risk:hasCapacityDeterminant ⊑ dul:hasComponent ⊑ dul:hasProperPart ⊑ dul:hasPart   (ecmo-property-alignments.ttl:152)
dul:Object ⊑ ∀dul:hasPart.dul:Object                            (DUL: every part of an object is an object)
```

Example:

```
ebola:NadiraEVDRisk a risk:Risk                                       ⇒ a dul:Object
ebola:NadiraEVDRisk risk:hasCapacityDeterminant ebola:EU_HumanitarianCapacity
                                                                      ⇒ EU_HumanitarianCapacity a dul:Object
ebola:EU_HumanitarianCapacity a capacity:CopingCapacity ⊑ dul:Quality ✗ Object ⊓ Quality
```

Because `dul:hasPart` is transitive, everything the capacity includes also
becomes a part of the risk, and therefore an Object. That is how
`ebola:SocialCohesion_Akele` (a `capacity:CollectiveAttribute`, i.e. a Quality)
is caught, and it gives the resources of group A a second route.

Affected individuals (3): `ebola:EU_HumanitarianCapacity`,
`hondius:EU_DRR_Capacity`, `ebola:SocialCohesion_Akele`.

**Fix.** Align `risk:hasCapacityDeterminant` and its inverse
`risk:isCapacityDeterminantOf` (line 532, `⊑ dul:isComponentOf`) to a
non-parthood relation, e.g. `dul:associatedWith`. A risk *depends on* a
capacity; the capacity is not a component of the risk description.

## C. Temporal validity makes information objects into events

```
foundation:hasTemporalValidity ⊑ dul:hasTimeInterval            (ecmo-property-alignments.ttl:228)
domain(dul:hasTimeInterval) = dul:Event
```

Example:

```
ebola:s_nadira_initial a situation:Signal ⊑ dul:InformationObject ⊑ dul:Object
ebola:s_nadira_initial foundation:hasTemporalValidity [ … ]         ⇒ a dul:Event
                                                                      ✗ Event ⊓ Object
```

Every non-event with a validity period is affected: signals, notifications,
threats, warnings.

Affected individuals (13): `ebola:s_nadira_initial`, `ebola:s_argus_p1`,
`ebola:s_argus_p2`, `ebola:s_athina_threat`, `ebola:s_ews_n1`,
`ebola:s_who_pheic`, `hondius:s_argus_p1`, `hondius:s_athina_sig`,
`hondius:s_athina_threat`, `hondius:s_ecmp_sig1`, `hondius:s_ews_n1`,
`hondius:s_ews_n2`, `hondius:EWS_Warning_02May`.

**Fix.** Drop the alignment of `foundation:hasTemporalValidity` to
`dul:hasTimeInterval`, together with the inverse `foundation:isTemporalValidityOf`
(line 617, `⊑ dul:isTimeIntervalOf`). DUL has no generic "valid during"
relation; aligning to `dul:associatedWith` is safe. An alternative is to keep
`dul:hasTimeInterval` only for event-like classes and use a separate validity
property for information objects and descriptions.

## D. Shared category values: roles classify only objects

Many ECMO "category/type/level" properties are aligned to `dul:isClassifiedBy`
(38 ECMO properties in total). DUL constrains classification asymmetrically:

```
dul:Object ⊑ ∀dul:isClassifiedBy.dul:Role     (anything that classifies an object is a role)
dul:Role   ⊑ ∀dul:classifies.dul:Object       (a role classifies only objects)
```

So as soon as a category value classifies **one** object, it becomes a
`dul:Role`, and every event it also classifies becomes an Object. Category values
are often shared between objects (agents, descriptions, information objects,
diseases) and events (outbreaks, disasters, assessments).

Example:

```
ph:PopilliaJaponica a ph:Pest ⊑ dul:Agent ⊑ dul:Object
ph:Pest has the hasValue restriction  hazard:hasHazardCategory hazard:BiologicalTarget
hazard:hasHazardCategory ⊑ dul:isClassifiedBy (ecmo-property-alignments.ttl:179)
                                                              ⇒ hazard:BiologicalTarget a dul:Role
ebola:EbolaOutbreakEvent hazard:hasHazardCategory hazard:BiologicalTarget
                                                              ⇒ EbolaOutbreakEvent a dul:Object
ebola:EbolaOutbreakEvent a hazard:HazardousEvent ⊑ dul:Event  ✗ Event ⊓ Object
```

The problem then cascades. `EbolaOutbreakEvent`, now an Object, makes
`disaster:SuddenOnset` and `disaster:LowFrequency` Roles, which makes
`ebola:NadiraEVDDisaster` an Object. In the Hondius case, `ph:DiseaseCategory`
classifies the disease individuals of `ecmo-ph.ttl` (objects), so it becomes a
Role, and `hondius:CruiseShipHantavirusEvent`, which has the same category, becomes an
Object.

Affected individuals (3): `ebola:EbolaOutbreakEvent`,
`ebola:NadiraEVDDisaster`, `hondius:CruiseShipHantavirusEvent`. Once groups
A, B, C and E are fixed, `ebola:CampCapacityAssessment` is also caught here,
through `capacity:hasCapacityDomain`, `foundation:hasAssessmentDomain` and
`foundation:hasLevel`.

Smallest set of `dul:isClassifiedBy` alignments that must change to reach zero
violations on the current case data (each was tested by removing it from the
fix set; lines in `ecmo-property-alignments.ttl`):

| Property | Line | Why it is needed |
|---|---|---|
| `hazard:hasHazardCategory` | 179 | `hazard:BiologicalTarget` classifies pests (objects) and outbreak events |
| `ph:hasHealthConditionCategory` | 360 | `ph:DiseaseCategory` classifies diseases (objects) and `hondius:CruiseShipHantavirusEvent` |
| `foundation:hasLevel` and inverse `foundation:isLevelOf` (`⊑ dul:classifies`) | 347, 368 | `ebola:Sev_Medium` is the level of an assessment (event) and of its qualitative assessment (information object) |
| `capacity:hasCapacityDomain` **or** `foundation:hasAssessmentDomain` | 344 / 346 | `foundation:PathogenRiskDomain` is the domain of HERA scales (descriptions) and of `ebola:CampCapacityAssessment` (event); changing either one is enough |

`disaster:hasOnsetType`, `disaster:hasFrequencyType` and `ph:hasRouteOfTransmission`
take part in the derivations above, but only as a consequence of the
properties in the table. Once those are fixed, they produce no violation.

This list depends on the data: any other category property whose values are
used for both objects and events will fail in the same way with new data.

**Fix.**
- Simplest: align category properties whose values are shared between
  objects and events to `dul:associatedWith` instead of `dul:isClassifiedBy`.
  At minimum, change the ones in the table above.
- More faithful to DUL: split the value sets. Concepts that classify events
  should not be used for objects, and vice versa. A category that applies to
  both would need two individuals, or a modelling choice that keeps them apart.

A related data smell in `ecmo-ph.ttl`: `ph:Nosocomial` is typed both as
`ph:InfectiousDiseaseOrPathogen` and as `ph:RouteOfTransmission`, and it has
`ph:hasRouteOfTransmission ph:Nosocomial` (it is its own route). That looks
like an import artefact.

## E. Qualitative assessment: wrong direction of `isAbout`

```
foundation:hasQualitativeAssessment   ⊑ dul:isAbout     (ecmo-property-alignments.ttl:210)
foundation:isQualitativeAssessmentOf  ⊑ dul:isAbout     (:540)
domain(dul:isAbout) = dul:InformationObject
```

Both a property and its inverse are aligned to `dul:isAbout`, so one of them
is reversed. `X hasQualitativeAssessment QA` means that QA is about X, so it is
the assessed thing X that becomes an information object:

```
ebola:CampCapacityAssessment a capacity:CapacityAssessment ⊑ dul:Process ⊑ dul:Event
ebola:CampCapacityAssessment foundation:hasQualitativeAssessment ebola:CapAssessQA
                                                              ⇒ a dul:InformationObject ⊑ dul:Object
                                                              ✗ Event ⊓ Object
```

Affected individuals (1): `ebola:CampCapacityAssessment`.

**Fix.** `foundation:hasQualitativeAssessment ⊑ dul:isReferenceOf` (the inverse
of `dul:isAbout`) instead of `dul:isAbout`. Keep
`foundation:isQualitativeAssessmentOf ⊑ dul:isAbout`.

## Verified fix set

These changes to `ecmo-property-alignments.ttl` were applied together, and
`check_disjointness.py` then reports 0 violations on ECMO + DUL + all four case
fixtures:

| Line | Current | Change to |
|---|---|---|
| 134–136 | `includesResource / includesInstitution / includesKnowledge ⊑ dul:hasPart` | `⊑ dul:associatedWith` |
| 514–515 | `isKnowledgeOf / isResourceOf ⊑ dul:isPartOf` | `⊑ dul:associatedWith` |
| 152 | `risk:hasCapacityDeterminant ⊑ dul:hasComponent` | `⊑ dul:associatedWith` |
| 532 | `risk:isCapacityDeterminantOf ⊑ dul:isComponentOf` | `⊑ dul:associatedWith` |
| 228 | `foundation:hasTemporalValidity ⊑ dul:hasTimeInterval` | `⊑ dul:associatedWith` |
| 617 | `foundation:isTemporalValidityOf ⊑ dul:isTimeIntervalOf` | `⊑ dul:associatedWith` |
| 210 | `foundation:hasQualitativeAssessment ⊑ dul:isAbout` | `⊑ dul:isReferenceOf` |
| 179 | `hazard:hasHazardCategory ⊑ dul:isClassifiedBy` | `⊑ dul:associatedWith` |
| 360 | `ph:hasHealthConditionCategory ⊑ dul:isClassifiedBy` | `⊑ dul:associatedWith` |
| 347 | `foundation:hasLevel ⊑ dul:isClassifiedBy` | `⊑ dul:associatedWith` |
| 368 | `foundation:isLevelOf ⊑ dul:classifies` | `⊑ dul:associatedWith` |
| 344 (or 346) | `capacity:hasCapacityDomain` (or `foundation:hasAssessmentDomain`) `⊑ dul:isClassifiedBy` | `⊑ dul:associatedWith` |

Every row is needed: removing any single change from the set brings back at
least one violation (the two alternatives in the last row aside).
`capacity:includesCollectiveAttribute ⊑ dul:hasPart` can stay as it is.

`dul:associatedWith` is the conservative choice: it keeps the properties inside
DUL's hierarchy without importing constraints. Where a more specific DUL
relation fits the intended meaning, it can be used instead, but it should be
re-checked.

## Caveats

- `check_disjointness.py` implements the OWL 2 RL rules that matter for class
  disjointness: subclass/subproperty, inverses, symmetry, transitivity, domain,
  range, `allValuesFrom`, `someValuesFrom`, `hasValue`, intersection, union.
  It does not handle `owl:sameAs`, property chains, cardinalities or datatypes,
  so further violations of other kinds are possible.
- With `owl:sameAs` handling on, the ~3.7k `owl:sameAs` links in `ecmo-ph.ttl`
  could merge individuals of different kinds and expose more clashes.
- Not yet cross-checked with a DL reasoner (HermiT). The violations above use only
  standard OWL semantics, so HermiT should report them as well.

## Reproducing

```bash
# all violations with derivations (needs rdflib)
python3 check_disjointness.py                       # ECMO + DUL-lite + case fixtures
python3 check_disjointness.py --dul ecmo-deps/DUL.owl
python3 check_disjointness.py --no-data             # ontology only: 0 violations
python3 check_disjointness.py --examples 3          # more derivations per group

# GraphDB (stops at the first violation)
./ecmo-graphdb-benchmark.sh --dul-lite --consistency -n 1 \
    --rulesets owl2-ql-optimized owl2-rl-optimized
```
