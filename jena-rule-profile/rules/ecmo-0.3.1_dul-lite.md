# Compiled rule profile

Rules file: `../rules/ecmo-0.3.1_dul-lite.rules` · 2643 rules

| Rule type | Rules |
|---|---|
| cax | 818 |
| cax-dw | 25 |
| prp-asyp | 3 |
| prp-dom | 460 |
| prp-inv | 321 |
| prp-irp | 1 |
| prp-rng | 432 |
| prp-spo1 | 550 |
| prp-spo2 | 16 |
| prp-symp | 4 |
| prp-trp | 13 |

## Skipped axioms

| Reason | Axioms | Examples |
|---|---|---|
| restriction on the super-class side (someValuesFrom) | 190 | http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Action subClassOf n21105a19d9314d82835fa7f545975cbfb42; http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Classification subClassOf n21105a19d9314d82835fa7f545975cbfb44; http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Classification subClassOf n21105a19d9314d82835fa7f545975cbfb45 |
| unionOf on the super-class side | 41 | http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#InformationRealization subClassOf n21105a19d9314d82835fa7f545975cb; http://www.ontologydesignpatterns.org/ont/d0.owl#CognitiveEntity subClassOf N2294b15d31464d4c9d5eabea046ba8c6; http://data.europa.eu/h8v/ecmo/bio/BiologicalEntity subClassOf n9d3654b7ef854a91bd186a8eb34eba4eb2 |
| owl:sameAs inference (enable with --sameas) | 9 | http://data.europa.eu/h8v/ecmo/phsm/hasMeasureCategory; http://data.europa.eu/h8v/ecmo/phsm/hasLegalStatus; http://data.europa.eu/h8v/ecmo/phsm/hasImplementationScope |
| restriction on the super-class side (minCardinality) | 5 | http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Action subClassOf n21105a19d9314d82835fa7f545975cbfb43; http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Place subClassOf n21105a19d9314d82835fa7f545975cbfb88; http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Right subClassOf n21105a19d9314d82835fa7f545975cbfb101 |
| restriction on the super-class side (minQualifiedCardinality) | 5 | http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Transition subClassOf n21105a19d9314d82835fa7f545975cbfb134; http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Transition subClassOf n21105a19d9314d82835fa7f545975cbfb135; http://www.ontologydesignpatterns.org/ont/d0.owl#Domain subClassOf Na4ce05084e4241f1b788d317facdf601 |
| restriction on the super-class side (hasSelf) | 1 | http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#InformationRealization subClassOf n21105a19d9314d82835fa7f545975cb |
| restriction on the super-class side (cardinality) | 1 | http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#SocialPerson subClassOf n21105a19d9314d82835fa7f545975cbfb110 |
