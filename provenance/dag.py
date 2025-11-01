"""
DAG (Directed Acyclic Graph) reconstruction and analysis for provenance chains.

This module provides utilities to:
- Load provenance fragments from JSONL files
- Build DAG representations of transformation pipelines
- Query lineage for specific specimens
- Analyze processing patterns and detect inconsistencies
"""

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Any


@dataclass
class DAGNode:
    """A node in the provenance DAG."""

    fragment_id: str
    fragment_type: str
    source_identifier: str
    output_identifier: str
    process_operation: str
    timestamp: str
    parameters: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class DAGEdge:
    """An edge in the provenance DAG."""

    from_fragment_id: str
    to_fragment_id: str
    relationship_type: str = "transforms_to"  # or "derived_from"


class ProvenanceDAG:
    """
    DAG representation of provenance chains.

    Nodes represent transformations (provenance fragments).
    Edges represent data flow between transformations.
    """

    def __init__(self):
        self.nodes: Dict[str, DAGNode] = {}
        self.edges: List[DAGEdge] = []
        self.children: Dict[str, List[str]] = defaultdict(list)  # fragment_id → child fragment_ids
        self.parents: Dict[str, Optional[str]] = {}  # fragment_id → parent fragment_id

    def add_node(self, node: DAGNode) -> None:
        """Add a node to the DAG."""
        self.nodes[node.fragment_id] = node

    def add_edge(self, from_id: str, to_id: str) -> None:
        """Add an edge to the DAG."""
        edge = DAGEdge(from_fragment_id=from_id, to_fragment_id=to_id)
        self.edges.append(edge)
        self.children[from_id].append(to_id)
        self.parents[to_id] = from_id

    def get_lineage(self, fragment_id: str) -> List[DAGNode]:
        """
        Get the full lineage chain for a fragment (from root to this fragment).

        Args:
            fragment_id: Fragment ID to trace lineage for

        Returns:
            List of DAGNodes in chronological order (oldest to newest)
        """
        lineage = []
        current_id = fragment_id

        # Trace backwards to root
        chain_ids = []
        while current_id is not None:
            chain_ids.append(current_id)
            current_id = self.parents.get(current_id)

        # Reverse to get chronological order
        chain_ids.reverse()

        # Build lineage list
        for fid in chain_ids:
            if fid in self.nodes:
                lineage.append(self.nodes[fid])

        return lineage

    def get_descendants(self, fragment_id: str) -> List[DAGNode]:
        """
        Get all descendants of a fragment (breadth-first traversal).

        Args:
            fragment_id: Fragment ID to find descendants for

        Returns:
            List of DAGNodes that are derived from this fragment
        """
        descendants = []
        visited: Set[str] = set()
        queue = [fragment_id]

        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            for child_id in self.children.get(current_id, []):
                if child_id not in visited:
                    queue.append(child_id)
                    if child_id in self.nodes:
                        descendants.append(self.nodes[child_id])

        return descendants

    def get_roots(self) -> List[DAGNode]:
        """Get all root nodes (fragments with no parents)."""
        roots = []
        for fragment_id, node in self.nodes.items():
            if fragment_id not in self.parents or self.parents[fragment_id] is None:
                roots.append(node)
        return roots

    def get_leaves(self) -> List[DAGNode]:
        """Get all leaf nodes (fragments with no children)."""
        leaves = []
        for fragment_id, node in self.nodes.items():
            if fragment_id not in self.children or not self.children[fragment_id]:
                leaves.append(node)
        return leaves

    def get_statistics(self) -> Dict[str, Any]:
        """Get DAG statistics."""
        fragment_type_counts = defaultdict(int)
        for node in self.nodes.values():
            fragment_type_counts[node.fragment_type] += 1

        return {
            "total_fragments": len(self.nodes),
            "total_edges": len(self.edges),
            "root_fragments": len(self.get_roots()),
            "leaf_fragments": len(self.get_leaves()),
            "fragment_types": dict(fragment_type_counts),
            "max_depth": self._compute_max_depth(),
        }

    def _compute_max_depth(self) -> int:
        """Compute maximum depth of the DAG."""
        max_depth = 0
        for root in self.get_roots():
            depth = self._compute_node_depth(root.fragment_id)
            max_depth = max(max_depth, depth)
        return max_depth

    def _compute_node_depth(self, fragment_id: str, visited: Optional[Set[str]] = None) -> int:
        """Compute depth of a node (longest path to a leaf)."""
        if visited is None:
            visited = set()

        if fragment_id in visited:  # Cycle detection
            return 0

        visited.add(fragment_id)

        children = self.children.get(fragment_id, [])
        if not children:
            return 0

        max_child_depth = 0
        for child_id in children:
            child_depth = self._compute_node_depth(child_id, visited.copy())
            max_child_depth = max(max_child_depth, child_depth)

        return 1 + max_child_depth


def load_provenance_fragments(provenance_path: Path) -> List[Dict[str, Any]]:
    """
    Load provenance fragments from JSONL file.

    Args:
        provenance_path: Path to provenance.jsonl

    Returns:
        List of fragment dictionaries
    """
    fragments = []
    if not provenance_path.exists():
        return fragments

    with open(provenance_path) as f:
        for line in f:
            line = line.strip()
            if line:
                fragments.append(json.loads(line))

    return fragments


