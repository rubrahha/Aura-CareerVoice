"""Zero-cost hybrid RAG retrieval over the curated 40-career knowledge base.

Combines TF-IDF vectors (lexical similarity) + BM25 (term relevance) with
reciprocal rank fusion adapted from an MIT-licensed GitHub reference repo.
This is *not* dense semantic embedding search; it is honest, CPU-friendly RAG.
"""
from functools import lru_cache
import json
from pathlib import Path
import re
import time

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .bm25 import BM25Index
from .integrations.rrf import reciprocal_rank_fusion

DATA_PATH = Path(__file__).parent / "data" / "careers.json"

# Normalize common student phrases. This also helps Hinglish questions somewhat.
ALIASES = {
    "don't like coding": "non coding design product management business",
    "dont like coding": "non coding design product management business",
    "not into coding": "non coding design product management business",
    "hate coding": "non coding design product management business",
    "no coding": "non coding design product management business",
    "without coding": "non coding design product management business",
    "ai": "artificial intelligence machine learning",
    "ml": "machine learning artificial intelligence",
    "ux": "user experience",
    "ui": "user interface",
    "cyber": "cybersecurity security",
    "designing": "design visual creativity",
    "business": "business analytics product management operations",
    "after bca": "computer applications software analytics",
    "after 12th": "higher secondary education career",
    "salary": "salary compensation earnings job market",
    "paise": "salary earnings compensation",
    "mujhe": "i am interested in",
    "nahi": "not interested",
}


def enhance_query(query: str) -> str:
    cleaned = query.casefold()
    expansions = [v for k, v in ALIASES.items() if re.search(r"(?<!\w)" + re.escape(k) + r"(?!\w)", cleaned)]
    # Negation is crucial: ordinary TF-IDF tends to interpret "I do not like coding"
    # as if the student *likes* coding, especially after English stopword removal.
    no_heavy_coding = bool(re.search(
        r"(?:not|don't|dont|avoid|hate|without|no).{0,55}(?:coding|programming|code)", cleaned
    ))
    if no_heavy_coding:
        expansions.append("product manager user research product roadmap business analyst UX UI design non coding coordination customer needs")
    if "building products" in cleaned or "building a product" in cleaned:
        expansions.append("product management product strategy user needs product development")
    return f"{query} {' '.join(expansions)}"


class CareerIndex:
    def __init__(self, path: Path = DATA_PATH):
        self.careers = json.loads(path.read_text(encoding="utf-8"))
        self.records = [self._as_document(entry) for entry in self.careers]
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode",
            stop_words="english", max_features=16000,
        )
        self.vectors = self.vectorizer.fit_transform(self.records)
        self.bm25 = BM25Index(self.records)

    @staticmethod
    def _as_document(item: dict) -> str:
        return " ".join(str(item.get(k, "")) if not isinstance(item.get(k), list)
                        else " ".join(item[k])
                        for k in ("title", "cluster", "summary", "skills", "education", "roadmap",
                                  "growth", "fit", "keywords", "cautions"))

    def search(self, query: str, k: int = 4) -> list[dict]:
        """Retrieve career notes with two real indexes and RRF consensus ranking."""
        if k <= 0:
            return []
        query = enhance_query(query[:2200])
        qvector = self.vectorizer.transform([query])
        similarities = cosine_similarity(qvector, self.vectors)[0]
        keyword_scores = self.bm25.score(query)
        pool = min(len(self.careers), max(k * 3, 12))
        tfidf_ids = sorted(range(len(similarities)), key=lambda i: float(similarities[i]), reverse=True)
        bm25_ids = sorted(range(len(keyword_scores)), key=lambda i: keyword_scores[i], reverse=True)
        # Do not include unrelated careers with zero similarity; a question can be
        # out of scope and we should not imply strong supporting references.
        tfidf = [{"id": self.careers[i]["id"]} for i in tfidf_ids[:pool] if similarities[i] > 0]
        keyword = [{"id": self.careers[i]["id"]} for i in bm25_ids[:pool] if keyword_scores[i] > 0]
        if not tfidf and not keyword:
            return []
        fused = reciprocal_rank_fusion([tfidf, keyword])
        ids = {entry["id"]: i for i, entry in enumerate(self.careers)}
        # Sources show TF-IDF similarity (0..1). Ranking instead uses RRF.
        return [{**self.careers[ids[hit["id"]]],
                 "score": round(float(similarities[ids[hit["id"]]]), 3)}
                for hit in fused[:k]]


@lru_cache(maxsize=1)
def get_index() -> CareerIndex:
    return CareerIndex()


def retrieve(message: str, history: list, profile: object) -> tuple[list[dict], float]:
    started = time.perf_counter()
    # Last student turn informs follow-up resolution; current turn remains primary.
    previous_user = next((x.content for x in reversed(history) if x.role == "user"), "")
    context = f"{message} {message} {previous_user[:280]} {profile.education} {profile.interests} {profile.goals}"
    results = get_index().search(context)
    return results, round((time.perf_counter() - started) * 1000, 2)


def public_sources(docs: list[dict]) -> list[dict]:
    return [{"id": d["id"], "title": d["title"], "cluster": d["cluster"], "score": d["score"]}
            for d in docs]


def grounding_context(docs: list[dict]) -> str:
    parts = []
    for d in docs:
        parts.append(
            f"[SOURCE:{d['id']}] {d['title']} — {d['cluster']}\n"
            f"Overview: {d['summary']}\nFit: {d['fit']}\n"
            f"Skills: {', '.join(d['skills'])}\nEducation: {d['education']}\n"
            f"Start here: {'; '.join(d['roadmap'])}\nGrowth: {d['growth']}\n"
            f"Cautions: {d['cautions']}"
        )
    return "\n\n".join(parts)
