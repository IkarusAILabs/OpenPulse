**Conformance of the implementation to the specification**

| check | cases | result |
|---|---|---|
| oracle matrix (exhaustive grid) | 6195 | conform: 6123, label: both unresolved: 72 |
| randomised differential (seed 7) | 100000 | conform: 100000 |
| decision invariants I1-I8 (seeds 11, 12, 13) | 12000 | violations: 0; checks per invariant I1 2481, I2 1393, I3 1112, I4 7235, I5 12928, I6 1351, I7 1025, I8 8480 |
| defect re-injection (mutants) | 23 | caught 23; by invariants 14; not re-injected D2, D5, D6 |

The oracle and the invariants were written by the same team as the engine (THREATS_TO_VALIDITY.md); this is internal evidence, not formal verification.
