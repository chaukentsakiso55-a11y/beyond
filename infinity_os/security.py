from pathlib import Path
import json, time, threading
from .paths import CONFIG, DATA

MODES = ("always_allow", "ask", "session", "deny")
DEFAULTS = {
    "files.read":"always_allow","files.write":"ask","commands.execute":"ask","apps.launch":"session",
    "apps.control":"ask","browser.navigate":"session","browser.form_submit":"ask","messages.send":"ask",
    "clipboard.read":"ask","clipboard.write":"session","microphone":"ask","camera":"deny",
    "power.control":"deny","plugins.execute":"ask","network.remote":"session","network.discovery":"ask"
}

class SecurityEngine:
    def __init__(self):
        self.path = CONFIG / "security.json"
        self.audit_path = DATA / "audit.jsonl"
        self._lock = threading.RLock()
        self.session_grants = set()
        self.policies = self._load()

    def _load(self):
        try:
            data=json.loads(self.path.read_text(encoding="utf-8"))
            return {**DEFAULTS, **{k:v for k,v in data.items() if v in MODES}}
        except Exception:
            return dict(DEFAULTS)

    def save(self):
        self.path.write_text(json.dumps(self.policies, indent=2), encoding="utf-8")

    def set(self, permission, mode):
        if mode not in MODES: raise ValueError(mode)
        self.policies[permission]=mode; self.save(); self.audit("security.policy", {"permission":permission,"mode":mode})

    def decision(self, permission):
        mode=self.policies.get(permission,"ask")
        if mode=="always_allow": return "allow"
        if mode=="deny": return "deny"
        if mode=="session" and permission in self.session_grants: return "allow"
        return "ask"

    def grant_session(self, permission):
        self.session_grants.add(permission); self.audit("security.session_grant", {"permission":permission})

    def revoke_session(self, permission=None):
        if permission: self.session_grants.discard(permission)
        else: self.session_grants.clear()

    def audit(self, action, detail=None, actor="local"):
        record={"timestamp":time.time(),"action":action,"detail":detail or {},"actor":actor}
        with self._lock, self.audit_path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(record,ensure_ascii=False)+"\n")

    def recent(self, limit=250):
        if not self.audit_path.exists(): return []
        try:
            lines=self.audit_path.read_text(encoding="utf-8").splitlines()[-limit:]
            return [json.loads(x) for x in lines]
        except Exception: return []
