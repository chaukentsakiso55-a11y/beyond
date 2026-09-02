import queue, threading
from .contracts import ToolResult

class BrowserAgent:
    def __init__(self):
        self.tasks=queue.Queue();self.thread=None;self._ready=threading.Event();self._stop=False;self._error='';self._headless=False
    def available(self):
        try:import playwright.sync_api;return True
        except Exception:return False
    def _loop(self):
        pw=browser=context=page=None
        try:
            from playwright.sync_api import sync_playwright
            pw=sync_playwright().start();browser=pw.chromium.launch(headless=self._headless);context=browser.new_context();page=context.new_page();self._ready.set()
            while not self._stop:
                item=self.tasks.get()
                if item is None:break
                fn,args,event,box=item
                try:box['result']=fn(page,*args)
                except Exception as exc:box['result']=ToolResult(False,str(exc),retryable=True)
                event.set()
        except Exception as exc:self._error=str(exc);self._ready.set()
        finally:
            try:
                if browser:browser.close()
                if pw:pw.stop()
            except Exception:pass
    def start(self,headless=False):
        if self.thread and self.thread.is_alive():return ToolResult(True,'Browser Agent already running')
        if not self.available():return ToolResult(False,'Playwright is not installed')
        self._headless=headless;self._stop=False;self._error='';self._ready.clear();self.thread=threading.Thread(target=self._loop,daemon=True,name='InfinityBrowserAgent');self.thread.start();self._ready.wait(30)
        return ToolResult(False,'Browser Agent failed: '+self._error) if self._error else ToolResult(True,'Browser Agent started')
    def _submit(self,fn,*args,timeout=90):
        r=self.start(False)
        if not r.ok:return r
        event=threading.Event();box={};self.tasks.put((fn,args,event,box))
        if not event.wait(timeout):return ToolResult(False,'Browser Agent timed out',retryable=True)
        return box.get('result',ToolResult(False,'No browser result'))
    def navigate(self,url):
        def op(page,url):page.goto(url,wait_until='domcontentloaded',timeout=60000);return ToolResult(True,'Opened '+url,{'title':page.title(),'url':page.url})
        return self._submit(op,url)
    def text(self,max_chars=30000):
        def op(page,max_chars):return ToolResult(True,'Read page',{'title':page.title(),'url':page.url,'text':page.locator('body').inner_text(timeout=15000)[:max_chars]})
        return self._submit(op,int(max_chars))
    def click_text(self,text):
        def op(page,text):page.get_by_text(text,exact=False).first.click(timeout=15000);return ToolResult(True,'Clicked '+text)
        return self._submit(op,text)
    def fill(self,label_or_selector,value):
        def op(page,label,value):
            try:page.get_by_label(label,exact=False).first.fill(value,timeout=5000)
            except Exception:page.locator(label).first.fill(value,timeout=10000)
            return ToolResult(True,'Filled field')
        return self._submit(op,label_or_selector,value)
    def press(self,key):
        def op(page,key):page.keyboard.press(key);return ToolResult(True,'Pressed '+key)
        return self._submit(op,key)
    def screenshot(self,path):
        def op(page,path):page.screenshot(path=str(path),full_page=False);return ToolResult(True,'Browser screenshot saved',{'path':str(path)})
        return self._submit(op,path)
    def close(self):
        self._stop=True
        if self.thread and self.thread.is_alive():self.tasks.put(None);self.thread.join(timeout=5)
        self.thread=None
