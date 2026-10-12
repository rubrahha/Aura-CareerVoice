"""Meaningful integration tests for upstream voice-agent conversation memory."""
from fastapi.testclient import TestClient
from app.integrations.conversation import ConversationManager
from app.counselor import build_prompt
from app.rag import get_index
from app.schemas import Turn, Profile
from app.main import app


def test_upstream_rolling_memory_keeps_system_and_recent_turns():
    manager = ConversationManager(max_turns=2, system_prompt='Career counselor', instruction_prompt='Keep context')
    for idx in range(4):
        manager.add_user_message(f'question {idx}')
        manager.add_assistant_message(f'answer {idx}')
    messages = manager.get_messages()
    assert messages[0]['role'] == 'system'
    assert 'Career counselor' in messages[0]['content']
    assert len(messages) == 5
    assert messages[-1]['content'] == 'answer 3'
    assert 'question 0' not in str(messages)


def test_followup_prompt_contains_prior_personal_context():
    history = [Turn(role='user',content='I study BCA and love data analytics'),
               Turn(role='assistant',content='Data Analyst is a good path to explore.')]
    prompt = build_prompt('What skills should I learn?', history, Profile(education='BCA'),
                          get_index().search('Data Analyst'))
    assert 'I study BCA and love data analytics' in prompt
    assert 'Data Analyst is a good path' in prompt
    assert 'BCA' in prompt
    assert 'RETRIEVED CAREER REFERENCE NOTES' in prompt


def test_streaming_real_ai_path_with_mocked_provider(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY','dummy-test-key')
    monkeypatch.setenv('AI_MODE','auto')
    import app.main as api
    captured=[]
    async def provider(prompt):
        captured.append(prompt)
        yield 'A career in data '
        yield 'analytics might suit you.'
    monkeypatch.setattr(api, 'gemini_stream', provider)
    with TestClient(app) as client:
        response = client.post('/api/chat/stream', json={
            'message': 'What should I learn for data analytics?',
            'history':[{'role':'user','content':'I am studying BCA'},
                       {'role':'assistant','content':'You could explore a data analyst role.'}],
            'profile':{'education':'BCA','interests':'data'}})
        assert response.status_code == 200
        assert 'event: done' in response.text
        assert '"mode": "gemini"' in response.text
        assert '"first_token_ms"' in response.text
        assert 'analytics might suit you' in response.text
        assert 'BCA' in captured[0]
        assert 'RETRIEVED CAREER REFERENCE NOTES' in captured[0]
        metrics = client.get('/api/latency/summary').json()['metrics']
        assert metrics['first_token_ms']['count'] >= 1


def test_upstream_mit_notices_and_code_included():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    notices=(root/'THIRD_PARTY_NOTICES.md').read_text()
    source=(root/'app/integrations/conversation.py').read_text()
    assert 'lythe labs' in notices
    assert 'lythelab/voice-agent-starter-kit' in source
    assert 'def add_user_message' in source
