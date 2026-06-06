from textgraph.nlp import NLPProcessor
from textgraph.graph_builder import DependencyGraphBuilder

s = "Компания запустила новый продукт."
proc = NLPProcessor()
doc = proc.parse_text(s, lang='ru')
G = DependencyGraphBuilder.build_from_doc(doc)

print('Nodes:')
for n, d in G.nodes(data=True):
    print(n, d.get('text'), 'idx=', d.get('idx'), 'is_root=', d.get('is_root'))

print('\nEdges (head -> dependent, dep):')
for u, v, data in G.edges(data=True):
    print(f"{G.nodes[u].get('text')} ({u}) -> {G.nodes[v].get('text')} ({v}) , dep={data.get('dep')}")
