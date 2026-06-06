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

    edge_labels = {(u, v): data["dep"] for u, v, data in graph.edges(data=True)}
    nx.draw_networkx_edges(graph, pos, arrowstyle="-|>", arrowsize=18, ax=ax)
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=8, ax=ax)

    return fig


def draw_evolution_graph(source: nx.DiGraph, target: nx.DiGraph, node_diff: dict, edge_diff: dict, title: str = "Evolution") -> plt.Figure:
    """Нарисовать объединённый граф с подсветкой изменений.

    Статусы узлов: common, changed, added, removed
    Статусы рёбер: common, changed, added, removed
    """
    G = nx.DiGraph()

    # Add all nodes from source and target, prefer target attributes when available
    for n, data in source.nodes(data=True):
        G.add_node(n, **{**data, "status": "removed"})

    for n, data in target.nodes(data=True):
        if G.has_node(n):
            attrs = G.nodes[n]
            attrs.update(data)
            attrs["status"] = "common"
        else:
            G.add_node(n, **{**data, "status": "added"})

    # Update statuses for changed nodes
    for item in node_diff.get("changed", []):
        tgt = item.get("target_idx")
        if tgt in G.nodes:
            G.nodes[tgt]["status"] = "changed"

    # Mark removed nodes explicitly (they exist only in source)
    for item in node_diff.get("removed", []):
        idx = item.get("idx")
        if idx in G.nodes:
            G.nodes[idx]["status"] = "removed"

    # Add edges from both graphs, map status
    for u, v, data in source.edges(data=True):
        G.add_edge(u, v, dep=data.get("dep"), status="removed")

    for u, v, data in target.edges(data=True):
        if G.has_edge(u, v):
            G.edges[u, v]["status"] = "common"
            G.edges[u, v]["dep_target"] = data.get("dep")
        else:
            G.add_edge(u, v, dep=data.get("dep"), status="added")

    for item in edge_diff.get("changed", []):
        tgt_u, tgt_v = item["target_edge"]
        if G.has_edge(tgt_u, tgt_v):
            G.edges[tgt_u, tgt_v]["status"] = "changed"

    # Visualization
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_title(title)
    ax.axis("off")

    # build maps for changed node display
    changed_map = {item.get("target_idx"): (item.get("source_text"), item.get("target_text")) for item in node_diff.get("changed", [])}

    def node_label(n, d):
        text = d.get("text", "")
        lemma = d.get("lemma", "")
        pos = d.get("pos", "")
        if d.get("status") == "changed" and n in changed_map:
            src_text, tgt_text = changed_map[n]
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

    # edges with colors
    edge_color_map = {"common": "#555555", "changed": "#ff9900", "added": "#2e7d32", "removed": "#cc0000"}
    edge_colors = [edge_color_map.get(d.get("status", "common"), "#000") for _, _, d in G.edges(data=True)]
    nx.draw_networkx_edges(G, pos, arrowstyle="-|>", arrowsize=14, edge_color=edge_colors, ax=ax)

    edge_labels = {(u, v): d.get("dep") for u, v, d in G.edges(data=True)}
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
