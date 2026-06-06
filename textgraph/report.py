from __future__ import annotations


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
