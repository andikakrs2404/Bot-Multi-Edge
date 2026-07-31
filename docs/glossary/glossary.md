# AlphaOS Glossary (Working)

Companion to ADR-000A (Ubiquitous Language). This file keeps the growing vocabulary; ADR-000A remains canonical for domain terms.

| Term | Definition |
| --- | --- |
| AlphaOS | The autonomous quantitative research operating system. |
| AKB | Alpha Knowledge Base — persistent representation of domain knowledge graph. |
| Observation | Raw measurement of market state (price/volume/OI/funding). |
| Feature | Immutable derived property of market state (registered). |
| Label | Future outcome, research-only (registered). |
| Rule | AST logical expression over Features. |
| Candidate | Rule under evaluation in an Experiment. |
| Experiment | Reproducible scientific inquiry (aggregate root). |
| Evidence | Statistical results supporting/refuting a Candidate. |
| Edge | Candidate promoted to Knowledge. |
| Knowledge | Validated content of the AKB. |
| Portfolio | Allocation over ACTIVE edges. |
| ProductionDecision | Auditable production action. |
| ResearchCycle | Complete scheduled research pipeline run. |
| Realm | Research or Production partition. |
| Constitution Hash | SHA256 over ratified ADR files; recorded in every Experiment. |
| OOS | Out-of-sample (sacred held-out set). |
| WF | Walk-forward validation. |
| FeatureID / RuleID / EdgeID | Permanent content-addressed identities. |