def build_dag(provenance_path: Path) -> ProvenanceDAG:
    """
    Build a DAG from provenance fragments.

    Args:
        provenance_path: Path to provenance.jsonl

    Returns:
        ProvenanceDAG representing the transformation chains
    """
    fragments = load_provenance_fragments(provenance_path)
    dag = ProvenanceDAG()

    # Add all nodes
    for fragment in fragments:
        node = DAGNode(
            fragment_id=fragment["fragment_id"],
            fragment_type=fragment["fragment_type"],
            source_identifier=fragment["source"]["identifier"],
            output_identifier=fragment["output"]["identifier"],
            process_operation=fragment["process"]["operation"],
            timestamp=fragment["timestamp"],
            parameters=fragment["process"].get("parameters", {}),
            quality_metrics=fragment["output"].get("quality_metrics", {}),
            metadata=fragment.get("metadata", {}),
        )
        dag.add_node(node)

    # Add edges based on previous_fragment_id
    for fragment in fragments:
        fragment_id = fragment["fragment_id"]
        previous_id = fragment["source"].get("previous_fragment_id")
        if previous_id:
            dag.add_edge(previous_id, fragment_id)

    return dag


def get_specimen_lineage(provenance_path: Path, specimen_sha256: str) -> Dict[str, Any]:
    """
    Get the full provenance lineage for a specific specimen.

    Args:
        provenance_path: Path to provenance.jsonl
        specimen_sha256: SHA256 hash of the specimen image

    Returns:
        Dictionary containing lineage information
    """
    dag = build_dag(provenance_path)

    # Find fragments related to this specimen
    related_fragments = []
    for node in dag.nodes.values():
        if specimen_sha256 in node.source_identifier or specimen_sha256 in node.output_identifier:
            related_fragments.append(node)

    # Get complete lineage for each fragment
    lineages = []
    for fragment in related_fragments:
        lineage = dag.get_lineage(fragment.fragment_id)
        lineages.append(
            {
                "fragment_id": fragment.fragment_id,
                "fragment_type": fragment.fragment_type,
                "chain": [
                    {
                        "fragment_id": node.fragment_id,
                        "type": node.fragment_type,
                        "operation": node.process_operation,
                        "timestamp": node.timestamp,
                    }
                    for node in lineage
                ],
            }
        )

    return {
        "specimen_sha256": specimen_sha256,
        "related_fragments": len(related_fragments),
        "lineages": lineages,
    }


def detect_inconsistencies(provenance_path: Path) -> List[Dict[str, Any]]:
    """
    Detect processing inconsistencies in the DAG.

    Checks for:
    - Orphaned fragments (nodes with missing parents)
    - Cycles (should not exist in a DAG)
    - Missing quality metrics
    - Timestamp ordering violations

    Args:
        provenance_path: Path to provenance.jsonl

    Returns:
        List of inconsistency reports
    """
    dag = build_dag(provenance_path)
    inconsistencies = []

    # Check for orphaned fragments (references to non-existent parents)
    for fragment_id, parent_id in dag.parents.items():
        if parent_id and parent_id not in dag.nodes:
            inconsistencies.append(
                {
                    "type": "orphaned_fragment",
                    "fragment_id": fragment_id,
                    "missing_parent_id": parent_id,
                    "severity": "warning",
                }
            )

    # Check for missing quality metrics
    for node in dag.nodes.values():
        if node.fragment_type in ["dwc_extraction", "qc_validation"] and not node.quality_metrics:
            inconsistencies.append(
                {
                    "type": "missing_quality_metrics",
                    "fragment_id": node.fragment_id,
                    "fragment_type": node.fragment_type,
                    "severity": "info",
                }
            )

    # Check timestamp ordering (parent should be before child)
    for edge in dag.edges:
        parent = dag.nodes.get(edge.from_fragment_id)
        child = dag.nodes.get(edge.to_fragment_id)
        if parent and child:
            if parent.timestamp > child.timestamp:
                inconsistencies.append(
                    {
                        "type": "timestamp_violation",
                        "parent_id": parent.fragment_id,
                        "parent_timestamp": parent.timestamp,
                        "child_id": child.fragment_id,
                        "child_timestamp": child.timestamp,
                        "severity": "error",
                    }
                )

    return inconsistencies


def visualize_lineage(provenance_path: Path, specimen_sha256: str, format: str = "text") -> str:
    """
    Visualize provenance lineage for a specimen.

    Args:
        provenance_path: Path to provenance.jsonl
        specimen_sha256: SHA256 hash of the specimen
        format: Output format ("text" or "json")

    Returns:
        Formatted lineage visualization
    """
    lineage_data = get_specimen_lineage(provenance_path, specimen_sha256)

    if format == "json":
        return json.dumps(lineage_data, indent=2)

    # Text format
    lines = [f"Provenance Lineage for Specimen: {specimen_sha256[:16]}..."]
    lines.append("=" * 80)

    for lineage in lineage_data["lineages"]:
        lines.append(f"\nChain for {lineage['fragment_type']}:")
        for i, node in enumerate(lineage["chain"]):
            indent = "  " * i
            arrow = "└─>" if i > 0 else "  "
            lines.append(
                f"{indent}{arrow} {node['type']}: {node['operation']} ({node['timestamp'][:19]})"
            )

    return "\n".join(lines)
