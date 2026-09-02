import os, platform, shutil, socket, time, threading
from pathlib import Path
try: import psutil
except Exception: psutil=None

class SystemMonitor:
    def __init__(self,bus=None,interval=2.0):
        self.bus=bus; self.interval=interval; self.latest={}; self._stop=threading.Event(); self._thread=None

    def snapshot(self):
        disk=shutil.disk_usage(Path.home())
        d={"cpu":0.0,"ram":0.0,"disk":disk.used/disk.total*100 if disk.total else 0,"battery":None,
           "disk_free_gb":disk.free/1024**3,"host":socket.gethostname(),"platform":platform.platform(),"python":platform.python_version(),"uptime":0}
        if psutil:
            try:
                d["cpu"]=psutil.cpu_percent(interval=None); d["ram"]=psutil.virtual_memory().percent
                b=psutil.sensors_battery(); d["battery"]=None if b is None else b.percent; d["uptime"]=time.time()-psutil.boot_time()
            except Exception: pass
        self.latest=d; return d

    def processes(self,limit=60):
        rows=[]
        if psutil:
            for p in psutil.process_iter(["pid","name","cpu_percent","memory_percent"]):
                try:
                    i=p.info; rows.append({"pid":i["pid"],"name":i.get("name") or "","cpu":float(i.get("cpu_percent") or 0),"memory":float(i.get("memory_percent") or 0)})
                except Exception: pass
            rows.sort(key=lambda x:(x["cpu"],x["memory"]),reverse=True)
        return rows[:limit]

    def start(self):
        if self._thread and self._thread.is_alive(): return
        self._stop.clear()
        def loop():
            while not self._stop.wait(self.interval):
                snap=self.snapshot()
                if self.bus:self.bus.emit("system.snapshot",snap)
        self._thread=threading.Thread(target=loop,daemon=True);self._thread.start()

    def stop(self): self._stop.set()
