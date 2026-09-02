from .contracts import ToolSpec, ToolResult
import inspect

class ToolRegistry:
    def __init__(self):self.tools={}
    def register(self,name,description,permission,handler,source="core",tags=None):
        self.tools[name]=ToolSpec(name,description,permission,handler,source,tags or [])
    def unregister_source(self,source):self.tools={k:v for k,v in self.tools.items() if v.source!=source}
    def get(self,name):return self.tools.get(name)
    def specs(self):
        rows=[]
        for t in self.tools.values():
            try:
                sig=inspect.signature(t.handler);args=[{"name":n,"default":None if p.default is inspect._empty else p.default,"required":p.default is inspect._empty and p.kind not in (p.VAR_KEYWORD,p.VAR_POSITIONAL)} for n,p in sig.parameters.items() if p.kind not in (p.VAR_KEYWORD,p.VAR_POSITIONAL)]
            except Exception:args=[]
            rows.append({"name":t.name,"description":t.description,"permission":t.permission,"source":t.source,"tags":t.tags,"args":args})
        return rows
    def call(self,name,args=None):
        spec=self.get(name)
        if not spec:return ToolResult(False,"Unknown tool: "+name)
        try:return spec.handler(**(args or {}))
        except TypeError as exc:return ToolResult(False,"Invalid tool arguments: "+str(exc))
        except Exception as exc:return ToolResult(False,"Tool failed: "+str(exc),retryable=True)
