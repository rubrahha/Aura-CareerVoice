"""Small pure-Python BM25 ranker for the 40-document career knowledge base.

The hybrid BM25 + vector/lexical RRF strategy follows the architecture of
Aayushyaash/Rag-chatbot (MIT license), with our own in-memory implementation
to avoid heavyweight ChromaDB/embedding-model dependencies and API costs.
"""
from collections import Counter
import math
import re

STOPWORDS = frozenset('''a an the and or but in on at to for of with by from is are was were be been being have has had do does did will would could should may might must shall can this that these those i you he she it we they what which who whom how when where why if then else so just also only very too more some any no not all each every both few many much most other such own same than as'''.split())


def tokenize(text: str) -> list[str]:
    return [term for term in re.findall(r'\b[a-z0-9]+\b', text.casefold())
            if len(term) > 2 and term not in STOPWORDS]


class BM25Index:
    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        self.freqs = [Counter(tokenize(doc)) for doc in corpus]
        self.lens = [sum(c.values()) for c in self.freqs]
        self.avgdl = (sum(self.lens) / len(corpus)) if corpus else 0.0
        self.n = len(corpus)
        self.k1 = k1
        self.b = b
        self.df = Counter(term for record in self.freqs for term in record)

    def score(self, query: str) -> list[float]:
        tokens = set(tokenize(query))
        scores: list[float] = []
        for counts, dl in zip(self.freqs, self.lens):
            score = 0.0
            for term in tokens:
                tf = counts.get(term, 0)
                if not tf:
                    continue
                df = self.df[term]
                idf = math.log(1 + ((self.n - df + 0.5) / (df + 0.5)))
                denom = tf + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1))
                score += idf * tf * (self.k1 + 1) / denom
            scores.append(score)
        return scores
