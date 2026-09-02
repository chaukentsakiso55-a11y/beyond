from pathlib import Path
import json, time, urllib.request, urllib.error, threading, statistics, uuid, re
from urllib.parse import urlparse
from .paths import CONFIG, DATA


PROVIDER_PROFILES = {
    "openai": {
        "label": "OpenAI",
        "aliases": ("openai", "chatgpt", "gpt"),
        "key_prefixes": ("sk-proj-", "sk-"),
        "base_url": "https://api.openai.com/v1",
        "type": "openai-compatible",
        "model_hints": ("gpt-5.6", "gpt-5", "gpt-4.1", "gpt-4o"),
        "default_model": "gpt-5.6-luna",
    },
    "openrouter": {
        "label": "OpenRouter",
        "aliases": ("openrouter", "open router"),
        "key_prefixes": ("sk-or-",),
        "base_url": "https://openrouter.ai/api/v1",
        "type": "openai-compatible",
        "model_hints": ("openai/", "anthropic/", "google/", "deepseek/"),
    },
    "gemini": {
        "label": "Google Gemini",
        "aliases": ("gemini", "google ai", "google gemini", "ai studio"),
        "key_prefixes": ("AIza", "AQ."),
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "type": "openai-compatible",
        "model_hints": ("gemini-",),
        "default_model": "gemini-3.7-flash",
    },
    "anthropic": {
        "label": "Anthropic Claude",
        "aliases": ("anthropic", "claude"),
        "key_prefixes": ("sk-ant-",),
        "base_url": "https://api.anthropic.com/v1",
        "type": "anthropic",
        "model_hints": ("claude-sonnet-", "claude-opus-", "claude-haiku-", "claude-"),
        "default_model": "claude-sonnet-4-6",
    },
    "groq": {
        "label": "Groq",
        "aliases": ("groq",),
        "key_prefixes": ("gsk_",),
        "base_url": "https://api.groq.com/openai/v1",
        "type": "openai-compatible",
        "model_hints": ("llama", "qwen", "openai/", "gemma"),
    },
    "mistral": {
        "label": "Mistral AI",
        "aliases": ("mistral", "codestral", "ministral"),
        "key_prefixes": (),
        "base_url": "https://api.mistral.ai/v1",
        "type": "openai-compatible",
        "model_hints": ("mistral", "ministral", "codestral"),
    },
    "xai": {
        "label": "xAI Grok",
        "aliases": ("xai", "x.ai", "grok"),
        "key_prefixes": ("xai-",),
        "base_url": "https://api.x.ai/v1",
        "type": "openai-compatible",
        "model_hints": ("grok-",),
    },
    "deepseek": {
        "label": "DeepSeek",
        "aliases": ("deepseek", "deep seek"),
        "key_prefixes": (),
        "base_url": "https://api.deepseek.com",
        "type": "openai-compatible",
        "model_hints": ("deepseek-",),
    },
    "perplexity": {
        "label": "Perplexity",
        "aliases": ("perplexity", "sonar"),
        "key_prefixes": ("pplx-",),
        "base_url": "https://api.perplexity.ai",
        "type": "openai-compatible",
        "model_hints": ("sonar",),
    },
    "together": {
        "label": "Together AI",
        "aliases": ("together", "together ai"),
        "key_prefixes": (),
        "base_url": "https://api.together.xyz/v1",
        "type": "openai-compatible",
        "model_hints": ("meta-llama/", "Qwen/", "deepseek"),
    },
    "fireworks": {
        "label": "Fireworks AI",
        "aliases": ("fireworks", "fireworks ai"),
        "key_prefixes": (),
        "base_url": "https://api.fireworks.ai/inference/v1",
        "type": "openai-compatible",
        "model_hints": ("accounts/fireworks/models/",),
    },
    "cerebras": {
        "label": "Cerebras",
        "aliases": ("cerebras",),
        "key_prefixes": (),
        "base_url": "https://api.cerebras.ai/v1",
        "type": "openai-compatible",
        "model_hints": ("llama", "qwen"),
    },
    "nvidia": {
        "label": "NVIDIA NIM",
        "aliases": ("nvidia", "nim"),
        "key_prefixes": ("nvapi-",),
        "base_url": "https://integrate.api.nvidia.com/v1",
        "type": "openai-compatible",
        "model_hints": ("meta/", "qwen/", "mistralai/", "deepseek"),
    },
    "sambanova": {
        "label": "SambaNova",
        "aliases": ("sambanova", "samba nova"),
        "key_prefixes": (),
        "base_url": "https://api.sambanova.ai/v1",
        "type": "openai-compatible",
        "model_hints": ("Meta-Llama", "Qwen", "DeepSeek"),
    },
    "huggingface": {
        "label": "Hugging Face",
        "aliases": ("huggingface", "hugging face", "hf"),
        "key_prefixes": ("hf_",),
        "base_url": "https://router.huggingface.co/v1",
        "type": "openai-compatible",
        "model_hints": ("meta-llama/", "Qwen/", "mistralai/", "deepseek"),
    },
    "moonshot": {
        "label": "Moonshot / Kimi",
        "aliases": ("moonshot", "kimi"),
        "key_prefixes": (),
        "base_url": "https://api.moonshot.ai/v1",
        "type": "openai-compatible",
        "model_hints": ("kimi-", "moonshot-"),
    },
}


