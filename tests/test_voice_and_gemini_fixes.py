from infinity_os.router2 import Router2


def test_gemini_models_prefix_is_removed():
    r=Router2()
    p={"name":"meme","provider_kind":"gemini","api_key":"AQ."+"x"*30,"simple_setup":True,"models":["models/gemini-2.5-flash"],"model":"models/gemini-2.5-flash"}
    r.autofill_provider(p)
    r.ensure_provider_ready(p,discover=False)
    assert p["model"]=="gemini-2.5-flash"
    assert p["models"]==["gemini-2.5-flash"]
    assert p["base_url"].rstrip("/")=="https://generativelanguage.googleapis.com/v1beta/openai"


def test_gemini_key_detects_with_nickname():
    r=Router2()
    assert r.detect_provider("nn","AQ."+"a"*30)=="gemini"

def test_gemini_chat_payload_uses_openai_endpoint_and_clean_model(monkeypatch):
    import json
    import infinity_os.router2 as router_mod
    seen={}
    class Resp:
        def __enter__(self): return self
        def __exit__(self,*a): return False
        def read(self): return b'{"choices":[{"message":{"content":"ok"}}],"usage":{}}'
    def fake_urlopen(req, timeout=0):
        seen['url']=req.full_url
        seen['body']=json.loads(req.data.decode())
        seen['auth']=req.headers.get('Authorization')
        return Resp()
    monkeypatch.setattr(router_mod.urllib.request,'urlopen',fake_urlopen)
    r=Router2()
    p={"name":"meme","provider_kind":"gemini","api_key":"AQ."+"x"*30,"simple_setup":True,"models":["models/gemini-2.5-flash"],"model":"models/gemini-2.5-flash"}
    r.autofill_provider(p)
    text,_=r._openai_request(p,[{"role":"user","content":"hi"}],p['model'],5)
    assert text=='ok'
    assert seen['url']=='https://generativelanguage.googleapis.com/v1beta/openai/chat/completions'
    assert seen['body']['model']=='gemini-2.5-flash'
    assert seen['auth'].startswith('Bearer AQ.')
