import time, threading
class FocusService:
    def __init__(self,bus=None,notifications=None):self.bus=bus;self.notifications=notifications;self.running=False;self.started=0;self.ends=0;self.total=0;self.intent='';self._lock=threading.RLock()
    def start(self,minutes=25,intent=''):
        with self._lock:self.running=True;self.started=time.time();self.ends=self.started+max(1,int(minutes))*60;self.intent=intent
        if self.bus:self.bus.emit('focus.started',self.status())
        if self.notifications:self.notifications.push('Focus started',f'{int(minutes)} minute session','info','Study Center')
        return self.status()
    def stop(self):
        with self._lock:
            if self.running:self.total+=max(0,time.time()-self.started)
            self.running=False;self.started=0;self.ends=0
        if self.bus:self.bus.emit('focus.stopped',self.status())
        return self.status()
    def status(self):
        with self._lock:
            remaining=max(0,int(self.ends-time.time())) if self.running else 0
            if self.running and remaining<=0:self.total+=max(0,time.time()-self.started);self.running=False;self.started=0;self.ends=0
            return {'running':self.running,'remaining':remaining,'total_seconds':int(self.total),'intent':self.intent}
