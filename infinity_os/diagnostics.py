import importlib.util, json, platform, shutil, time, traceback
from .paths import DATA, ROOT, CONFIG

class Diagnostics:
    MODULES={"PySide6":"Native UI","psutil":"System telemetry","pywinauto":"Windows UI Automation","pyautogui":"Desktop fallback","playwright":"Browser Agent","pyperclip":"Clipboard integration","qrcode":"Phone QR","PIL":"Images","speech_recognition":"Speech recognition","sounddevice":"Microphone capture (PyAudio-free)","numpy":"Voice audio processing","pyttsx3":"Voice output"}
    def __init__(self): self.report_path=DATA/"diagnostics.json";self.safe_mode_path=DATA/"SAFE_MODE"
    def run(self):
        checks=[]
        for mod,purpose in self.MODULES.items():checks.append({"name":mod,"purpose":purpose,"ok":bool(importlib.util.find_spec(mod))})
        try:
            probe=DATA/".write_test";probe.write_text("ok",encoding="utf-8");probe.unlink();checks.append({"name":"data-writable","purpose":"Persistent local state","ok":True})
        except Exception as exc:checks.append({"name":"data-writable","purpose":"Persistent local state","ok":False,"message":str(exc)})
        try:
            ppath=CONFIG/"providers.json" if (CONFIG/"providers.json").exists() else CONFIG/"providers.example.json";cfg=json.loads(ppath.read_text(encoding="utf-8"));bad=[p.get("name","Unnamed") for p in cfg.get("providers",[]) if p.get("enabled",True) and (not p.get("base_url") or not (p.get("model") or p.get("models")))];checks.append({"name":"provider-config","purpose":"AI Router configuration","ok":not bad,"message":"Incomplete: "+", ".join(bad) if bad else "Valid"})
        except Exception as exc:checks.append({"name":"provider-config","purpose":"AI Router configuration","ok":False,"message":str(exc)})
        disk=shutil.disk_usage(ROOT);report={"timestamp":time.time(),"platform":platform.platform(),"python":platform.python_version(),"free_gb":disk.free/1024**3,"safe_mode":self.safe_mode_path.exists(),"checks":checks}
        self.report_path.write_text(json.dumps(report,indent=2),encoding="utf-8");return report
    def enable_safe_mode(self):self.safe_mode_path.write_text("1",encoding="utf-8")
    def disable_safe_mode(self):self.safe_mode_path.unlink(missing_ok=True)
    def safe_mode(self):return self.safe_mode_path.exists()
    def record_crash(self,exc):
        (DATA/"last_crash.txt").write_text(f"{time.ctime()}\n{exc}\n\n{traceback.format_exc()}",encoding="utf-8")
