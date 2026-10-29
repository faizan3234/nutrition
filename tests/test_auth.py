import base64,hashlib,hmac,json,time
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)

def token(secret,sub,alg='HS256',exp=3600):
    def enc(x):return base64.urlsafe_b64encode(json.dumps(x,separators=(',',':')).encode()).decode().rstrip('=')
    header=enc({'typ':'JWT','alg':alg})
    payload=enc({'iss':'reliv-auth','aud':'reliv-nutrition','sub':sub,'exp':time.time()+exp})
    sign=base64.urlsafe_b64encode(hmac.new(secret.encode(),(header+'.'+payload).encode(),hashlib.sha256).digest()).decode().rstrip('=')
    return '.'.join((header,payload,sign))

def test_production_fail_closed_without_secret(monkeypatch):
    monkeypatch.setenv('RELIV_ENV','production');monkeypatch.delenv('RELIV_AUTH_SECRET',raising=False)
    r=client.get('/api/day?profile=sample-test-123&date=2026-10-29')
    assert r.status_code==503

def test_production_checks_profile_and_signature(monkeypatch):
    secret='a-very-long-reliv-auth-only-secret-2026-strong'
    monkeypatch.setenv('RELIV_ENV','production');monkeypatch.setenv('RELIV_AUTH_SECRET',secret)
    path='/api/day?profile=sample-test-123&date=2026-10-29'
    assert client.get(path).status_code==401
    assert client.get(path,headers={'Authorization':'Bearer '+token(secret,'someone-else')}).status_code==401
    assert client.get(path,headers={'Authorization':'Bearer '+token(secret,'sample-test-123',exp=-5)}).status_code==401
    assert client.get(path,headers={'Authorization':'Bearer '+token(secret,'sample-test-123')}).status_code==200
    assert client.post('/api/log',json={'profile':'sample-test-123','food_id':'steamed-rice','grams':100,'meal':'Lunch'}).status_code==401

def test_local_mode_no_token(monkeypatch):
    monkeypatch.setenv('RELIV_ENV','local')
    assert client.get('/api/day?profile=sample-test-123&date=2026-10-29').status_code==200
