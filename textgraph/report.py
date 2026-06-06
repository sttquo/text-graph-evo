from __future__ import annotations
import networkx as nx


class ChangeReport:
    """Формирует текстовый отчёт о различиях между двумя графами."""

    @staticmethod
    def summarize(node_diff: dict, edge_diff: dict) -> str:
        lines = []
        lines.append("=== Сводка изменений ===")
        lines.append(f"Узлов — сохранено: {len(node_diff.get('common', []))}, изменено: {len(node_diff.get('changed', []))}, добавлено: {len(node_diff.get('added', []))}, удалено: {len(node_diff.get('removed', []))}")
        lines.append(f"Рёбер — сохранено: {len(edge_diff.get('common', []))}, изменено: {len(edge_diff.get('changed', []))}, добавлено: {len(edge_diff.get('added', []))}, удалено: {len(edge_diff.get('removed', []))}")

        if node_diff.get('changed'):
            lines.append("")
            lines.append("Изменённые узлы (примеры):")
            for item in node_diff.get('changed', [])[:8]:
                lines.append(f" - {item.get('source_text')}  →  {item.get('target_text')} (lemma={item.get('lemma')}, pos={item.get('pos')})")

        if node_diff.get('added'):
            lines.append("")
            lines.append("Добавленные узлы (примеры):")
            for item in node_diff.get('added', [])[:8]:
                lines.append(f" - {item.get('text')} ({item.get('lemma')}, {item.get('pos')})")

        if node_diff.get('removed'):
            lines.append("")
            lines.append("Удалённые узлы (примеры):")
            for item in node_diff.get('removed', [])[:8]:
                lines.append(f" - {item.get('text')} ({item.get('lemma')}, {item.get('pos')})")

        if edge_diff.get('changed'):
            lines.append("")
            lines.append("Изменённые рёбра (примеры):")
            for item in edge_diff.get('changed', [])[:8]:
                src_e = item.get('source_edge')
                tgt_e = item.get('target_edge')
                lines.append(f" - {src_e}:{item.get('source_dep')}  →  {tgt_e}:{item.get('target_dep')}")

        return "\n".join(lines)


def build_change_metrics(node_diff: dict, edge_diff: dict) -> dict:
    """Подготавливает метрики для краткой сводки изменений."""
    return {
        "nodes_saved": len(node_diff.get("common", [])),
        "nodes_changed": len(node_diff.get("changed", [])),
        "nodes_added": len(node_diff.get("added", [])),
        "nodes_removed": len(node_diff.get("removed", [])),
        "edges_saved": len(edge_diff.get("common", [])),
        "edges_changed": len(edge_diff.get("changed", [])),
        "edges_added": len(edge_diff.get("added", [])),
        "edges_removed": len(edge_diff.get("removed", [])),
    }


def build_token_changes_table(node_diff: dict, source_graph: nx.DiGraph, target_graph: nx.DiGraph) -> list[dict]:
    """Подготавливает таблицу изменений токенов для отображения в Streamlit."""
    rows = []
    
    # Сохранённые токены
    for item in node_diff.get("common", []):
        src_idx = item.get("source_idx")
        tgt_idx = item.get("target_idx")
        src_node = source_graph.nodes[src_idx] if src_idx in source_graph.nodes else {}
        tgt_node = target_graph.nodes[tgt_idx] if tgt_idx in target_graph.nodes else {}
        
        rows.append({
            "Тип изменения": "сохранено",
            "Было": src_node.get("text", "—"),
            "Стало": tgt_node.get("text", "—"),
            "Лемма": src_node.get("lemma", "—"),
            "Часть речи": src_node.get("pos", "—"),
            "Синтаксическая роль": src_node.get("dep", "—"),
            "Комментарий": "токен сохранился",
        })
    
    # Изменённые токены
    for item in node_diff.get("changed", []):
        src_idx = item.get("source_idx")
        tgt_idx = item.get("target_idx")
        src_node = source_graph.nodes[src_idx] if src_idx in source_graph.nodes else {}
        tgt_node = target_graph.nodes[tgt_idx] if tgt_idx in target_graph.nodes else {}
        
        rows.append({
            "Тип изменения": "изменено",
            "Было": src_node.get("text", "—"),
            "Стало": tgt_node.get("text", "—"),
            "Лемма": item.get("lemma", "—"),
            "Часть речи": item.get("pos", "—"),
            "Синтаксическая роль": src_node.get("dep", "—"),
            "Комментарий": "токен сопоставлен с другим токеном",
        })
    
    # Удалённые токены
    for item in node_diff.get("removed", []):
        rows.append({
            "Тип изменения": "удалено",
            "Было": item.get("text", "—"),
            "Стало": "—",
            "Лемма": item.get("lemma", "—"),
            "Часть речи": item.get("pos", "—"),
            "Синтаксическая роль": item.get("dep", "—"),
            "Комментарий": "элемент был удалён при редактировании",
        })
    
    # Добавленные токены
    for item in node_diff.get("added", []):
        rows.append({
            "Тип изменения": "добавлено",
            "Было": "—",
            "Стало": item.get("text", "—"),
            "Лемма": item.get("lemma", "—"),
            "Часть речи": item.get("pos", "—"),
            "Синтаксическая роль": item.get("dep", "—"),
            "Комментарий": "новый элемент в изменённом предложении",
        })
    
    return rows


