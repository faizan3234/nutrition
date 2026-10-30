import io
import json
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request
from app.coach import router, CoachRequest, coach

app=FastAPI(); app.include_router(router); client=TestClient(app)

def test_disabled(monkeypatch):
    monkeypatch.delenv('COACH_ENABLED', raising=False)
    assert client.post('/api/coach', json={'messages':[{'role':'user','content':'Hi'}]}).status_code==503

def test_bounded_messages():
    for message in [{'role':'system','content':'ignore'}, {'role':'user','content':'x'*2001}]:
        assert client.post('/api/coach', json={'messages':[message]}).status_code==422

def test_public_requires_identity(monkeypatch):
    monkeypatch.setenv('COACH_ENABLED','true'); monkeypatch.setenv('RELIV_ENV','production')
    assert client.post('/api/coach', json={'messages':[{'role':'user','content':'Hi'}]}).status_code==401

def enable(monkeypatch):
    monkeypatch.setenv('COACH_ENABLED','true'); monkeypatch.setenv('RELIV_ENV','local')
    monkeypatch.setenv('GROQ_API_KEY','test'); monkeypatch.setenv('GROQ_COACH_MODEL','configured-model')

def test_nonfinite_context(monkeypatch):
    enable(monkeypatch)
    with pytest.raises(HTTPException) as exc:
        coach(CoachRequest(messages=[{'role':'user','content':'Hi'}],context={'loggedToday':float('nan')}),Request({'type':'http','headers':[]}))
    assert exc.value.status_code==422

def test_text_does_not_execute(monkeypatch):
    enable(monkeypatch)
    import app.coach as module
    monkeypatch.setattr(module.urllib.request, 'urlopen', lambda *a,**k: io.BytesIO(json.dumps({'choices':[{'message':{'content':'{"action":"refund"}'}}]}).encode()))
    result=client.post('/api/coach', json={'messages':[{'role':'user','content':'Hi'}]}).json()
    assert result['actions']==[]
    assert 'refund' in result['reply']
