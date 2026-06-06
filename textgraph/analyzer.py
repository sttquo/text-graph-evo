from __future__ import annotations

from .nlp import NLPProcessor
from .graph_builder import DependencyGraphBuilder
from .aligner import TokenAligner
from .graph_diff import GraphDiff
from .report import ChangeReport


class TextGraphAnalyzer:
    def __init__(self) -> None:
        self.processor = NLPProcessor()

    def analyze(self, source_text: str, target_text: str, lang: str | None = None) -> dict:
        source_doc = self.processor.parse_text(source_text, lang=lang)
        target_doc = self.processor.parse_text(target_text, lang=lang)

        source_tokens = self.processor.extract_tokens(source_doc)
        target_tokens = self.processor.extract_tokens(target_doc)

        alignment = TokenAligner.align_by_features(source_tokens, target_tokens)
        source_graph = DependencyGraphBuilder.build_from_doc(source_doc)
        target_graph = DependencyGraphBuilder.build_from_doc(target_doc)

        node_diff = GraphDiff.diff_nodes(source_graph, target_graph, alignment)
        edge_diff = GraphDiff.diff_edges(source_graph, target_graph, alignment)
        report = ChangeReport.summarize(node_diff, edge_diff)

        return {
            "source_text": source_text,
            "target_text": target_text,
            "language": lang or self.processor.detect_language(source_text),
            "source_tokens": source_tokens,
            "target_tokens": target_tokens,
            "alignment": alignment,
            "source_graph": source_graph,
            "target_graph": target_graph,
            "node_diff": node_diff,
            "edge_diff": edge_diff,
            "report": report,
        }
