from pathlib import Path
import importlib.util, json, subprocess, threading, time
from .paths import ROOT, DATA
from .contracts import ToolResult
from .mcp_client import MCPStdioClient

class PluginManager:
    def __init__(self,registry,security,notifications=None):
        self.dir=ROOT/"plugins";self.dir.mkdir(exist_ok=True);self.registry=registry;self.security=security;self.notifications=notifications;self.plugins={};self.mcp_path=DATA/"mcp_servers.json";self.mcp_servers=[];self.mcp_processes={};self.scan();self.load_mcp()
    def scan(self):
        self.plugins={}
        for folder in self.dir.iterdir():
            if not folder.is_dir():continue
            manifest=folder/"manifest.json"
            if not manifest.exists():continue
            try:
                data=json.loads(manifest.read_text(encoding="utf-8"));data["path"]=str(folder);self.plugins[data.get("id",folder.name)]=data
            except Exception:pass
        return self.plugins
    def load_plugin(self,pid):
        if self.security.decision("plugins.execute")!="allow":return False,"Plugin execution must be allowed or granted for this session"
        p=self.plugins.get(pid)
        if not p:return False,"Plugin not found"
        main=Path(p["path"])/(p.get("entrypoint") or "plugin.py")
        if not main.exists():return False,"Entrypoint missing"
        try:
            spec=importlib.util.spec_from_file_location("infinity_plugin_"+pid.replace("-","_"),main);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
            if not hasattr(mod,"register"):return False,"Plugin has no register(registry) function"
            mod.register(self.registry);p["loaded"]=True;return True,"Loaded"
        except Exception as exc:return False,str(exc)
    def load_all(self):
        result={}
        for pid in self.plugins:
            if self.plugins[pid].get("enabled",True):result[pid]=self.load_plugin(pid)
        return result
    def load_mcp(self):
        try:self.mcp_servers=json.loads(self.mcp_path.read_text(encoding="utf-8"))
        except Exception:self.mcp_servers=[]
    def save_mcp(self):self.mcp_path.write_text(json.dumps(self.mcp_servers,indent=2),encoding="utf-8")
    def add_mcp_server(self,name,command,args=None):
        item={"name":name,"command":command,"args":args or [],"enabled":True};self.mcp_servers.append(item);self.save_mcp();return item
    def start_mcp(self,name):
        srv=next((x for x in self.mcp_servers if x["name"]==name),None)
        if not srv:return False,"Server not configured"
        if self.security.decision("plugins.execute")!="allow":return False,"Plugin/MCP execution must be allowed or granted for this session"
        try:
            client=MCPStdioClient(name,srv["command"],srv.get("args",[]));client.start();self.mcp_processes[name]=client
            tools=client.list_tools()
            for tool in tools:
                tname=tool.get("name","");description=tool.get("description","")
                if not tname:continue
                exposed=f"mcp.{name}.{tname}"
                self.registry.register(exposed,description,"plugins.execute",lambda _client=client,_name=tname,**kwargs:_client.call_tool(_name,kwargs),source="mcp:"+name,tags=["mcp",name])
            return True,f"Connected. Registered {len(tools)} MCP tools."
        except Exception as exc:return False,str(exc)
    def stop_all(self):
        for p in self.mcp_processes.values():
            try:p.stop()
            except Exception:pass
        self.mcp_processes={}