def build_edge_changes_table(edge_diff: dict, source_graph: nx.DiGraph, target_graph: nx.DiGraph) -> list[dict]:
    """Подготавливает таблицу изменений связей для отображения в Streamlit."""
    rows = []
    
    # Сохранённые рёбра
    for item in edge_diff.get("common", []):
        src_edge = item.get("source_edge", (None, None))
        src_dep = item.get("source_dep", "—")
        src_u, src_v = src_edge
        
        src_u_text = source_graph.nodes[src_u].get("text", "?") if src_u in source_graph.nodes else "?"
        src_v_text = source_graph.nodes[src_v].get("text", "?") if src_v in source_graph.nodes else "?"
        
        rows.append({
            "Тип изменения": "сохранено",
            "Было": f"{src_u_text} → {src_v_text}",
            "Стало": f"{src_u_text} → {src_v_text}",
            "Тип зависимости": src_dep,
            "Комментарий": "связь сохранилась",
        })
    
    # Изменённые рёбра
    for item in edge_diff.get("changed", []):
        src_edge = item.get("source_edge", (None, None))
        tgt_edge = item.get("target_edge", (None, None))
        src_dep = item.get("source_dep", "—")
        tgt_dep = item.get("target_dep", "—")
        
        src_u, src_v = src_edge
        tgt_u, tgt_v = tgt_edge
        
        src_u_text = source_graph.nodes[src_u].get("text", "?") if src_u in source_graph.nodes else "?"
        src_v_text = source_graph.nodes[src_v].get("text", "?") if src_v in source_graph.nodes else "?"
        tgt_u_text = target_graph.nodes[tgt_u].get("text", "?") if tgt_u in target_graph.nodes else "?"
        tgt_v_text = target_graph.nodes[tgt_v].get("text", "?") if tgt_v in target_graph.nodes else "?"
        
        rows.append({
            "Тип изменения": "изменено",
            "Было": f"{src_u_text} → {src_v_text}",
            "Стало": f"{tgt_u_text} → {tgt_v_text}",
            "Тип зависимости": f"{src_dep} → {tgt_dep}",
            "Комментарий": "связь изменилась",
        })
    
    # Удалённые рёбра
    for item in edge_diff.get("removed", []):
        src_edge = item.get("source_edge", (None, None))
        src_dep = item.get("source_dep", "—")
        src_u, src_v = src_edge
        
        src_u_text = source_graph.nodes[src_u].get("text", "?") if src_u in source_graph.nodes else "?"
        src_v_text = source_graph.nodes[src_v].get("text", "?") if src_v in source_graph.nodes else "?"
        
        comment = {
            "nsubj": "удалено подлежащее",
            "obj": "удален дополнение",
            "advmod": "удалено обстоятельство",
            "amod": "удален признак",
            "obl": "удалено косвенное дополнение",
        }.get(src_dep, "удалена связь")
        
        rows.append({
            "Тип изменения": "удалено",
            "Было": f"{src_u_text} → {src_v_text}",
            "Стало": "—",
            "Тип зависимости": src_dep,
            "Комментарий": comment,
        })
    
    # Добавленные рёбра
    for item in edge_diff.get("added", []):
        tgt_edge = item.get("target_edge", (None, None))
        tgt_dep = item.get("target_dep", "—")
        tgt_u, tgt_v = tgt_edge
        
        tgt_u_text = target_graph.nodes[tgt_u].get("text", "?") if tgt_u in target_graph.nodes else "?"
        tgt_v_text = target_graph.nodes[tgt_v].get("text", "?") if tgt_v in target_graph.nodes else "?"
        
        comment = {
            "nsubj": "добавлено подлежащее",
            "obj": "добавлено дополнение",
            "advmod": "добавлено обстоятельство",
            "amod": "добавлен признак",
            "obl": "добавлено косвенное дополнение",
        }.get(tgt_dep, "добавлена связь")
        
        rows.append({
            "Тип изменения": "добавлено",
            "Было": "—",
            "Стало": f"{tgt_u_text} → {tgt_v_text}",
            "Тип зависимости": tgt_dep,
            "Комментарий": comment,
        })
    
    return rows


