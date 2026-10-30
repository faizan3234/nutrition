"""Browser integration must permit the same auth/method contract as the API."""
from starlette.middleware.cors import CORSMiddleware
from starlette.applications import Starlette
from starlette.testclient import TestClient
import ast
from pathlib import Path


def test_customer_authenticated_preflight_and_untrusted_origin():
    source = ast.parse(Path('app/main.py').read_text())
    middleware = next(node for node in ast.walk(source)
                      if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                      and node.func.attr == 'add_middleware')
    options = {kw.arg: ast.literal_eval(kw.value) for kw in middleware.keywords if kw.arg != 'allow_origins'}
    app = CORSMiddleware(Starlette(), allow_origins=['https://reliv7.vercel.app'], **options)
    client = TestClient(app)
    headers = {'Origin': 'https://reliv7.vercel.app', 'Access-Control-Request-Method': 'PUT',
               'Access-Control-Request-Headers': 'authorization,content-type'}
    assert client.options('/api/me/plate', headers=headers).status_code == 200
    headers['Origin'] = 'https://untrusted.example'
    assert client.options('/api/me/plate', headers=headers).status_code == 400
