from __future__ import annotations

import networkx as nx
from spacy.tokens import Doc


class DependencyGraphBuilder:
    @staticmethod
    def build_from_doc(doc: Doc) -> nx.DiGraph:
        graph = nx.DiGraph()

        for token in doc:
            graph.add_node(
                token.i,
                idx=token.i,
                text=token.text,
                lemma=token.lemma_,
                pos=token.pos_,
                morph=token.morph.to_dict(),
                dep=token.dep_,
                head=token.head.i,
                is_root=token.dep_ == "ROOT",
            )

        for token in doc:
            if token.dep_ != "ROOT":
                # Edge direction: head -> dependent (head token points to its dependent)
                # store dependency label both as 'dep' and 'label' for convenient visualization
                graph.add_edge(token.head.i, token.i, dep=token.dep_, label=token.dep_)

        return graph
