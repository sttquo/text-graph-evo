from __future__ import annotations

import matplotlib.pyplot as plt
import networkx as nx


def draw_dependency_graph(graph: nx.DiGraph, title: str = "") -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(title)
    ax.axis("off")

    labels = {
        node: f"{data['text']}\n{data['lemma']}\n{data['pos']}"
        for node, data in graph.nodes(data=True)
    }

    try:
        pos = nx.nx_pydot.graphviz_layout(graph, prog="dot")
    except Exception:
        pos = nx.spring_layout(graph, seed=42)

    nx.draw_networkx_nodes(graph, pos, node_color="#f0f0f0", edgecolors="#333", node_size=1600, ax=ax)
    nx.draw_networkx_labels(graph, pos, labels=labels, font_size=8, ax=ax)

    # show directed edges (head -> dependent) with arrows and labels
    edge_labels = {(u, v): data.get("label") or data.get("dep") for u, v, data in graph.edges(data=True)}
    nx.draw_networkx_edges(graph, pos, arrowstyle="-|>", arrowsize=18, ax=ax, arrows=True)
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=8, ax=ax)

    return fig


def draw_evolution_graph(source: nx.DiGraph, target: nx.DiGraph, node_diff: dict, edge_diff: dict, title: str = "Evolution") -> plt.Figure:
    """Нарисовать объединённый граф с подсветкой изменений.

    Статусы узлов: common, changed, added, removed
    Статусы рёбер: common, changed, added, removed
    """
    # Use separate nodes for old/new tokens to avoid accidental merging by numeric idx
    G = nx.DiGraph()

    # Add old (source) nodes with prefix 'old_'
    for n, data in source.nodes(data=True):
        G.add_node(f"old_{n}", **{**data, "status": "removed", "side": "old"})

    # Add new (target) nodes with prefix 'new_'
    for n, data in target.nodes(data=True):
        G.add_node(f"new_{n}", **{**data, "status": "added", "side": "new"})

    # Update statuses for changed nodes (mark the new-side node as changed)
    for item in node_diff.get("changed", []):
        tgt = item.get("target_idx")
        key = f"new_{tgt}"
        if key in G.nodes:
            G.nodes[key]["status"] = "changed"

    # Mark removed nodes explicitly (they exist only in source)
    for item in node_diff.get("removed", []):
        idx = item.get("idx")
        key = f"old_{idx}"
        if key in G.nodes:
            G.nodes[key]["status"] = "removed"

    # Add dependency edges inside old/new graphs (directed head -> dependent)
    for u, v, data in source.edges(data=True):
        G.add_edge(f"old_{u}", f"old_{v}", dep=data.get("dep"), label=data.get("label") or data.get("dep"), status="removed")

    for u, v, data in target.edges(data=True):
        if G.has_edge(f"new_{u}", f"new_{v}"):
            # shouldn't normally happen, but ensure status
            G.edges[f"new_{u}", f"new_{v}"]["status"] = "common"
        else:
            G.add_edge(f"new_{u}", f"new_{v}", dep=data.get("dep"), label=data.get("label") or data.get("dep"), status="added")

    # Mark edges that changed according to edge_diff (these refer to target edges)
    for item in edge_diff.get("changed", []):
        tgt_u, tgt_v = item["target_edge"]
        key_u = f"new_{tgt_u}"
        key_v = f"new_{tgt_v}"
        if G.has_edge(key_u, key_v):
            G.edges[key_u, key_v]["status"] = "changed"

    # Add match edges between old and new nodes to show token alignment
    # These are auxiliary undirected/dashed edges of type 'match' (old_idx -> new_idx)
    for item in node_diff.get("common", []) + node_diff.get("changed", []):
        src_idx = item.get("source_idx")
        tgt_idx = item.get("target_idx")
        old_key = f"old_{src_idx}"
        new_key = f"new_{tgt_idx}"
        if G.has_node(old_key) and G.has_node(new_key):
            # match edges connect the corresponding tokens across versions
            G.add_edge(old_key, new_key, dep="match", label="match", status="match")

    # Visualization
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_title(title)
    ax.axis("off")

    # build maps for changed node display (map new_idx -> (source_text, target_text))
    changed_map = {item.get("target_idx"): (item.get("source_text"), item.get("target_text")) for item in node_diff.get("changed", [])}

    def node_label(n, d):
        text = d.get("text", "")
        lemma = d.get("lemma", "")
        pos = d.get("pos", "")
        # n is like 'new_3' or 'old_2' — extract numeric suffix for lookup when needed
        if d.get("status") == "changed":
            # try to use changed_map with numeric idx from new-side nodes
            if isinstance(n, str) and n.startswith("new_"):
                num = int(n.split("new_")[1])
                if num in changed_map:
                    src_text, tgt_text = changed_map[num]
                    return f"{tgt_text}\n{lemma} ({pos})\n{src_text} → {tgt_text}"
        if d.get("status") == "added":
            return f"{text}\n{lemma} ({pos})\n[added]"
        if d.get("status") == "removed":
            return f"{text}\n{lemma} ({pos})\n[removed]"
        return f"{text}\n{lemma} ({pos})"

    labels = {n: node_label(n, d) for n, d in G.nodes(data=True)}

    try:
        pos = nx.nx_pydot.graphviz_layout(G, prog="dot")
    except Exception:
        pos = nx.spring_layout(G, seed=42)

    # node colors
    color_map = {
        "common": "#9fc5e8",
        "changed": "#f6b26b",
        "added": "#b6d7a8",
        "removed": "#f4cccc",
    }
    node_colors = [color_map.get(d.get("status", "common"), "#ffffff") for _, d in G.nodes(data=True)]

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, edgecolors="#333", node_size=1400, ax=ax)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, ax=ax)

    # edges with colors — keep direction head -> dependent for dependency edges
    edge_color_map = {"common": "#555555", "changed": "#ff9900", "added": "#2e7d32", "removed": "#cc0000", "match": "#888888"}

    # Separate dependency edges (status != 'match') and match edges (status == 'match')
    dep_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("status") != "match"]
    dep_edge_colors = [edge_color_map.get(G.edges[u, v].get("status", "common"), "#000") for u, v in dep_edges]

    # Draw dependency edges with arrows (head -> dependent)
    if dep_edges:
        nx.draw_networkx_edges(G, pos, edgelist=dep_edges, arrowstyle="-|>", arrowsize=14, edge_color=dep_edge_colors, ax=ax, arrows=True)

    # Draw match edges as dashed lines without arrows to show alignment between old/new
    match_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("status") == "match"]
    if match_edges:
        nx.draw_networkx_edges(G, pos, edgelist=match_edges, style="dashed", edge_color=edge_color_map.get("match"), ax=ax, arrows=False)

    # Edge labels use 'label' (or 'dep')
    edge_labels = {(u, v): d.get("label") or d.get("dep") for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7, ax=ax)

    # Legend
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D

    # translate legend labels to Russian
    node_labels_ru = [("Сохранено", "#9fc5e8"), ("Изменено", "#f6b26b"), ("Добавлено", "#b6d7a8"), ("Удалено", "#f4cccc")]
    edge_labels_ru = [("Сохранено", "#555555"), ("Изменено", "#ff9900"), ("Добавлено", "#2e7d32"), ("Удалено", "#cc0000")]

    node_legend = [Patch(facecolor=c, edgecolor="#333", label=label) for label, c in node_labels_ru]
    edge_legend = [Line2D([0], [0], color=c, lw=2, label=label) for label, c in edge_labels_ru]

    # place legends
    ax.legend(handles=node_legend + edge_legend, loc="lower left", bbox_to_anchor=(0, -0.15), ncol=2)

    return fig
