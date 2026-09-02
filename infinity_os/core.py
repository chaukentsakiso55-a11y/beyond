from pathlib import Path
import json, os, re, subprocess, time, urllib.parse
from .paths import ROOT, DATA, SHARE, CONFIG
from .event_bus import EventBus
from .security import SecurityEngine
from .notifications import NotificationCenter
from .system_monitor import SystemMonitor
from .router2 import Router2
from .memory2 import MemoryEngine2
from .tool_registry import ToolRegistry
from .windows_automation import WindowsAutomation
from .browser_agent import BrowserAgent
from .agent_engine import AgentEngine
from .workflows import WorkflowEngine
from .plugin_manager import PluginManager
from .forge2 import Forge2
from .voice2 import VoiceAegis
from .updater import UpdateManager
from .mesh import DeviceMesh
from .network_discovery import NetworkDiscovery
from .pairing import PairingManager
from .remote_server2 import RemoteServer2
from .chat_store import ChatStore
from .attachments import AttachmentManager
from .appearance import AppearanceManager
from .diagnostics import Diagnostics
from .native_bridge import NativeBridge
from .focus_service import FocusService
from .contracts import ToolResult

class InfinityCore:
    def __init__(self,confirm_callback=None):
        self.bus=EventBus();self.security=SecurityEngine();self.notifications=NotificationCenter(self.bus);self.system=SystemMonitor(self.bus);self.router=Router2(self.bus,self.notifications);self.memory=MemoryEngine2();self.tools=ToolRegistry();self.windows=WindowsAutomation(self.security);self.browser=BrowserAgent();self.forge=Forge2(self.security);self.voice=VoiceAegis(self.bus);self.mesh=DeviceMesh(self.bus);self.network=NetworkDiscovery(self.security);self.pairing=PairingManager();self.chats=ChatStore();self.attachments=AttachmentManager();self.appearance=AppearanceManager();self.focus=FocusService(self.bus,self.notifications);self.diagnostics=Diagnostics();self.native=NativeBridge();self.router.native=self.native;self.updater=UpdateManager();self._confirm_callback=confirm_callback;self._register_tools();self.plugins=PluginManager(self.tools,self.security,self.notifications);self.workflows=WorkflowEngine(self.tools,self.security,self.bus,self.notifications);self.agent=AgentEngine(self.router,self.tools,self.security,self.memory,self.notifications,self.bus,confirm_callback);self.remote=RemoteServer2(self.pairing,self,self._remote_port());self.started=time.time()
    def _remote_port(self):
        try:return int(json.loads((CONFIG/'control.json').read_text(encoding='utf-8')).get('remote_port',8765))
        except Exception:return 8765
    def set_confirm_callback(self,cb):self._confirm_callback=cb;self.agent.confirm_callback=cb
    def _register_tools(self):
        r=self.tools.register
        r('aegis.answer','Ask the configured AI router for a direct answer','',lambda prompt:ToolResult(True,self.router.ask(prompt).get('text','')))
        r('windows.open_app','Open a Windows application','apps.launch',self.windows.open_app,tags=['windows'])
        r('windows.focus','Focus a window by title','apps.control',self.windows.focus_window,tags=['windows'])
        r('windows.close','Close a window by title','apps.control',self.windows.close_window,tags=['windows'])
        r('windows.click_control','Click a named UI Automation control','apps.control',self.windows.click_control,tags=['windows','uia'])
        r('windows.type','Type text into the active application','apps.control',self.windows.type_text,tags=['windows'])
        r('windows.hotkey','Press one or more keyboard keys','apps.control',lambda keys:self.windows.hotkey(keys),tags=['windows'])
        r('windows.click','Click screen coordinates','apps.control',self.windows.click,tags=['windows','fallback'])
        r('windows.scroll','Scroll active window','apps.control',self.windows.scroll,tags=['windows'])
        r('windows.volume_up','Increase system volume','apps.control',lambda count=5:self.windows.media_key('volumeup',count),tags=['windows','media'])
        r('windows.volume_down','Decrease system volume','apps.control',lambda count=5:self.windows.media_key('volumedown',count),tags=['windows','media'])
        r('windows.mute','Toggle system mute','apps.control',lambda:self.windows.media_key('volumemute',1),tags=['windows','media'])
        r('windows.media_play_pause','Play or pause media','apps.control',lambda:self.windows.media_key('playpause',1),tags=['windows','media'])
        r('windows.media_next','Next media track','apps.control',lambda:self.windows.media_key('nexttrack',1),tags=['windows','media'])
        r('windows.media_previous','Previous media track','apps.control',lambda:self.windows.media_key('prevtrack',1),tags=['windows','media'])
        r('windows.open_url','Open a URL in the default browser','browser.navigate',self.windows.open_url,tags=['browser'])
        r('browser.search','Search the web in a browser','browser.navigate',self.windows.search_web,tags=['browser'])
        r('browser.navigate','Navigate with the Playwright Browser Agent','browser.navigate',self.browser.navigate,tags=['browser','agent'])
        r('browser.read','Read visible page text','',lambda:self.browser.text(),tags=['browser','agent'])
        r('browser.click_text','Click page content by visible text','browser.form_submit',self.browser.click_text,tags=['browser','agent'])
        r('browser.fill','Fill a browser field','browser.form_submit',self.browser.fill,tags=['browser','agent'])
        r('browser.press','Press a browser keyboard key','browser.form_submit',self.browser.press,tags=['browser','agent'])
        r('messages.whatsapp','Send or prepare a WhatsApp message','messages.send',self.windows.send_whatsapp,tags=['messaging'])
        r('system.screenshot','Take a screenshot','apps.control',self._screenshot,tags=['system'])
        r('system.status','Read system telemetry','',lambda:ToolResult(True,'System status',self.status()),tags=['system'])
        r('network.discover_lan','Discover devices on the private local network without port scanning','network.discovery',self.network.discover_lan,tags=['network','mesh'])
        r('network.discover_bluetooth','List present or known Bluetooth devices visible to Windows','network.discovery',self.network.discover_bluetooth,tags=['network','mesh','bluetooth'])
        r('focus.start','Start an Infinity focus session','',lambda minutes=25,intent='':ToolResult(True,'Focus session started',self.focus.start(minutes,intent)),tags=['study'])
        r('focus.stop','Stop the current Infinity focus session','',lambda:ToolResult(True,'Focus session stopped',self.focus.stop()),tags=['study'])
        r('files.read','Read a text file','files.read',self._read_file,tags=['files'])
        r('files.write','Write a text file','files.write',self._write_file,tags=['files'])
        r('terminal.run','Run a local shell command','commands.execute',self._run_command,tags=['terminal'])
        r('power.shutdown','Shut down Windows','power.control',lambda:self._power('shutdown'),tags=['system','power'])
        r('power.restart','Restart Windows','power.control',lambda:self._power('restart'),tags=['system','power'])
        r('power.sleep','Put Windows to sleep','power.control',lambda:self._power('sleep'),tags=['system','power'])
        r('clipboard.read','Read the Windows clipboard','clipboard.read',lambda:ToolResult(True,'Clipboard read',{'text':self.get_clipboard()}),tags=['clipboard'])
        r('clipboard.write','Write the Windows clipboard','clipboard.write',lambda text:ToolResult(self.set_clipboard(text),'Clipboard updated'),tags=['clipboard'])
    def _screenshot(self):
        folder=DATA/'screenshots';folder.mkdir(exist_ok=True);return self.windows.screenshot(folder/f'screenshot_{int(time.time())}.png')
    def _power(self,action):
        try:
            if action=='shutdown':subprocess.Popen(['shutdown','/s','/t','0'])
            elif action=='restart':subprocess.Popen(['shutdown','/r','/t','0'])
            elif action=='sleep':subprocess.Popen(['rundll32.exe','powrprof.dll,SetSuspendState','0,1,0'])
            return ToolResult(True,'Power action requested: '+action)
        except Exception as exc:return ToolResult(False,str(exc))
    def _read_file(self,path):
        p=Path(path);return ToolResult(True,'Read '+p.name,{'text':p.read_text(encoding='utf-8',errors='replace')[:500000]})
    def _write_file(self,path,content):
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content,encoding='utf-8');return ToolResult(True,'Wrote '+str(p))
    def _run_command(self,command,cwd=None,timeout=120):
        try:
            p=subprocess.run(command,cwd=cwd or str(ROOT),shell=True,capture_output=True,text=True,timeout=int(timeout));return ToolResult(p.returncode==0,'Command finished',{'code':p.returncode,'stdout':p.stdout[-30000:],'stderr':p.stderr[-30000:]})
        except Exception as exc:return ToolResult(False,str(exc),retryable=True)
    def status(self):
        s=self.system.snapshot();return {**s,'version':'7.9.0-ultimate','host':s.get('host'),'router_providers':len(self.router.providers(True)),'notifications':self.notifications.unread_count(),'remote_online':bool(self.remote.httpd),'native':self.native.status(),'focus':self.focus.status(),'uptime_infinity':time.time()-self.started}
    def aegis_answer(self,message,workspace='Infinity OS',source='desktop',attachments=None,chat_id=None):
        message=(message or '').strip();cid=chat_id or self.chats.latest();items=attachments or [];self.chats.add(cid,'user',message,attachments=items);context=self.memory.context(message,workspace,8,10000);file_context=self.attachments.context(items)
        system='You are AEGIS in Infinity OS. Be concise, capable, preserve architecture, clearly state limitations, and use supplied local project context when relevant.'
        prompt=message
        if context:prompt+='\n\nPROJECT MEMORY:\n'+context
        if file_context:prompt+='\n\nATTACHED FILES:\n'+file_context
        r=self.router.ask(prompt,task='coding' if any(k in message.lower() for k in ('code','build','debug','project')) else 'default',system=system);self.chats.add(cid,'assistant',r.get('text',''),r.get('provider',''),r.get('model',''));
        chat=self.chats.chats.get(cid,{});
        if len(chat.get('messages',[]))>=10 and len(chat.get('messages',[]))%10==0:self.memory.summarize_chat(chat.get('messages',[]),workspace,'Chat summary: '+chat.get('title','AEGIS'))
        self.security.audit('aegis.chat',{'source':source,'provider':r.get('provider'),'chat_id':cid},source);return r
    def get_clipboard(self,remote=False):
        if remote and self.security.decision('clipboard.read')=='deny':return ''
        try:return subprocess.check_output(['powershell','-NoProfile','-Command','Get-Clipboard -Raw'],text=True,timeout=5).rstrip('\r\n')
        except Exception:
            try:
                import pyperclip;return pyperclip.paste()
            except Exception:return ''
    def set_clipboard(self,text,remote=False):
        if remote and self.security.decision('clipboard.write')=='deny':return False
        try:
            subprocess.run(['powershell','-NoProfile','-Command','$input | Set-Clipboard'],input=text,text=True,timeout=5,check=True);self.security.audit('clipboard.write',{'chars':len(text)},'phone' if remote else 'local');return True
        except Exception:
            try:
                import pyperclip;pyperclip.copy(text);return True
            except Exception:return False
    def start(self):
        report=self.diagnostics.run();self.system.start();self.router.start_health_monitor();
        if not self.diagnostics.safe_mode():
            self.workflows.start_scheduler();self.plugins.load_all()
        else:self.notifications.push('Safe Mode active','Plugins, scheduled workflows, wake-word listener and automatic remote services are disabled.','warning','Recovery')
        self.notifications.push('Infinity Core online','AEGIS, Router 2.0, Memory 2.0 and automation services started.','success')
        return report
    def shutdown(self):
        self.workflows.stop();self.system.stop();self.router.stop_health_monitor();self.browser.close();self.remote.stop();self.plugins.stop_all();self.voice.stop();self.memory.close();self.security.revoke_session()
