"""AlphaOS AKB Representation (ADR-009).

AKB = knowledge graph contract. Storage is detail. This first adapter is
stdlib in-memory, enough to enforce ontology and query guarantees before
introducing DuckDB.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .contracts import Edge, EdgeStatus, ProductionDecision, RelationshipType
from .evidence import Evidence, EvidenceStatus


class NodeType(str, Enum):
    DATASET = "Dataset"
    FEATURE = "Feature"
    LABEL = "Label"
    RULE = "Rule"
    EXPERIMENT = "Experiment"
    CANDIDATE = "Candidate"
    EVIDENCE = "Evidence"
    EDGE = "Edge"
    PORTFOLIO = "Portfolio"
    PRODUCTION_DECISION = "ProductionDecision"
    ACTIVATION_RECORD = "ActivationRecord"


@dataclass(frozen=True, slots=True)
class GraphNode:
    node_type: NodeType
    node_id: str
    payload: Any


@dataclass(frozen=True, slots=True)
class GraphRelationship:
    rel_type: RelationshipType
    source_type: NodeType
    source_id: str
    target_type: NodeType
    target_id: str


@dataclass(slots=True)
class AKB:
    """Logical AKB graph with query guarantees from spec §5."""
    nodes: dict[tuple[NodeType, str], GraphNode] = field(default_factory=dict)
    rels: list[GraphRelationship] = field(default_factory=list)

    def add_node(self, node_type: NodeType | str, node_id: str, payload: Any) -> None:
        nt = NodeType(node_type)
        key = (nt, node_id)
        if key in self.nodes:
            raise ValueError(f"duplicate node: {nt.value}:{node_id}")
        self.nodes[key] = GraphNode(nt, node_id, payload)

    def get_node(self, node_type: NodeType | str, node_id: str) -> GraphNode:
        nt = NodeType(node_type)
        try:
            return self.nodes[(nt, node_id)]
        except KeyError as e:
            raise KeyError(f"missing node: {nt.value}:{node_id}") from e

    def add_relationship(self, rel_type: RelationshipType | str,
                         source_type: NodeType | str, source_id: str,
                         target_type: NodeType | str, target_id: str) -> None:
        rt = RelationshipType(rel_type)
        st = NodeType(source_type)
        tt = NodeType(target_type)
        self.get_node(st, source_id)
        self.get_node(tt, target_id)
        rel = GraphRelationship(rt, st, source_id, tt, target_id)
        if rel not in self.rels:
            self.rels.append(rel)

    def relationships_from(self, node_type: NodeType | str, node_id: str,
                           rel_type: RelationshipType | str | None = None) -> list[GraphRelationship]:
        nt = NodeType(node_type)
        rt = RelationshipType(rel_type) if rel_type else None
        return [r for r in self.rels
                if r.source_type == nt and r.source_id == node_id
                and (rt is None or r.rel_type == rt)]

    def relationships_to(self, node_type: NodeType | str, node_id: str,
                         rel_type: RelationshipType | str | None = None) -> list[GraphRelationship]:
        nt = NodeType(node_type)
        rt = RelationshipType(rel_type) if rel_type else None
        return [r for r in self.rels
                if r.target_type == nt and r.target_id == node_id
                and (rt is None or r.rel_type == rt)]

    def evidence_for_edge(self, edge_id: str) -> list[GraphNode]:
        """Given EdgeID → all Evidence (1:N)."""
        rels = self.relationships_from(NodeType.EDGE, edge_id,
                                       RelationshipType.SUPPORTED_BY)
        return [self.get_node(NodeType.EVIDENCE, r.target_id) for r in rels]

    def trace_evidence(self, evidence_id: str) -> dict[str, GraphNode | None]:
        """Given EvidenceID → Candidate and Experiment."""
        ev = self.get_node(NodeType.EVIDENCE, evidence_id)
        refs = self.relationships_from(NodeType.EVIDENCE, evidence_id,
                                       RelationshipType.REFERENCES)
        out: dict[str, GraphNode | None] = {"evidence": ev,
                                            "candidate": None,
                                            "experiment": None}
        for r in refs:
            if r.target_type == NodeType.CANDIDATE:
                out["candidate"] = self.get_node(NodeType.CANDIDATE, r.target_id)
            elif r.target_type == NodeType.EXPERIMENT:
                out["experiment"] = self.get_node(NodeType.EXPERIMENT, r.target_id)
        return out

    def trace_edge_to_datasets(self, edge_id: str) -> list[GraphNode]:
        """Given EdgeID → Dataset(s) via Evidence → Experiment → Dataset."""
        datasets: dict[str, GraphNode] = {}
        for ev in self.evidence_for_edge(edge_id):
            tr = self.trace_evidence(ev.node_id)
            exp = tr.get("experiment")
            if exp is None:
                continue
            uses = self.relationships_from(NodeType.EXPERIMENT, exp.node_id,
                                           RelationshipType.USES)
            for r in uses:
                if r.target_type == NodeType.DATASET:
                    datasets[r.target_id] = self.get_node(NodeType.DATASET, r.target_id)
        return list(datasets.values())

    def experiments_for_rule(self, rule_id: str) -> list[GraphNode]:
        """Given RuleID → Experiments using it."""
        return [self.get_node(NodeType.EXPERIMENT, r.source_id)
                for r in self.relationships_to(NodeType.RULE, rule_id,
                                               RelationshipType.USES)
                if r.source_type == NodeType.EXPERIMENT]

    def trace_production_decision(self, decision_id: str) -> dict[str, Any]:
        """ProductionDecision → Portfolio → Edge → Evidence → Experiment → Dataset."""
        decision = self.get_node(NodeType.PRODUCTION_DECISION, decision_id)
        drives = self.relationships_to(NodeType.PRODUCTION_DECISION, decision_id,
                                       RelationshipType.DRIVES)
        portfolios = [self.get_node(NodeType.PORTFOLIO, r.source_id) for r in drives]
        edges: list[GraphNode] = []
        evidence: list[GraphNode] = []
        datasets: list[GraphNode] = []
        for p in portfolios:
            alloc = self.relationships_to(NodeType.PORTFOLIO, p.node_id,
                                          RelationshipType.ALLOCATED_TO)
            for r in alloc:
                edge = self.get_node(NodeType.EDGE, r.source_id)
                edges.append(edge)
                evs = self.evidence_for_edge(edge.node_id)
                evidence.extend(evs)
                datasets.extend(self.trace_edge_to_datasets(edge.node_id))
        return {"decision": decision, "portfolios": portfolios,
                "edges": _dedupe_nodes(edges), "evidence": _dedupe_nodes(evidence),
                "datasets": _dedupe_nodes(datasets)}

    def validate_active_edge(self, edge_id: str) -> None:
        """Reject orphan ACTIVE Edge (spec §4.4)."""
        edge = self.get_node(NodeType.EDGE, edge_id).payload
        if isinstance(edge, Edge) and edge.status == EdgeStatus.ACTIVE:
            evs = self.evidence_for_edge(edge_id)
            if not evs:
                raise ValueError("ACTIVE edge requires SUPPORTS evidence")
            for ev in evs:
                payload = ev.payload
                if isinstance(payload, Evidence) and payload.status != EvidenceStatus.SUPPORTS:
                    raise ValueError("ACTIVE edge evidence must be SUPPORTS")


def _dedupe_nodes(nodes: list[GraphNode]) -> list[GraphNode]:
    seen: set[tuple[NodeType, str]] = set()
    out: list[GraphNode] = []
    for n in nodes:
        key = (n.node_type, n.node_id)
        if key not in seen:
            seen.add(key)
            out.append(n)
    return out


def link_edge_evidence(akb: AKB, edge: Edge, evidence: Evidence) -> None:
    """Add Edge → Evidence 1:N relationship and keep Edge.supported_by in sync."""
    akb.add_relationship(RelationshipType.SUPPORTED_BY,
                         NodeType.EDGE, edge.edge_id,
                         NodeType.EVIDENCE, evidence.evidence_id)


def link_evidence_trace(akb: AKB, evidence: Evidence, candidate_id: str,
                        experiment_id: str) -> None:
    """Add Evidence → Candidate and Evidence → Experiment relationships."""
    akb.add_relationship(RelationshipType.REFERENCES,
                         NodeType.EVIDENCE, evidence.evidence_id,
                         NodeType.CANDIDATE, candidate_id)
    akb.add_relationship(RelationshipType.REFERENCES,
                         NodeType.EVIDENCE, evidence.evidence_id,
                         NodeType.EXPERIMENT, experiment_id)


def register_production_decision(akb: AKB, decision: ProductionDecision) -> None:
    """Reject decisions that cannot trace to at least one ACTIVE Edge."""
    if not decision.triggered_edges:
        raise ValueError("ProductionDecision requires triggered_edges")
    for edge_id in decision.triggered_edges:
        edge = akb.get_node(NodeType.EDGE, edge_id).payload
        if isinstance(edge, Edge) and edge.status != EdgeStatus.ACTIVE:
            raise ValueError(f"triggered edge is not ACTIVE: {edge_id}")
    akb.add_node(NodeType.PRODUCTION_DECISION, decision.decision_id, decision)