class Router2:
    def __init__(self,bus=None,notifications=None):
        self.path=CONFIG/"providers.json";self.example=CONFIG/"providers.example.json";self.bus=bus;self.notifications=notifications;self._lock=threading.RLock()
        self.stats_path=DATA/"provider_stats.json";self.stats={};self._health_stop=threading.Event();self._health_thread=None;self.reload();self._load_stats()

    def reload(self):
        src=self.path if self.path.exists() else self.example
        try:self.config=json.loads(src.read_text(encoding="utf-8"))
        except Exception:self.config={"routing":{},"providers":[]}
        self.config.setdefault("routing",{});self.config.setdefault("providers",[])
        for p in self.config["providers"]:
            p.setdefault("id",str(uuid.uuid4()));p.setdefault("enabled",True);p.setdefault("priority",50);p.setdefault("models",[]);p.setdefault("type","openai-compatible")

    def save(self):self.path.write_text(json.dumps(self.config,indent=2),encoding="utf-8")
    def providers(self,enabled_only=False):return [p for p in self.config["providers"] if p.get("enabled",True) or not enabled_only]
    def provider(self,name):return next((p for p in self.providers() if p.get("name")==name or p.get("id")==name),None)

    @staticmethod
    def normalize_api_key(api_key):
        """Clean common copy/paste wrappers without changing the credential itself."""
        key=(api_key or "").strip()
        # Users often copy GEMINI_API_KEY="...", Authorization: Bearer ..., or quoted values.
        for prefix in ("GEMINI_API_KEY=", "GOOGLE_API_KEY=", "OPENAI_API_KEY=", "ANTHROPIC_API_KEY=", "API_KEY="):
            if key.upper().startswith(prefix):
                key=key[len(prefix):].strip()
                break
        if key.lower().startswith("bearer "):
            key=key[7:].strip()
        if len(key)>=2 and key[0]==key[-1] and key[0] in ("'", '"'):
            key=key[1:-1].strip()
        return key

    def detect_provider(self,display_name="",api_key="",provider_hint=""):
        """Identify a known provider from an explicit hint, friendly name, or local key signature."""
        hint=(provider_hint or "").strip().lower()
        if hint in PROVIDER_PROFILES:return hint
        name=(display_name or "").strip().lower()
        key=self.normalize_api_key(api_key)
        # A provider-like display name is only a hint; users may otherwise use any nickname they want.
        for provider_id,profile in PROVIDER_PROFILES.items():
            if any(alias and alias in name for alias in profile.get("aliases",())):
                return provider_id
        # Check specific/long prefixes before broad ones.
        prefix_rows=[]
        for provider_id,profile in PROVIDER_PROFILES.items():
            for prefix in profile.get("key_prefixes",()):prefix_rows.append((len(prefix),prefix,provider_id))
        for _,prefix,provider_id in sorted(prefix_rows,reverse=True):
            if key.startswith(prefix):return provider_id
        # Google AI Studio keys are Google API keys and conventionally use the AIza... form.
        # Keep this local-only: Infinity never sends an unknown credential to random providers to guess its source.
        if re.fullmatch(r"AIza[0-9A-Za-z_-]{20,}",key) or re.fullmatch(r"AQ\.[0-9A-Za-z._-]{20,}",key):return "gemini"
        return ""

    def provider_profile(self,provider_or_name,api_key=""):
        if isinstance(provider_or_name,dict):
            provider_id=provider_or_name.get("provider_kind") or self.detect_provider(provider_or_name.get("name",""),provider_or_name.get("api_key",""),provider_or_name.get("provider_hint",""))
        else:provider_id=self.detect_provider(provider_or_name,api_key)
        profile=PROVIDER_PROFILES.get(provider_id)
        return (provider_id,profile.copy()) if profile else ("",None)

    def autofill_provider(self,provider):
        """Fill endpoint/protocol for a known cloud provider while preserving manual advanced settings."""
        if not isinstance(provider,dict):return provider
        provider_id,profile=self.provider_profile(provider)
        if not profile:return provider
        provider["provider_kind"]=provider_id
        provider["api_key"]=self.normalize_api_key(provider.get("api_key",""))
        provider.setdefault("type",profile["type"])
        if not provider.get("base_url"):provider["base_url"]=profile["base_url"]
        if provider.get("simple_setup",False):
            provider["type"]=profile["type"]
            provider["base_url"]=profile["base_url"]
        return provider

    @staticmethod
    def _valid_http_url(url):
        try:
            parsed=urlparse((url or "").strip())
            return parsed.scheme in ("http","https") and bool(parsed.netloc)
        except Exception:return False

    def validate_provider(self,provider,require_model=False):
        self.autofill_provider(provider)
        base=(provider.get("base_url") or "").strip()
        if not base:return False,"Infinity could not identify the API provider. Use a recognizable provider name, or open Advanced settings and enter the API base URL."
        if base.lower().startswith(("curl ","curl\t")) or not self._valid_http_url(base):
            return False,"Invalid API base URL. Enter only an http:// or https:// address — not a full cURL command."
        if provider.get("simple_setup") and not provider.get("api_key"):
            return False,"Enter the API key for this provider."
        if require_model and not (provider.get("model") or provider.get("models")):
            return False,"No chat model is configured or discoverable for this provider."
        return True,"Ready"

    def _headers_for(self,provider,json_body=False):
        headers={"Accept":"application/json"}
        if json_body:headers["Content-Type"]="application/json"
        key=provider.get("api_key","")
        if provider.get("type")=="anthropic":
            if key:headers["x-api-key"]=key
            headers["anthropic-version"]="2023-06-01"
        elif key:headers["Authorization"]="Bearer "+key
        return headers

    def normalize_model_id(self, provider, model):
        """Normalize provider-specific model IDs into the form expected by chat endpoints."""
        mid=(model or "").strip()
        provider_id,_=self.provider_profile(provider)
        # Gemini's native models API may surface names as models/gemini-..., while
        # the OpenAI-compatible chat endpoint expects gemini-... without models/.
        if provider_id=="gemini" and mid.startswith("models/"):
            mid=mid.split("/",1)[1]
        return mid

    def discover_models(self,provider,timeout=12):
        """Return chat-capable-looking model IDs exposed by the provider's model-list endpoint."""
        self.autofill_provider(provider)
        ok,msg=self.validate_provider(provider)
        if not ok:raise ValueError(msg)
        base=provider.get("base_url","").rstrip("/")
        req=urllib.request.Request(base+"/models",headers=self._headers_for(provider),method="GET")
        with urllib.request.urlopen(req,timeout=timeout) as r:data=json.loads(r.read().decode("utf-8"))
        rows=data.get("data",data.get("models",[])) if isinstance(data,dict) else []
        ids=[]
        for item in rows:
            if isinstance(item,str):mid=item
            elif isinstance(item,dict):mid=item.get("id") or item.get("name") or item.get("model")
            else:mid=""
            mid=self.normalize_model_id(provider,mid)
            if mid and mid not in ids:ids.append(mid)
        return self._filter_chat_models(ids,provider)

    def _filter_chat_models(self,models,provider):
        if not models:return []
        bad=("embedding","whisper","tts","speech","moderation","image","dall-e","realtime","audio","transcrib","rerank")
        chat=[m for m in models if not any(x in m.lower() for x in bad)] or list(models)
        _,profile=self.provider_profile(provider)
        hints=profile.get("model_hints",()) if profile else ()
        if hints:
            preferred=[m for m in chat if any(h.lower() in m.lower() for h in hints)]
            if preferred:chat=preferred+[m for m in chat if m not in preferred]
        return chat[:120]

    def ensure_provider_ready(self,provider,discover=True):
        self.autofill_provider(provider)
        ok,msg=self.validate_provider(provider)
        if not ok:raise ValueError(msg)
        models=[self.normalize_model_id(provider,x) for x in (provider.get("models") or []) if x]
        models=[x for x in models if x]
        if provider.get("model"):
            provider["model"]=self.normalize_model_id(provider,provider.get("model"))
        if not models and provider.get("model"):models=[provider["model"]]
        if not models and discover:
            try:
                models=self.discover_models(provider)
            except urllib.error.HTTPError as exc:
                provider["last_discovery_error"]=str(exc)[:500]
                _,profile=self.provider_profile(provider)
                fallback=(profile or {}).get("default_model","")
                if exc.code==404 and fallback:models=[fallback]
                else:raise
            except Exception as exc:
                provider["last_discovery_error"]=str(exc)[:500]
                raise
        if not models:
            _,profile=self.provider_profile(provider);fallback=(profile or {}).get("default_model","")
            if fallback:models=[fallback]
        if models:
            provider["models"]=models
            if not provider.get("model") or provider.get("model") not in models:provider["model"]=models[0]
            # Persist auto-discovery if this is one of our configured provider objects.
            if any(p is provider or p.get("id")==provider.get("id") for p in self.config.get("providers",[])):
                try:self.save()
                except Exception:pass
        return provider

    def _load_stats(self):
        try:self.stats=json.loads(self.stats_path.read_text(encoding="utf-8"))
        except Exception:self.stats={}
    def _save_stats(self):
        with self._lock:self.stats_path.write_text(json.dumps(self.stats,indent=2),encoding="utf-8")
    def _stat(self,name):return self.stats.setdefault(name,{"calls":0,"success":0,"fail":0,"latencies":[],"tokens_in":0,"tokens_out":0,"last_error":"","last_ok":0,"arena_rating":0.0,"arena_votes":0})

    def record(self,name,ok,latency,error="",tokens_in=0,tokens_out=0):
        s=self._stat(name);s["calls"]+=1;s["success" if ok else "fail"]+=1;s["latencies"]=(s["latencies"]+[round(latency,3)])[-80:];s["tokens_in"]+=tokens_in;s["tokens_out"]+=tokens_out
        if ok:s["last_ok"]=time.time();s["last_error"]=""
        else:s["last_error"]=error[:500]
        self._save_stats()

    def health(self,name):
        s=self._stat(name);calls=max(1,s["calls"]);success=s["success"]/calls;lat=statistics.mean(s["latencies"]) if s["latencies"] else 2.0
        return {"success_rate":success,"avg_latency":lat,"calls":s["calls"],"last_error":s["last_error"],"last_ok":s["last_ok"]}

    def rank(self,task="default",private=False):
        routing=self.config.get("routing",{});preferred=routing.get("privacy_provider" if private else ("coding_provider" if task=="coding" else "default_provider"),"")
        rows=[]
        for p in self.providers(True):
            h=self.health(p.get("name",""));priority=float(p.get("priority",50));success=h["success_rate"] if h["calls"] else .4;latency=h["avg_latency"]
            native=getattr(self,"native",None);score=native.route_score(priority,success,latency,p.get("name")==preferred) if native else priority+success*25-min(latency,20)*1.5+(40 if p.get("name")==preferred else 0)
            if private and (p.get("local") or p.get("base_url","").startswith(("http://127.0.0.1","http://localhost"))):score+=30
            tags=[x.lower() for x in p.get("tags",[])]
            if task=="coding" and "coding" in tags:score+=15
            st=self._stat(p.get("name",""));score+=float(st.get("arena_rating",0))*3
            rows.append((score,p))
        return [p for _,p in sorted(rows,key=lambda x:x[0],reverse=True)]

    def _openai_request(self,provider,messages,chosen,timeout):
        base=provider.get("base_url","").rstrip("/")
        chosen=self.normalize_model_id(provider,chosen)
        payload={"model":chosen,"messages":messages,"temperature":0.45,"stream":False}
        req=urllib.request.Request(base+"/chat/completions",data=json.dumps(payload).encode(),headers=self._headers_for(provider,True),method="POST")
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r:data=json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # Preserve the provider's error body when available; it is much more useful
            # than a bare "HTTP Error 404" in Model Arena.
            try:
                body=exc.read().decode("utf-8","replace")[:1800]
            except Exception:
                body=""
            if body:
                raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
            raise
        text=data["choices"][0]["message"].get("content","");usage=data.get("usage",{})
        return text,usage

    def _anthropic_request(self,provider,messages,chosen,timeout):
        base=provider.get("base_url","").rstrip("/")
        systems=[];chat=[]
        for message in messages:
            role=message.get("role","user");content=message.get("content","")
            if role=="system":systems.append(str(content))
            elif role in ("user","assistant"):chat.append({"role":role,"content":content})
        payload={"model":chosen,"max_tokens":4096,"messages":chat or [{"role":"user","content":"Hello"}]}
        if systems:payload["system"]="\n\n".join(systems)
        req=urllib.request.Request(base+"/messages",data=json.dumps(payload).encode(),headers=self._headers_for(provider,True),method="POST")
        with urllib.request.urlopen(req,timeout=timeout) as r:data=json.loads(r.read().decode("utf-8"))
        parts=data.get("content",[]);text="".join(x.get("text","") for x in parts if isinstance(x,dict) and x.get("type")=="text")
        raw=data.get("usage",{});usage={"prompt_tokens":raw.get("input_tokens",0),"completion_tokens":raw.get("output_tokens",0)}
        return text,usage

    def _request(self,provider,messages,model=None,stream=False,timeout=90):
        self.ensure_provider_ready(provider,discover=not bool(model))
        chosen=self.normalize_model_id(provider,model or provider.get("model") or ((provider.get("models") or [""])[0]))
        if chosen:
            provider["model"]=chosen
            provider["models"]=[self.normalize_model_id(provider,x) for x in (provider.get("models") or [chosen]) if x]
        ok,msg=self.validate_provider(provider,require_model=True)
        if not ok:raise ValueError(msg)
        started=time.perf_counter()
        try:
            if provider.get("type")=="anthropic":text,usage=self._anthropic_request(provider,messages,chosen,timeout)
            else:text,usage=self._openai_request(provider,messages,chosen,timeout)
            latency=time.perf_counter()-started
            self.record(provider.get("name","Provider"),True,latency,tokens_in=int(usage.get("prompt_tokens",0) or 0),tokens_out=int(usage.get("completion_tokens",0) or 0))
            return {"ok":True,"provider":provider.get("name"),"model":chosen,"text":text,"latency":latency,"usage":usage}
        except Exception as exc:
            latency=time.perf_counter()-started;self.record(provider.get("name","Provider"),False,latency,str(exc));raise

    def chat(self,messages,task="default",private=False,provider_name=None,model=None,failover=True):
        candidates=[self.provider(provider_name)] if provider_name else self.rank(task,private);candidates=[p for p in candidates if p]
        errors=[]
        for p in candidates[:(5 if failover else 1)]:
            try:
                result=self._request(p,messages,model if provider_name else None)
                if self.bus:self.bus.emit("router.response",result)
                return result
            except Exception as exc:errors.append(f"{p.get('name')}: {exc}")
        return {"ok":False,"provider":"AEGIS Offline","model":"","text":"No configured AI provider responded. "+" | ".join(errors[-3:]),"errors":errors}

    def ask(self,prompt,task="default",private=False,system="You are AEGIS inside Infinity OS. Be practical and preserve project architecture."):
        return self.chat([{"role":"system","content":system},{"role":"user","content":prompt}],task,private)

    def check_provider(self,provider):return self.ping_provider(provider)

    def cost_estimate(self,name):
        p=self.provider(name) or {};s=self._stat(p.get("name",name));ci=float(p.get("cost_input_per_million",0) or 0);co=float(p.get("cost_output_per_million",0) or 0)
        return s.get("tokens_in",0)/1_000_000*ci+s.get("tokens_out",0)/1_000_000*co

    def record_arena_feedback(self,provider_name,rating):
        s=self._stat(provider_name);votes=int(s.get("arena_votes",0));old=float(s.get("arena_rating",0));s["arena_rating"]=(old*votes+float(rating))/(votes+1);s["arena_votes"]=votes+1;self._save_stats()

    def ping_provider(self,provider):
        started=time.perf_counter()
        try:
            self.ensure_provider_ready(provider,discover=True)
            models=provider.get("models") or []
            model_text=f" · {len(models)} model(s) found" if models else ""
            return {"ok":True,"latency":time.perf_counter()-started,"message":"Connected"+model_text}
        except urllib.error.HTTPError as exc:
            if exc.code in (401,403):msg="Authentication failed — check the API key."
            elif exc.code==404:msg="Provider reached, but model discovery is not supported at this endpoint. Add a model in Advanced settings."
            elif exc.code==429:msg="Provider rate limit reached. Try again later."
            else:msg=f"Provider returned HTTP {exc.code}."
            return {"ok":False,"latency":time.perf_counter()-started,"message":msg}
        except Exception as exc:return {"ok":False,"latency":time.perf_counter()-started,"message":str(exc)}

    def start_health_monitor(self,interval=600):
        if self._health_thread and self._health_thread.is_alive():return
        self._health_stop.clear()
        def loop():
            while not self._health_stop.wait(interval):
                for p in self.providers(True):
                    result=self.ping_provider(p);s=self._stat(p.get("name",""));s["last_probe_ok"]=result["ok"];s["last_probe_latency"]=result["latency"];s["last_probe_message"]=result["message"][:500]
                self._save_stats()
                if self.bus:self.bus.emit("router.health",self.stats)
        self._health_thread=threading.Thread(target=loop,daemon=True,name="InfinityRouterHealth");self._health_thread.start()

    def stop_health_monitor(self):self._health_stop.set()

    def arena(self,prompt,provider_names=None):
        selected=[self.provider(n) for n in provider_names] if provider_names else self.providers(True);selected=[x for x in selected if x]
        results=[];lock=threading.Lock();threads=[]
        def run(p):
            try:r=self._request(p,[{"role":"user","content":prompt}])
            except Exception as exc:r={"ok":False,"provider":p.get("name"),"model":p.get("model",""),"text":str(exc),"latency":0}
            with lock:results.append(r)
        for p in selected[:8]:
            t=threading.Thread(target=run,args=(p,),daemon=True);threads.append(t);t.start()
        for t in threads:t.join(timeout=120)
        results.sort(key=lambda r:(not r.get("ok",False),r.get("latency",999)))
        return results
