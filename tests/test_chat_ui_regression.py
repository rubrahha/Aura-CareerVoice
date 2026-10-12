"""Simple-UI readiness checks that run without a real browser or AI API key."""
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.counselor import demo_response, demo_stream
from app.rag import retrieve
from app.schemas import Profile, Turn

ROOT = Path(__file__).resolve().parents[1]


def test_frontend_provides_minimal_chat_controls():
    html = (ROOT/'app/static/index.html').read_text()
    assert 'chatMessages' in html and 'messageInput' in html
    assert 'micButton' in html and 'soundButton' in html
    assert 'stopButton' in html and 'newChatButton' in html
    assert 'modeChip' in html and 'emptyState' in html
    assert 'insights-panel' not in html and 'hero-decoration' not in html


def test_browser_safe_markdown_and_stream_parser_present():
    js = (ROOT/'app/static/app.js').read_text()
    assert 'renderMarkdown' in js and 'inlineFormat' in js
    assert '.textContent' in js
    assert 'consumeSSE' in js and 'ReadableStream' not in js  # Fetch stream consumed using getReader
    assert 'aborter.abort()' in js
    assert 'sessionStorage' in js
    assert 'innerHTML' not in js


def test_demo_roadmap_is_specific_and_scannable():
    docs, _ = retrieve('How do I become an AI engineer? Give me a beginner roadmap.',[],Profile())
    text = demo_response('How do I become an AI engineer? Give me a beginner roadmap.',[],Profile(),docs)
    assert 'AI / Machine Learning Engineer' in text
    assert '**Core skills:**' in text
    assert '1. **Step 1:**' in text
    assert 'end-to-end prediction API' in text


def test_no_coding_request_favors_non_coding_roles():
    docs, _ = retrieve("I completed BCA and don't enjoy heavy coding. Which careers should I explore?",[],Profile())
    assert docs[0]['title']=='Product Manager'
    assert any(d['title']=='UX / UI Designer' for d in docs[:3])
    text=demo_response("I completed BCA and don't enjoy heavy coding. Which careers should I explore?",[],Profile(education='BCA'),docs)
    assert '**Product Manager:**' in text and '**UX / UI Designer:**' in text


def test_chunked_demo_stream_reconstructs_answer_without_loss():
    async def collect():
        chunks=[]
        async for ch in demo_stream('one two three four five six seven eight'):
            chunks.append(ch)
        return chunks
    chunks = asyncio.run(collect())
    assert len(chunks)>=2
    assert ''.join(chunks) == 'one two three four five six seven eight'


def test_server_reports_demo_status_and_valid_source_metadata(monkeypatch):
    monkeypatch.setenv('AI_MODE','demo')
    with TestClient(app) as client:
        result=client.post('/api/chat',json={'message':'I want a product management career.'}).json()
        assert result['mode']=='demo'
        assert len(result['sources']) == 4
        assert all('title' in s and 'cluster' in s for s in result['sources'])
        assert client.get('/static/app.js').status_code==200
        assert client.get('/static/styles.css').status_code==200
