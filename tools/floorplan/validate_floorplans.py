#!/usr/bin/env python3
"""Validate generated floor-plan assets and exercise graph routing."""

from __future__ import annotations

import argparse
import heapq
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest",
        nargs="?",
        type=Path,
        default=(
            PROJECT_ROOT
            / "assets"
            / "floorplans"
            / "taipei_main_station"
            / "manifest.json"
        ),
    )
    return parser.parse_args()


def shortest_path(
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    start: str,
    end: str,
    accessible_only: bool,
) -> list[str]:
    adjacency: dict[str, list[tuple[str, float]]] = {node_id: [] for node_id in nodes}
    for edge in edges:
        if accessible_only and not edge["accessible"]:
            continue
        adjacency[edge["from"]].append((edge["to"], float(edge["cost"])))
        if edge["bidirectional"]:
            adjacency[edge["to"]].append((edge["from"], float(edge["cost"])))

    queue: list[tuple[float, str]] = [(0.0, start)]
    distance = {start: 0.0}
    previous: dict[str, str] = {}
    while queue:
        current_distance, current = heapq.heappop(queue)
        if current_distance != distance.get(current):
            continue
        if current == end:
            break
        for neighbour, cost in adjacency[current]:
            candidate = current_distance + cost
            if candidate < distance.get(neighbour, float("inf")):
                distance[neighbour] = candidate
                previous[neighbour] = current
                heapq.heappush(queue, (candidate, neighbour))

    if end not in distance:
        return []
    result = [end]
    while result[-1] != start:
        result.append(previous[result[-1]])
    return list(reversed(result))


def main() -> None:
    manifest_path = parse_args().manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    asset_root = PROJECT_ROOT

    assert manifest["reviewStatus"] == "prototype-needs-on-site-validation"
    assert [floor["id"] for floor in manifest["floors"]] == ["B1", "B2", "B3", "B4"]

    for floor in manifest["floors"]:
        assert floor["width"] > 0 and floor["height"] > 0
        for field in ("image", "walkableMask"):
            path = asset_root / floor[field]
            assert path.is_file(), f"Missing {field}: {path}"

    nodes = {node["id"]: node for node in manifest["nodes"]}
    assert len(nodes) == len(manifest["nodes"]), "Duplicate node id"
    for node in nodes.values():
        assert 0.0 <= node["position"]["x"] <= 1.0
        assert 0.0 <= node["position"]["y"] <= 1.0
        assert node["floorId"] in {"B1", "B2", "B3", "B4"}

    edge_ids: set[str] = set()
    for edge in manifest["edges"]:
        assert edge["id"] not in edge_ids, f"Duplicate edge id: {edge['id']}"
        edge_ids.add(edge["id"])
        assert edge["from"] in nodes and edge["to"] in nodes
        assert float(edge["cost"]) > 0

    for destination in manifest["destinations"]:
        assert destination["nodeId"] in nodes

    routes = {
        "bannan": shortest_path(
            nodes, manifest["edges"], "b1_m4_entry", "b3_bl_platform", False
        ),
        "red_regular": shortest_path(
            nodes, manifest["edges"], "b1_m4_entry", "b4_r_platform", False
        ),
        "red_accessible": shortest_path(
            nodes, manifest["edges"], "b1_m4_entry", "b4_r_platform", True
        ),
    }
    assert all(routes.values()), "A demo destination is unreachable"
    assert "b4_r_elevator" in routes["red_accessible"]
    assert not any(nodes[node_id]["kind"] == "stairs" for node_id in routes["red_accessible"])

    print(
        json.dumps(
            {
                "valid": True,
                "floors": len(manifest["floors"]),
                "nodes": len(nodes),
                "edges": len(manifest["edges"]),
                "routes": routes,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
