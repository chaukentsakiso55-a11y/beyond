import json, secrets, time, threading
from .paths import DATA

class PairingManager:
    def __init__(self):
        self.path=DATA/'paired_devices.json'; self.devices={}; self.pin=''; self.pin_expires=0; self.lock=threading.RLock(); self.load(); self.new_pin()
    def load(self):
        try:self.devices=json.loads(self.path.read_text(encoding='utf-8'))
        except Exception:self.devices={}
    def save(self):
        with self.lock:self.path.write_text(json.dumps(self.devices,indent=2),encoding='utf-8')
    def new_pin(self,ttl=600):self.pin=f'{secrets.randbelow(1000000):06d}';self.pin_expires=time.time()+ttl;return self.pin
    def pair(self,pin,name='Phone'):
        if str(pin)!=self.pin or time.time()>=self.pin_expires:return None
        token=secrets.token_urlsafe(32);self.devices[token]={'id':secrets.token_hex(8),'name':name[:80],'created':time.time(),'last_seen':time.time(),'capabilities':['remote-control','aegis','files','notifications','clipboard']};self.save();self.new_pin();return token
    def authorize(self,token):
        if token not in self.devices:return False
        self.devices[token]['last_seen']=time.time();self.save();return True
    def revoke(self,token):self.devices.pop(token,None);self.save()
    def all(self):return sorted([(t,d) for t,d in self.devices.items()],key=lambda x:x[1].get('last_seen',0),reverse=True)
