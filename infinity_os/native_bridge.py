from pathlib import Path
import ctypes, platform
from .paths import ROOT
class NativeBridge:
    def __init__(self):
        self.rust=None;self.cpp=None
        if platform.system()=='Windows':self._load()
    def _load(self):
        for attr,name in [('rust','infinity_native.dll'),('cpp','infinity_telemetry.dll')]:
            p=ROOT/'native'/'bin'/name
            if p.exists():
                try:setattr(self,attr,ctypes.CDLL(str(p)))
                except Exception:pass
    def status(self):return {'rust':'active' if self.rust else 'python-fallback','cpp':'active' if self.cpp else 'python-fallback'}
    def route_score(self,priority,success,latency,preferred=False):
        if self.rust:
            try:
                f=self.rust.infinity_route_score;f.argtypes=[ctypes.c_double,ctypes.c_double,ctypes.c_double,ctypes.c_int];f.restype=ctypes.c_double;return float(f(priority,success,latency,1 if preferred else 0))
            except Exception:pass
        return priority+success*25-min(latency,20)*1.5+(40 if preferred else 0)
