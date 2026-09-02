import json, threading, time
from .paths import CONFIG

class VoiceAegis:
    def __init__(self,bus=None):
        self.bus=bus;self.path=CONFIG/"wakewords.json";self._stop=threading.Event();self._thread=None;self.config=self.load()
    def load(self):
        try:return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:return {"enabled":False,"wakewords":["hey aegis","hey infinity"],"listen_seconds":8}
    def save(self):self.path.write_text(json.dumps(self.config,indent=2),encoding="utf-8")
    def speak(self,text):
        try:
            import pyttsx3
            def run():
                e=pyttsx3.init();e.say((text or "")[:12000]);e.runAndWait()
            threading.Thread(target=run,daemon=True).start();return True,"Speaking"
        except Exception as exc:return False,str(exc)

    def _listen_with_pyaudio(self,timeout,phrase_time_limit):
        import speech_recognition as sr
        r=sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source,duration=.4)
            audio=r.listen(source,timeout=timeout,phrase_time_limit=phrase_time_limit)
        return r.recognize_google(audio)

    def _listen_with_sounddevice(self,seconds):
        """PyAudio-free Windows microphone fallback using sounddevice."""
        import numpy as np
        import sounddevice as sd
        import speech_recognition as sr
        rate=16000
        seconds=max(2.0,min(float(seconds or 8),15.0))
        frames=int(rate*seconds)
        audio=sd.rec(frames,samplerate=rate,channels=1,dtype="int16")
        sd.wait()
        pcm=np.asarray(audio,dtype=np.int16).reshape(-1).tobytes()
        if not pcm:
            raise RuntimeError("No microphone audio was captured.")
        recognizer=sr.Recognizer()
        return recognizer.recognize_google(sr.AudioData(pcm,rate,2))

    def listen_once(self,timeout=8,phrase_time_limit=30):
        try:
            return True,self._listen_with_pyaudio(timeout,phrase_time_limit)
        except Exception as first:
            try:
                seconds=min(int(self.config.get("listen_seconds",8) or 8),int(phrase_time_limit or 30))
                return True,self._listen_with_sounddevice(seconds)
            except Exception as second:
                msg=str(second) or str(first)
                low=msg.lower()+" "+str(first).lower()
                if "sounddevice" in low or "no module named" in low:
                    msg="Voice input dependency is missing. Run RUN-INFINITY.bat again so Infinity can install sounddevice and NumPy."
                elif "portaudio" in low or "device" in low:
                    msg="Infinity could not access a microphone. Check Windows microphone permissions and your default input device."
                elif "recogn" in low or "google" in low or "network" in low:
                    msg="Audio was captured, but speech recognition failed. Check your internet connection and try again."
                return False,msg

    def start_wake_listener(self,on_command):
        if self._thread and self._thread.is_alive():return
        self._stop.clear()
        def loop():
            while not self._stop.is_set():
                ok,text=self.listen_once(timeout=3,phrase_time_limit=int(self.config.get("listen_seconds",8)))
                if not ok:
                    time.sleep(1.0);continue
                low=text.lower();wake=next((w for w in self.config.get("wakewords",[]) if w in low),None)
                if wake:
                    command=low.split(wake,1)[1].strip()
                    if command:on_command(command)
        self._thread=threading.Thread(target=loop,daemon=True);self._thread.start()
    def stop(self):self._stop.set()
