import os, re, shutil, subprocess, time, urllib.parse, webbrowser
from .contracts import ToolResult

class WindowsAutomation:
    APP_ALIASES={"notepad":"notepad.exe","calculator":"calc.exe","calc":"calc.exe","file explorer":"explorer.exe","explorer":"explorer.exe","powershell":"powershell.exe","terminal":"wt.exe","command prompt":"cmd.exe","cmd":"cmd.exe","paint":"mspaint.exe","settings":"ms-settings:","task manager":"taskmgr.exe","edge":"msedge.exe","microsoft edge":"msedge.exe","chrome":"chrome.exe","google chrome":"chrome.exe","firefox":"firefox.exe","vscode":"code.exe","visual studio code":"code.exe","whatsapp":"whatsapp:","spotify":"spotify:"}
    def __init__(self,security=None):self.security=security
    def _pyauto(self):
        try:import pyautogui;pyautogui.FAILSAFE=True;return pyautogui
        except Exception:return None
    def _desktop(self):
        try:
            from pywinauto import Desktop
            return Desktop(backend="uia")
        except Exception:return None
    def open_app(self,name):
        target=self.APP_ALIASES.get(name.lower().strip(),name.strip())
        try:
            if target.endswith(":") or target.startswith("ms-settings:"):os.startfile(target)
            else:
                found=shutil.which(target)
                if found:subprocess.Popen([found])
                else:subprocess.Popen(["cmd","/c","start","",target],shell=False)
            return ToolResult(True,f"Opened {name}")
        except Exception as exc:return ToolResult(False,f"Could not open {name}: {exc}",retryable=True)
    def windows(self):
        d=self._desktop();out=[]
        if d:
            try:
                for w in d.windows():
                    title=w.window_text().strip()
                    if title:out.append({"title":title,"type":w.element_info.control_type,"handle":w.handle})
            except Exception:pass
        return out[:100]
    def focus_window(self,title_contains):
        d=self._desktop()
        if not d:return ToolResult(False,"pywinauto is not available; UI Automation cannot focus by semantic window title.")
        try:
            for w in d.windows():
                if title_contains.lower() in w.window_text().lower():w.set_focus();return ToolResult(True,"Focused "+w.window_text())
            return ToolResult(False,"No matching window found")
        except Exception as exc:return ToolResult(False,str(exc))
    def find_controls(self,window_title):
        d=self._desktop()
        if not d:return []
        try:
            win=next((w for w in d.windows() if window_title.lower() in w.window_text().lower()),None)
            if not win:return []
            rows=[]
            for c in win.descendants():
                try:
                    name=c.window_text().strip();ctype=c.element_info.control_type
                    if name:rows.append({"name":name,"type":ctype,"automation_id":getattr(c.element_info,"automation_id","")})
                except Exception:pass
            return rows[:400]
        except Exception:return []
    def click_control(self,window_title,control_name):
        d=self._desktop()
        if d:
            try:
                win=next((w for w in d.windows() if window_title.lower() in w.window_text().lower()),None)
                if win:
                    candidates=[c for c in win.descendants() if control_name.lower() in c.window_text().lower()]
                    if candidates:candidates[0].click_input();return ToolResult(True,f"Clicked {control_name} in {win.window_text()}")
            except Exception:pass
        return ToolResult(False,"Semantic UI control not found",retryable=True)

    def close_window(self,title_contains):
        d=self._desktop()
        if not d:return ToolResult(False,"pywinauto is not available")
        try:
            for w in d.windows():
                if title_contains.lower() in w.window_text().lower():w.close();return ToolResult(True,"Closed "+w.window_text())
            return ToolResult(False,"No matching window found")
        except Exception as exc:return ToolResult(False,str(exc))
    def media_key(self,key,count=1):
        p=self._pyauto()
        if not p:return ToolResult(False,"pyautogui unavailable")
        p.press(key,presses=int(count),interval=.05);return ToolResult(True,"Media control executed")
    def type_text(self,text):
        p=self._pyauto()
        if not p:return ToolResult(False,"pyautogui is unavailable")
        p.write(text,interval=0.012);return ToolResult(True,"Typed text")
    def hotkey(self,keys):
        p=self._pyauto()
        if not p:return ToolResult(False,"pyautogui is unavailable")
        aliases={"control":"ctrl","escape":"esc","windows":"win","return":"enter"};keys=[aliases.get(x.lower(),x.lower()) for x in keys]
        if len(keys)==1:p.press(keys[0])
        else:p.hotkey(*keys)
        return ToolResult(True,"Pressed "+" + ".join(keys))
    def click(self,x,y):
        p=self._pyauto()
        if not p:return ToolResult(False,"pyautogui unavailable")
        p.click(x=int(x),y=int(y));return ToolResult(True,f"Clicked {x},{y}")
    def scroll(self,amount):
        p=self._pyauto()
        if not p:return ToolResult(False,"pyautogui unavailable")
        p.scroll(int(amount));return ToolResult(True,"Scrolled")
    def screenshot(self,path):
        p=self._pyauto()
        if not p:return ToolResult(False,"pyautogui unavailable")
        p.screenshot(str(path));return ToolResult(True,f"Screenshot saved: {path}",{"path":str(path)})
    def open_url(self,url):
        if not re.match(r"^[a-z]+://",url,re.I):url="https://"+url
        webbrowser.open(url);return ToolResult(True,"Opened "+url)
    def search_web(self,query):return self.open_url("https://www.google.com/search?q="+urllib.parse.quote_plus(query))
    def send_whatsapp(self,recipient,message):
        clean=re.sub(r"\D","",recipient)
        p=self._pyauto()
        if len(clean)>=8:
            webbrowser.open("https://wa.me/"+clean+"?text="+urllib.parse.quote(message));return ToolResult(True,"Prepared WhatsApp message in browser. Confirm/send in WhatsApp if needed.")
        r=self.open_app("whatsapp")
        if not r.ok or not p:return ToolResult(False,"Could not automate WhatsApp contact by name")
        time.sleep(3);p.hotkey("ctrl","f");time.sleep(.5);p.write(recipient,interval=.03);time.sleep(1);p.press("enter");time.sleep(1);p.write(message,interval=.02);p.press("enter")
        return ToolResult(True,f"Attempted to send WhatsApp message to {recipient}")
