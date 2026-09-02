import json, threading
from dataclasses import asdict
from .paths import DATA
from .contracts import Notification

class NotificationCenter:
    def __init__(self, bus=None):
        self.path=DATA/"notifications.json"
        self.bus=bus; self._lock=threading.RLock(); self.items=[]; self.load()

    def load(self):
        try: self.items=json.loads(self.path.read_text(encoding="utf-8"))
        except Exception: self.items=[]

    def save(self):
        self.path.write_text(json.dumps(self.items[-1000:],indent=2),encoding="utf-8")

    def push(self,title,body,level="info",source="Infinity Core"):
        n=Notification.create(title,body,level,source); item=asdict(n)
        with self._lock: self.items.append(item); self.save()
        if self.bus: self.bus.emit("notification.created", item)
        return item

    def mark_read(self, notification_id):
        for n in self.items:
            if n["id"]==notification_id: n["read"]=True
        self.save()

    def unread_count(self): return sum(not n.get("read",False) for n in self.items)
    def recent(self,limit=100): return list(reversed(self.items[-limit:]))
