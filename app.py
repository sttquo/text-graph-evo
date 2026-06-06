import streamlit as st
import datetime
from textgraph.analyzer import TextGraphAnalyzer
from textgraph.nlp import NLPProcessor
from textgraph.graph_builder import DependencyGraphBuilder
from textgraph.visualizer import draw_dependency_graph, draw_evolution_graph

st.set_page_config(page_title="Text Graph Evolution", layout="wide")

st.title("Text Graph Evolution")
st.write("Сравнение двух версий текста через dependency-графы spaCy.")

# Only custom text inputs are supported
default_lang = "ru"
default_source = "Я люблю программирование."
default_target = "Мне нравится кодить."

lang_index = 0 if default_lang == "ru" else 1
lang = st.selectbox("Язык", ["ru", "en"], index=lang_index)
source_text = st.text_area("Исходный текст", height=120, value=default_source)
target_text = st.text_area("Изменённый текст", height=120, value=default_target)

if st.button("Проанализировать"):
    processor = NLPProcessor()
    analyzer = TextGraphAnalyzer()
    result = analyzer.analyze(source_text, target_text, lang=lang)

    source_doc = processor.parse_text(source_text, lang=lang)
    target_doc = processor.parse_text(target_text, lang=lang)
    source_graph = DependencyGraphBuilder.build_from_doc(source_doc)
    target_graph = DependencyGraphBuilder.build_from_doc(target_doc)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Граф исходного текста")
        fig1 = draw_dependency_graph(source_graph, title="Исходный текст")
        st.pyplot(fig1)
    with col2:
        st.subheader("Граф изменённого текста")
        fig2 = draw_dependency_graph(target_graph, title="Изменённый текст")
        st.pyplot(fig2)
    st.subheader("Граф эволюции")
    fig3 = draw_evolution_graph(source_graph, target_graph, result["node_diff"], result["edge_diff"], title="Эволюция графа")
    st.pyplot(fig3)

    st.subheader("Отчёт об изменениях")
    report_text = result["report"]
    st.text(report_text)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button("Скачать отчёт (.txt)", data=report_text, file_name=f"report_{timestamp}.txt", mime="text/plain")

    st.subheader("Выравнивание токенов (source_idx -> target_idx)")
    alignment = result.get("alignment", [])
    if alignment:
        rows = []
        for item in alignment:
            if isinstance(item, dict):
                rows.append({"source_idx": item.get("source_idx"), "target_idx": item.get("target_idx"), "method": item.get("method"), "score": item.get("score")})
            else:
                try:
                    a, b = item
                except Exception:
                    continue
                rows.append({"source_idx": a, "target_idx": b})
        if rows:
            st.table(rows)
        else:
            st.write("Совпадений не найдено")
    else:
        st.write("Совпадений не найдено")

    # Detailed lists
    nd = result.get("node_diff", {})
    ed = result.get("edge_diff", {})

    st.subheader("Детали изменений")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Изменённые узлы**")
        changed = nd.get("changed", [])
        if changed:
            st.table([
                {
                    "source_idx": it.get("source_idx"),
                    "target_idx": it.get("target_idx"),
                    "from": it.get("source_text"),
                    "to": it.get("target_text"),
                    "lemma": it.get("lemma"),
                    "pos": it.get("pos"),
                }
                for it in changed
            ])
        else:
            st.write("-")

        st.markdown("**Добавленные узлы**")
        added = nd.get("added", [])
        if added:
            st.table([
                {"idx": it.get("idx"), "text": it.get("text"), "lemma": it.get("lemma"), "pos": it.get("pos")} for it in added
            ])
        else:
            st.write("-")

    with c2:
        st.markdown("**Удалённые узлы**")
        removed = nd.get("removed", [])
        if removed:
            st.table([
                {"idx": it.get("idx"), "text": it.get("text"), "lemma": it.get("lemma"), "pos": it.get("pos")} for it in removed
            ])
        else:
            st.write("-")

        st.markdown("**Изменённые рёбра (примеры)**")
        changed_e = ed.get("changed", [])
        if changed_e:
            st.table([
                {"src": str(it.get("source_edge")), "tgt": str(it.get("target_edge")), "from": it.get("source_dep"), "to": it.get("target_dep")} for it in changed_e
            ])
        else:
            st.write("-")
