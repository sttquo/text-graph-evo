from __future__ import annotations

import networkx as nx


class GraphDiff:
    """Анализ изменений между двумя dependency-графами."""

    @staticmethod
    def normalize_alignment(alignment: list[object]) -> list[tuple[int, int]]:
        if not alignment:
            return []
        first = alignment[0]
        if isinstance(first, dict):
            return [(item["source_idx"], item["target_idx"]) for item in alignment]
        return alignment

    @staticmethod
    def diff_nodes(source: nx.DiGraph, target: nx.DiGraph, alignment: list[object]) -> dict:
        normalized = GraphDiff.normalize_alignment(alignment)
        mapped_target = {src: tgt for src, tgt in normalized}
        aligned_source = set(mapped_target)
        aligned_target = set(mapped_target.values())

        common = []
        changed = []
        for src_idx, tgt_idx in normalized:
            src_data = source.nodes[src_idx]
            tgt_data = target.nodes[tgt_idx]
            node_info = {
                "source_idx": src_idx,
                "target_idx": tgt_idx,
                "source_text": src_data["text"],
                "target_text": tgt_data["text"],
                "source_dep": src_data["dep"],
                "target_dep": tgt_data["dep"],
                "lemma": src_data["lemma"],
                "pos": src_data["pos"],
            }
            if src_data["text"] != tgt_data["text"] or src_data["pos"] != tgt_data["pos"]:
                changed.append(node_info)
            else:
                common.append(node_info)

        removed = [
            {"idx": idx, **source.nodes[idx]}
            for idx in source.nodes()
            if idx not in aligned_source
        ]
        added = [
            {"idx": idx, **target.nodes[idx]}
            for idx in target.nodes()
            if idx not in aligned_target
        ]

        role_changes = []
        for src_idx, tgt_idx in normalized:
            src_data = source.nodes[src_idx]
            tgt_data = target.nodes[tgt_idx]
            if src_data["dep"] != tgt_data["dep"] or src_data["head"] != tgt_data["head"]:
                role_changes.append({
                    "source_idx": src_idx,
                    "target_idx": tgt_idx,
                    "source_dep": src_data["dep"],
                    "target_dep": tgt_data["dep"],
                    "source_head": src_data["head"],
                    "target_head": tgt_data["head"],
                })

        return {
            "common": common,
            "changed": changed,
            "added": added,
            "removed": removed,
            "role_changes": role_changes,
        }

    @staticmethod
    def diff_edges(source: nx.DiGraph, target: nx.DiGraph, alignment: list[object]) -> dict:
        normalized = GraphDiff.normalize_alignment(alignment)
        source_to_target = {src: tgt for src, tgt in normalized}
        target_to_source = {tgt: src for src, tgt in normalized}

        common = []
        changed = []
        removed = []
        added = []

        seen_target_edges = set()

        for u, v, data in source.edges(data=True):
            if u in source_to_target and v in source_to_target:
                mapped_u = source_to_target[u]
                mapped_v = source_to_target[v]
                if target.has_edge(mapped_u, mapped_v):
                    seen_target_edges.add((mapped_u, mapped_v))
                    target_dep = target.edges[mapped_u, mapped_v]["dep"]
                    edge_info = {
                        "source_edge": (u, v),
                        "target_edge": (mapped_u, mapped_v),
                        "source_dep": data["dep"],
                        "target_dep": target_dep,
                    }
                    if data["dep"] == target_dep:
                        common.append(edge_info)
                    else:
                        changed.append(edge_info)
                else:
                    removed.append({"source_edge": (u, v), "source_dep": data["dep"]})
            else:
                removed.append({"source_edge": (u, v), "source_dep": data["dep"]})

        for u, v, data in target.edges(data=True):
            if (u, v) in seen_target_edges:
                continue
            if u in target_to_source and v in target_to_source:
                mapped_u = target_to_source[u]
                mapped_v = target_to_source[v]
                if source.has_edge(mapped_u, mapped_v):
                    continue
            added.append({"target_edge": (u, v), "target_dep": data["dep"]})

        return {
            "common": common,
            "changed": changed,
            "added": added,
            "removed": removed,
        }
