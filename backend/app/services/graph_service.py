"""Graph service – builds and queries a NetworkX DiGraph from graph_edges."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import networkx as nx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import GraphEdge, AccountOrVPA


def build_graph(db: Session) -> nx.DiGraph:
    """Build a directed graph from all graph_edges rows."""
    G: nx.DiGraph = nx.DiGraph()
    for e in db.query(GraphEdge).all():
        G.add_edge(
            e.source_account,
            e.target_account,
            weight=e.amount,
            timestamp=e.timestamp,
            transaction_id=e.transaction_id,
            edge_id=e.id,
        )
    return G


def _parse_ts(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def get_graph_features(db: Session, receiver_id: str) -> Dict[str, Any]:
    """Compute graph features for a receiver – used by risk_service."""
    G = build_graph(db)
    if receiver_id not in G:
        return {
            "fan_in_count": 0, "fan_out_count": 0,
            "rapid_onward": False, "multi_hop_paths": [],
            "fan_in_accounts": [], "fan_out_accounts": [],
        }

    preds = list(set(G.predecessors(receiver_id)))
    succs = list(set(G.successors(receiver_id)))

    # Rapid onward: any inbound → outbound within threshold minutes
    rapid = False
    for u in preds:
        in_ts = _parse_ts(G[u][receiver_id].get("timestamp", ""))
        if not in_ts:
            continue
        for v in succs:
            out_ts = _parse_ts(G[receiver_id][v].get("timestamp", ""))
            if not out_ts:
                continue
            diff = (out_ts - in_ts).total_seconds() / 60
            if 0 < diff <= settings.RAPID_ONWARD_MINUTES:
                rapid = True
                break
        if rapid:
            break

    # Multi-hop paths (sample up to 3×3 pairs, cutoff 4)
    multi_hop: List[List[str]] = []
    for pred in preds[:3]:
        for succ in succs[:3]:
            try:
                for path in nx.all_simple_paths(G, pred, succ, cutoff=4):
                    if receiver_id in path and len(path) >= 3:
                        multi_hop.append(path)
                        break
            except nx.NetworkXError:
                continue
        if multi_hop:
            break

    return {
        "fan_in_count": len(preds),
        "fan_out_count": len(succs),
        "rapid_onward": rapid,
        "multi_hop_paths": multi_hop,
        "fan_in_accounts": preds,
        "fan_out_accounts": succs,
    }


def get_account_network(
    db: Session, account_id: str, depth: int = 2
) -> Optional[Dict[str, Any]]:
    """Return ego-network dict for the /network endpoint. None if unknown."""
    # Must exist in accounts_or_vpas OR appear in graph_edges
    acc_row = db.get(AccountOrVPA, account_id)
    if acc_row is None:
        edge_check = (
            db.query(GraphEdge)
            .filter(
                (GraphEdge.source_account == account_id)
                | (GraphEdge.target_account == account_id)
            )
            .first()
        )
        if edge_check is None:
            return None

    G = build_graph(db)
    if account_id not in G:
        return None

    # BFS to collect ego nodes
    ego_nodes: set = {account_id}
    frontier: set = {account_id}
    for _ in range(depth):
        nxt: set = set()
        for n in frontier:
            nxt.update(G.successors(n))
            nxt.update(G.predecessors(n))
        ego_nodes.update(nxt)
        frontier = nxt

    # Build nodes
    nodes = []
    for nid in ego_nodes:
        a = db.get(AccountOrVPA, nid)
        label = (a.vpa if a and a.vpa else nid)
        report_status = (a.report_status if a else "NONE") or "NONE"
        risk_level = "HIGH" if report_status in ("REPORTED", "VERIFIED") else "LOW"
        flags: List[str] = []
        if report_status in ("REPORTED", "VERIFIED"):
            flags.append("REPORTED")
        in_deg = len(set(G.predecessors(nid))) if nid in G else 0
        out_deg = len(set(G.successors(nid))) if nid in G else 0
        if in_deg >= settings.FAN_IN_MIN:
            flags.append("FAN_IN")
            if risk_level == "LOW":
                risk_level = "MEDIUM"
        if out_deg >= settings.FAN_OUT_MIN:
            flags.append("FAN_OUT")
            if risk_level == "LOW":
                risk_level = "MEDIUM"
        nodes.append({
            "id": nid, "label": label,
            "risk_level": risk_level, "report_status": report_status,
            "flags": flags,
        })

    # Build edges
    edges = []
    for u, v, data in G.edges(data=True):
        if u in ego_nodes and v in ego_nodes:
            edges.append({
                "id": data.get("edge_id", 0),
                "source": u, "target": v,
                "amount": data.get("weight", 0),
                "timestamp": data.get("timestamp", ""),
                "transaction_id": data.get("transaction_id"),
                "direction": f"{u}->{v}",
            })

    # Patterns
    patterns = _detect_patterns(G, account_id)

    legend = {
        "node_colors": {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red"},
        "edge_direction": "Arrow shows fund flow direction",
        "disclaimer": "Graph connections are indicators, NOT proof of wrongdoing.",
        "patterns": {
            "FAN_IN": f">= {settings.FAN_IN_MIN} distinct senders",
            "FAN_OUT": f">= {settings.FAN_OUT_MIN} distinct recipients",
            "RAPID_ONWARD": f"Forwarded within {settings.RAPID_ONWARD_MINUTES} min",
            "MULTI_HOP": "3+ account chain",
        },
    }

    return {
        "center": account_id,
        "nodes": nodes, "edges": edges,
        "patterns": patterns, "legend": legend,
    }


def _detect_patterns(G: nx.DiGraph, account_id: str) -> List[Dict[str, Any]]:
    patterns: List[Dict[str, Any]] = []
    if account_id not in G:
        return patterns

    preds = list(set(G.predecessors(account_id)))
    succs = list(set(G.successors(account_id)))
    DISCLAIMER = "A graph connection is an indicator, NOT proof of wrongdoing."

    if len(preds) >= settings.FAN_IN_MIN:
        patterns.append({
            "pattern": "FAN_IN",
            "accounts": preds,
            "explanation": (
                f"{account_id} received from {len(preds)} distinct senders. {DISCLAIMER}"
            ),
        })

    if len(succs) >= settings.FAN_OUT_MIN:
        patterns.append({
            "pattern": "FAN_OUT",
            "accounts": succs,
            "explanation": (
                f"{account_id} sent to {len(succs)} distinct accounts. {DISCLAIMER}"
            ),
        })

    # Rapid onward
    for u in preds:
        in_ts = _parse_ts(G[u][account_id].get("timestamp", ""))
        if not in_ts:
            continue
        for v in succs:
            out_ts = _parse_ts(G[account_id][v].get("timestamp", ""))
            if not out_ts:
                continue
            diff = (out_ts - in_ts).total_seconds() / 60
            if 0 < diff <= settings.RAPID_ONWARD_MINUTES:
                patterns.append({
                    "pattern": "RAPID_ONWARD",
                    "accounts": [account_id, v],
                    "explanation": (
                        f"Funds forwarded to {v} within {diff:.0f} min of receipt. {DISCLAIMER}"
                    ),
                })
                break
        else:
            continue
        break

    # Multi-hop
    for pred in preds[:5]:
        for succ in succs[:5]:
            try:
                for path in nx.all_simple_paths(G, pred, succ, cutoff=4):
                    if account_id in path and len(path) >= 3:
                        patterns.append({
                            "pattern": "MULTI_HOP",
                            "accounts": path,
                            "explanation": (
                                f"Multi-hop flow: {' -> '.join(path)}. {DISCLAIMER}"
                            ),
                        })
                        return patterns
            except nx.NetworkXError:
                continue

    return patterns
