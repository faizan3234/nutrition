"""Optional HS256 bridge for identity supplied by Reliv's trusted auth service.

Not a full user registration/login system. Production requests with per-user
nutrition data are rejected unless an authenticated profile-scoped token matches.
"""
from __future__ import annotations
import os,base64,json,hmac,hashlib,time
from fastapi import HTTPException


def _decode(s:str)->bytes:
    return base64.urlsafe_b64decode(s+'='*((-len(s))%4))

def authorized_profile(headers,profile:str):
    if os.getenv('RELIV_ENV','local').casefold()!='production':return
    secret=os.getenv('RELIV_AUTH_SECRET','')
    if len(secret)<32:
        raise HTTPException(503,'Production authentication is not configured; access disabled')
    raw=headers.get('Authorization','')
    if not raw.startswith('Bearer '):raise HTTPException(401,'Bearer token required')
    token=raw[7:]
    try:
        header,payload,signature=token.split('.')
        h=json.loads(_decode(header)); p=json.loads(_decode(payload))
        if h.get('alg')!='HS256' or h.get('typ')!='JWT':raise ValueError('Unsupported token')
        digest=hmac.new(secret.encode(),(header+'.'+payload).encode(),hashlib.sha256).digest()
        if not hmac.compare_digest(digest,_decode(signature)):raise ValueError('Invalid signature')
        if p.get('iss')!='reliv-auth' or p.get('aud')!='reliv-nutrition':raise ValueError('Incorrect issuer/audience')
        if not isinstance(p.get('exp'),(int,float)) or not time.time()<p['exp']<=time.time()+86400:
            raise ValueError('Expired/long-lived token')
        if p.get('sub')!=profile:raise ValueError('Profile mismatch')
    except (ValueError,UnicodeError,KeyError,TypeError,OverflowError,json.JSONDecodeError) as e:
        raise HTTPException(401,'Invalid or unauthorized token') from e
