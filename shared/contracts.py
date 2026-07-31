"""AlphaOS shared contracts (ADR-002/003/004/005).

Constitution hash: be37bf97508691f93557849e1b05d7a1bf2c7be89029cc7f9dcbc77ba964d8cd
Constitutional Freeze v1.0 — Layer 0 & 1 ratified 2026-07-29.

This module is the ONLY place where domain entities are defined for both
realms (research + production). It is dependency-free (stdlib only) per
ADR-001 principle 7 (enforced dependency direction).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

CONSTITUTION_HASH = "be37bf97508691f93557849e1b05d7a1bf2c7be89029cc7f9dcbc77ba964d8cd"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Lifecycle states (ADR-002A) ──

class EdgeStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    OPTIMIZED = "OPTIMIZED"
    VALIDATED = "VALIDATED"
    ACTIVE = "ACTIVE"
    MONITORED = "MONITORED"
    DECAYED = "DECAYED"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"


class ExperimentStatus(str, Enum):
    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PROMOTED = "PROMOTED"
    FAILED = "FAILED"


class DatasetStatus(str, Enum):
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class PortfolioStatus(str, Enum):
    DRAFT = "DRAFT"
    BACKTESTED = "BACKTESTED"
    APPROVED = "APPROVED"
    LIVE = "LIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"


# ── Relationship types (ADR-002, first-class graph edges) ──

class RelationshipType(str, Enum):
    DERIVES = "derives"              # legacy alias: Feature -> Feature
    DERIVED_FROM = "derived_from"    # Feature/Label -> Dataset | Feature -> Feature
    USES = "uses"                    # Rule -> Feature | Experiment -> Dataset/Rule
    TESTS = "tests"                  # Experiment -> Candidate
    PRODUCES = "produces"            # Experiment -> Candidate/Evidence
    SUPPORTED_BY = "supported_by"    # Edge -> Evidence (1:N)
    SUPERSEDES = "supersedes"        # Edge -> Edge
    ALLOCATED_TO = "allocated_to"    # Edge -> Portfolio
    DRIVES = "drives"                # Portfolio -> ProductionDecision
    REFERENCES = "references"        # Evidence -> Candidate/Experiment
    ACTIVATED_BY = "activated_by"    # Edge -> ActivationRecord
    DECAYED_BY = "decayed_by"        # Edge -> ActivationRecord


# ── Domain entities (ADR-002) ──

@dataclass(frozen=True, slots=True)
class Dataset:
    """Immutable, versioned collection of market data (ADR-002, ADR-004)."""
    dataset_id: str
    schema_version: str
    universe: str
    timeframe: str
    date_range: tuple[str, str]
    content_hash: str
    parent_ids: tuple[str, ...] = ()
    status: DatasetStatus = DatasetStatus.CREATED
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class Feature:
    """Immutable derived property of market state (ADR-005)."""
    feature_id: str          # permanent identity; evolution = new id
    kind: str = "feature"    # 'feature' | 'label'
    category: str = ""
    formula: str = ""        # canonical AST serialization (ADR-006)
    owner: str = "system"
    lineage: tuple[str, ...] = ()   # derived_from FeatureIDs


@dataclass(frozen=True, slots=True)
class Rule:
    """Logical AST expression over Features (ADR-006)."""
    rule_id: str             # SHA256 of canonical AST
    ast: str                 # canonical serialized AST
    feature_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Experiment:
    """Reproducible scientific inquiry (ADR-007)."""
    experiment_id: str
    constitution_hash: str = CONSTITUTION_HASH
    dataset_ids: tuple[str, ...] = ()
    feature_ids: tuple[str, ...] = ()
    label_ids: tuple[str, ...] = ()
    seeds: tuple[int, ...] = (42,)
    git_commit: str = ""
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class Edge:
    """Validated Candidate promoted to Knowledge (ADR-002/002A).

    supported_by: 1:N EvidenceIDs (initial validation, walk-forward, OOS,
    decay check, revalidation — each produces its own Evidence). The
    edge is only as strong as its weakest supporting evidence chain.
    """
    edge_id: str
    rule_id: str
    experiment_id: str
    supported_by: tuple[str, ...] = ()  # EvidenceIDs (1:N)
    policy_id: str = ""               # ValidationPolicy that promoted it
    status: EdgeStatus = EdgeStatus.DISCOVERED
    version: int = 1
    birth_date: datetime = field(default_factory=utcnow)
    activation_date: datetime | None = None
    retirement_reason: str | None = None


@dataclass(frozen=True, slots=True)
class Evidence:
    """Statistical results supporting/refuting a Candidate (ADR-008)."""
    evidence_id: str
    experiment_id: str
    edge_id: str | None      # None while candidate not yet promoted
    metrics: dict[str, float]
    reports_refs: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class Portfolio:
    """Curated allocation over ACTIVE edges (ADR-002)."""
    portfolio_id: str
    objective: str = "max_sharpe"
    allocations: tuple[tuple[str, float], ...] = ()  # (edge_id, weight)
    status: PortfolioStatus = PortfolioStatus.DRAFT


@dataclass(frozen=True, slots=True)
class ProductionDecision:
    """Auditable production action (ADR-002)."""
    decision_id: str
    portfolio_id: str
    triggered_edges: tuple[str, ...]
    decision: str            # BUY | SELL | HOLD | SKIP
    confidence: float
    ts: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class Relationship:
    """First-class knowledge graph edge (ADR-002)."""
    rel_id: str
    rel_type: RelationshipType
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    created_by_experiment: str | None = None
    created_at: datetime = field(default_factory=utcnow)


# ── Content addressing (ADR-004, ADR-006) ──

def content_hash(obj: object) -> str:
    """SHA256 over the canonical JSON serialization of an object."""
    canonical = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def make_dataset_id(manifest: dict) -> str:
    return content_hash(manifest)


def make_rule_id(canonical_ast: str) -> str:
    return content_hash({"ast": canonical_ast})


def make_id(*parts: str, prefix: str = "ID") -> str:
    """Deterministic id from parts (permanent identity)."""
    return f"{prefix}-{content_hash(parts)}"[:24]


# ── Trust model enforcement (ADR-000B) ──

TRUST_LEVEL = {
    "RawObservation": 0, "Dataset": 1, "FeatureSnapshot": 2,
    "ExperimentResult": 3, "Evidence": 4, "Edge": 4, "Portfolio": 5,
}


def assert_trust(consumer: str, artifact: str) -> None:
    """Production may only consume trust level >= 4 (plus realtime level-2)."""
    if consumer == "production":
        level = TRUST_LEVEL[artifact]
        assert level >= 4, (
            f"trust violation: production consumed {artifact} (level {level}); "
            f"only levels 4-5 allowed (ADR-000B)"
        )
