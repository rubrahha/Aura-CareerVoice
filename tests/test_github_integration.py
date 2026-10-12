"""Regression and integration tests for open-source component adaptations."""
import os
from fastapi.testclient import TestClient
from app.main import app
from app.rag import get_index
from app.bm25 import BM25Index
from app.integrations.rrf import reciprocal_rank_fusion
from app.integrations.telemetry import LatencyStore


def test_rrf_merges_ranked_retrievers_and_deduplicates():
    first = [{"id":"python"}, {"id":"design"}]
    second = [{"id":"design"}, {"id":"data"}]
    fused = reciprocal_rank_fusion([first, second])
    assert [r["id"] for r in fused] == ["design", "python", "data"]
    assert fused[0]["rrf_score"] > fused[1]["rrf_score"]


def test_bm25_indexes_and_ranks_relevant_documents():
    index = BM25Index(["machine learning neural network machine learning", "landscape photography and artwork"])
    values = index.score("neural network")
    assert values[0] > values[1]
    assert values[1] == 0


def test_hybrid_rag_and_explainability(monkeypatch):
    results = get_index().search("machine learning python models")
    assert results and len(results) == 4
    assert any("AI" in r["title"] or "Machine Learning" in r["title"] for r in results)
    assert get_index().bm25.n == len(get_index().careers)
    with TestClient(app) as client:
        health = client.get("/api/health").json()
        assert health["retrieval"] == "TF-IDF + BM25 + RRF (MIT-adapted)"


def test_telemetry_store_is_bounded_and_reports_percentiles():
    store = LatencyStore(max_samples=3)
    for value in (10,20,30,40):
        store.add("rag_retrieval_ms", value)
    sample = store.summary()["rag_retrieval_ms"]
    assert sample["count"] == 3
    assert sample["min_ms"] == 20
    assert sample["max_ms"] == 40
    assert sample["p95_ms"] == 40


def test_aggregated_metrics_endpoint(monkeypatch):
    monkeypatch.setenv("AI_MODE", "demo")
    with TestClient(app) as client:
        resp = client.post("/api/chat", json={"message": "What skills for product management?"})
        assert resp.status_code == 200
        metrics = client.get("/api/latency/summary")
        assert metrics.status_code == 200
        data = metrics.json()
        assert data["metrics"]["rag_retrieval_ms"]["count"] >= 1
        assert data["metrics"]["total_response_ms"]["count"] >= 1


def test_out_of_scope_query_does_not_crash(monkeypatch):
    monkeypatch.setenv("AI_MODE", "demo")
    with TestClient(app) as client:
        resp = client.post("/api/chat",json={"message":"zzzzxxxyyyqqq"})
        assert resp.status_code == 200
        assert "couldn't find" in resp.json()["answer"]
        assert resp.json()["sources"] == []


def test_gemini_failure_falls_back_in_both_api_modes(monkeypatch):
    monkeypatch.setenv("AI_MODE", "auto")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-demo-key")
    async def failed_stream(_prompt):
        raise RuntimeError("AI free-tier quota reached. Showing knowledge-base demo reply.")
        yield ""  # make this an async generator for mocking
    import app.main as main
    monkeypatch.setattr(main, "gemini_stream", failed_stream)
    with TestClient(app) as client:
        data = client.post("/api/chat", json={"message":"How can I become a nurse?"}).json()
        assert data["mode"] == "fallback"
        assert "nurse" in data["answer"].lower()
        response = client.post("/api/chat/stream", json={"message":"How can I become a nurse?"})
        assert response.status_code == 200
        assert '"mode": "fallback"' in response.text
        assert "event: done" in response.text
