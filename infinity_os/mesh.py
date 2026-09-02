import json, time, uuid
from .paths import DATA, CONFIG

class DeviceMesh:
    def __init__(self,bus=None):self.path=DATA/"mesh_devices.json";self.bus=bus;self.devices={};self.load();self.register_local()
    def load(self):
        try:self.devices=json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:self.devices={}
    def save(self):self.path.write_text(json.dumps(self.devices,indent=2),encoding="utf-8")
    def register_local(self):
        try:cfg=json.loads((CONFIG/"mesh.json").read_text(encoding="utf-8"))
        except Exception:cfg={"device_name":"Infinity Desktop","capabilities":[]}
        self.devices["local"]={"id":"local","name":cfg.get("device_name","Infinity Desktop"),"platform":"windows","capabilities":cfg.get("capabilities",[]),"trusted":True,"online":True,"last_seen":time.time()};self.save()
    def register_remote(self,name,platform,capabilities,trusted=True):
        did=str(uuid.uuid4());self.devices[did]={"id":did,"name":name,"platform":platform,"capabilities":capabilities,"trusted":trusted,"online":True,"last_seen":time.time()};self.save();return did
    def heartbeat(self,did):
        if did in self.devices:self.devices[did]["last_seen"]=time.time();self.devices[did]["online"]=True;self.save()
    def choose(self,required):
        candidates=[]
        for d in self.devices.values():
            if d.get("trusted") and d.get("online") and all(x in d.get("capabilities",[]) for x in required):candidates.append(d)
        candidates.sort(key=lambda d:(d["id"]!="local",-d.get("last_seen",0)))
        return candidates[0] if candidates else None
