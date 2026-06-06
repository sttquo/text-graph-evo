import streamlit as st
import datetime
from textgraph.analyzer import TextGraphAnalyzer
from textgraph.nlp import NLPProcessor
from textgraph.graph_builder import DependencyGraphBuilder
from textgraph.visualizer import draw_dependency_graph
from textgraph.report import (
    build_change_metrics,
    build_token_changes_table,
    build_edge_changes_table,
    build_human_summary,
)

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

    # --- Графы зависимостей ---
    st.markdown("## Графы зависимостей")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Граф исходного текста")
        fig1 = draw_dependency_graph(source_graph, title="Исходный текст")
        st.pyplot(fig1)
    with col2:
        st.subheader("Граф изменённого текста")
        fig2 = draw_dependency_graph(target_graph, title="Изменённый текст")
        st.pyplot(fig2)

    # --- Сводка изменений ---
    st.markdown("## Краткая сводка изменений")
    node_diff = result.get("node_diff", {})
    edge_diff = result.get("edge_diff", {})
    metrics = build_change_metrics(node_diff, edge_diff)

    # Три столбца для ключевых метрик
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Токены (сохранено)", metrics["nodes_saved"])
    with col2:
        st.metric("Токены (изменено)", metrics["nodes_changed"])
    with col3:
        st.metric("Токены (добавлено)", metrics["nodes_added"])
    with col4:
        st.metric("Токены (удалено)", metrics["nodes_removed"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Связи (сохранено)", metrics["edges_saved"])
    with col2:
        st.metric("Связи (изменено)", metrics["edges_changed"])
    with col3:
        st.metric("Связи (добавлено)", metrics["edges_added"])
    with col4:
        st.metric("Связи (удалено)", metrics["edges_removed"])

    # --- Таблица изменений токенов ---
    st.markdown("## Изменения токенов")
    token_rows = build_token_changes_table(node_diff, source_graph, target_graph)
    if token_rows:
        st.dataframe(
            token_rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Тип изменения": st.column_config.Column(width="auto"),
                "Было": st.column_config.Column(width="auto"),
                "Стало": st.column_config.Column(width="auto"),
                "Лемма": st.column_config.Column(width="auto"),
                "Часть речи": st.column_config.Column(width="auto"),
                "Синтаксическая роль": st.column_config.Column(width="auto"),
                "Комментарий": st.column_config.Column(width="auto"),
            },
        )
    else:
        st.write("Изменений токенов не обнаружено.")

    # --- Таблица изменений связей ---
    st.markdown("## Изменения связей")
    edge_rows = build_edge_changes_table(edge_diff, source_graph, target_graph)
    if edge_rows:
        st.dataframe(
            edge_rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Тип изменения": st.column_config.Column(width="auto"),
                "Было": st.column_config.Column(width="auto"),
                "Стало": st.column_config.Column(width="auto"),
                "Тип зависимости": st.column_config.Column(width="auto"),
                "Комментарий": st.column_config.Column(width="auto"),
            },
        )
    else:
        st.write("Изменений связей не обнаружено.")

    # --- Интерпретация ---
    st.markdown("## Интерпретация")
    summary_text = build_human_summary(node_diff, edge_diff, source_graph, target_graph)
    st.info(summary_text)

    # --- Загрузка отчёта ---
    st.markdown("## Экспорт")
    report_text = result.get("report", "")
    if report_text:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "Скачать полный отчёт (.txt)",
            data=report_text,
            file_name=f"report_{timestamp}.txt",
            mime="text/plain",
        )
