import json, subprocess, threading, queue, itertools, time
from .contracts import ToolResult

class MCPStdioClient:
    def __init__(self,name,command,args=None):
        self.name=name;self.command=command;self.args=args or [];self.proc=None;self.ids=itertools.count(1);self.pending={};self.lock=threading.RLock();self.reader=None
    def start(self):
        if self.proc and self.proc.poll() is None:return True
        self.proc=subprocess.Popen([self.command,*self.args],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
        self.reader=threading.Thread(target=self._reader,daemon=True);self.reader.start()
        try:
            self.request('initialize',{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'Infinity OS','version':'7.9.0'}},20)
            self.notify('notifications/initialized',{})
            return True
        except Exception:
            self.stop();raise
    def _reader(self):
        while self.proc and self.proc.poll() is None:
            line=self.proc.stdout.readline()
            if not line:break
            try:data=json.loads(line)
            except Exception:continue
            rid=data.get('id')
            if rid in self.pending:self.pending[rid].put(data)
    def _send(self,obj):
        if not self.proc or self.proc.poll() is not None:raise RuntimeError('MCP server is not running')
        with self.lock:self.proc.stdin.write(json.dumps(obj,separators=(',',':'))+'\n');self.proc.stdin.flush()
    def request(self,method,params=None,timeout=30):
        rid=next(self.ids);q=queue.Queue(maxsize=1);self.pending[rid]=q;self._send({'jsonrpc':'2.0','id':rid,'method':method,'params':params or {}})
        try:data=q.get(timeout=timeout)
        finally:self.pending.pop(rid,None)
        if 'error' in data:raise RuntimeError(str(data['error']))
        return data.get('result',{})
    def notify(self,method,params=None):self._send({'jsonrpc':'2.0','method':method,'params':params or {}})
    def list_tools(self):return self.request('tools/list',{},30).get('tools',[])
    def call_tool(self,name,arguments=None):
        result=self.request('tools/call',{'name':name,'arguments':arguments or {}},60);parts=result.get('content',[]);text='\n'.join(x.get('text','') for x in parts if x.get('type')=='text');return ToolResult(not result.get('isError',False),text or ('MCP tool completed' if not result.get('isError') else 'MCP tool error'),{'raw':result})
    def stop(self):
        if self.proc:
            try:self.proc.terminate();self.proc.wait(timeout=3)
            except Exception:
                try:self.proc.kill()
                except Exception:pass
        self.proc=None
