"""RRF retrieval component adapted from Aayushyaash/Rag-chatbot.

Original: backend/retrieval/hybrid_retriever.py, MIT License,
Copyright (c) 2025 Aayush Yash. See THIRD_PARTY_NOTICES.md.
This module retains the upstream rank-fusion algorithm, without its ChromaDB wrapper.
"""
from typing import Any


def reciprocal_rank_fusion(
    results_lists: list[list[dict[str, Any]]], k: int = 60
) -> list[dict[str, Any]]:
    """Fuse independent ranked document lists using reciprocal rank fusion."""
    scores: dict[str, float] = {}
    docs: dict[str, dict[str, Any]] = {}
    for results in results_lists:
        for rank, doc in enumerate(results, 1):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            if doc_id not in docs:
                docs[doc_id] = doc
    ordered = sorted(scores, key=lambda doc_id: scores[doc_id], reverse=True)
    return [{**docs[doc_id], "rrf_score": scores[doc_id]} for doc_id in ordered]