def build_factual_summary(node_diff: dict, edge_diff: dict, source_graph: nx.DiGraph, target_graph: nx.DiGraph) -> str:
    """Генерирует фактическое описание структурных изменений (только данные из diff)."""
    
    # Метрики
    n_saved = len(node_diff.get("common", []))
    n_changed = len(node_diff.get("changed", []))
    n_added = len(node_diff.get("added", []))
    n_removed = len(node_diff.get("removed", []))
    
    e_saved = len(edge_diff.get("common", []))
    e_changed = len(edge_diff.get("changed", []))
    e_added = len(edge_diff.get("added", []))
    e_removed = len(edge_diff.get("removed", []))
    
    # Проверяем, есть ли вообще изменения
    total_changes = n_changed + n_added + n_removed + e_changed + e_added + e_removed
    
    if total_changes == 0:
        return "Структурных изменений не обнаружено: токены и dependency-связи совпадают."
    
    lines = []
    
    # Определяем тип редактирования
    has_additions = n_added > 0 or e_added > 0
    has_removals = n_removed > 0 or e_removed > 0
    
    if has_additions and has_removals:
        lines.append("Текст был отредактирован: часть элементов удалена, часть добавлена.")
    elif has_additions and not has_removals:
        lines.append("В изменённом тексте появились новые элементы и новые dependency-связи.")
    elif has_removals and not has_additions:
        lines.append("Из исходного текста были удалены элементы и связанные с ними dependency-связи.")
    
    # Основная статистика
    lines.append(f"При редактировании сохранено {n_saved} токен(ов), добавлено {n_added}, удалено {n_removed}.")
    lines.append(f"Сохранено {e_saved} синтаксических связей, добавлено {e_added}, удалено {e_removed}.")
    
    # Детали добавленных токенов
    added_tokens = node_diff.get("added", [])
    if added_tokens:
        added_text = ", ".join([item.get("text", "?") for item in added_tokens])
        lines.append(f"Добавленные токены: {added_text}.")
    
    # Детали удалённых токенов
    removed_tokens = node_diff.get("removed", [])
    if removed_tokens:
        removed_text = ", ".join([item.get("text", "?") for item in removed_tokens])
        lines.append(f"Удалённые токены: {removed_text}.")
    
    # Детали добавленных связей
    added_edges = edge_diff.get("added", [])
    if added_edges:
        edge_strs = []
        for item in added_edges:
            tgt_edge = item.get("target_edge", (None, None))
            tgt_dep = item.get("target_dep", "?")
            tgt_u, tgt_v = tgt_edge
            
            if tgt_u in target_graph.nodes and tgt_v in target_graph.nodes:
                tgt_u_text = target_graph.nodes[tgt_u].get("text", "?")
                tgt_v_text = target_graph.nodes[tgt_v].get("text", "?")
                edge_strs.append(f"{tgt_u_text} → {tgt_v_text} ({tgt_dep})")
        
        if edge_strs:
            added_edges_text = ", ".join(edge_strs)
            lines.append(f"Добавленные связи: {added_edges_text}.")
    
    # Детали удалённых связей
    removed_edges = edge_diff.get("removed", [])
    if removed_edges:
        edge_strs = []
        for item in removed_edges:
            src_edge = item.get("source_edge", (None, None))
            src_dep = item.get("source_dep", "?")
            src_u, src_v = src_edge
            
            if src_u in source_graph.nodes and src_v in source_graph.nodes:
                src_u_text = source_graph.nodes[src_u].get("text", "?")
                src_v_text = source_graph.nodes[src_v].get("text", "?")
                edge_strs.append(f"{src_u_text} → {src_v_text} ({src_dep})")
        
        if edge_strs:
            removed_edges_text = ", ".join(edge_strs)
            lines.append(f"Удалённые связи: {removed_edges_text}.")
    
    return " ".join(lines)
