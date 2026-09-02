from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
from pathlib import Path
import base64, html, json, mimetypes, socket, threading, time
from .paths import SHARE

PHONE_DIR=Path(__file__).resolve().parent/'phone'

class RemoteServer2:
    def __init__(self,pairing,core,port=8765):
        self.pairing=pairing; self.core=core; self.port=int(port); self.httpd=None; self.thread=None; self.pending={}; SHARE.mkdir(exist_ok=True)
    def ip(self):
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('8.8.8.8',80));ip=s.getsockname()[0];s.close();return ip
        except Exception:return socket.gethostbyname(socket.gethostname())
    def url(self):return f'http://{self.ip()}:{self.port}'
    def start(self):
        if self.httpd:return self.url()
        owner=self
        class H(BaseHTTPRequestHandler):
            def sendx(self,b,typ='application/json',status=200,extra=None):
                if isinstance(b,(dict,list)):b=json.dumps(b).encode()
                elif isinstance(b,str):b=b.encode()
                self.send_response(status);self.send_header('Content-Type',typ);self.send_header('Cache-Control','no-store');self.send_header('X-Frame-Options','DENY');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(b)))
                if extra:
                    for k,v in extra.items():self.send_header(k,v)
                self.end_headers();self.wfile.write(b)
            def auth(self,q):
                t=(q.get('token') or [''])[0];return t if owner.pairing.authorize(t) else None
            def body(self,limit=12000000):
                n=min(int(self.headers.get('Content-Length','0')),limit);return json.loads(self.rfile.read(n).decode() or '{}')
            def pair_page(self,q,error=''):
                pin=html.escape((q.get('pin') or [''])[0][:6],quote=True)
                name=html.escape((q.get('name') or ['My phone'])[0][:80],quote=True)
                message="<p style='color:#ff6b86'>Invalid or expired PIN.</p>" if error else ''
                page=(PHONE_DIR/'pair.html').read_text(encoding='utf-8')
                return page.replace('{{PIN}}',pin).replace('{{NAME}}',name).replace('{{ERROR}}',message)
            def do_GET(self):
                u=urlparse(self.path);q=parse_qs(u.query)
                if u.path in ('/icon.svg','/manifest.webmanifest','/sw.js'):
                    file=PHONE_DIR/u.path.lstrip('/');typ={'icon.svg':'image/svg+xml','manifest.webmanifest':'application/manifest+json','sw.js':'application/javascript'}[file.name];self.sendx(file.read_bytes(),typ);return
                if u.path=='/pair':
                    self.sendx(self.pair_page(q),'text/html; charset=utf-8');return
                if u.path=='/':
                    t=(q.get('token') or [''])[0]
                    if t and owner.pairing.authorize(t):self.sendx((PHONE_DIR/'index.html').read_text(encoding='utf-8'),'text/html; charset=utf-8')
                    else:self.sendx(self.pair_page(q),'text/html; charset=utf-8')
                    return
                t=self.auth(q)
                if not t:self.sendx({'error':'unauthorized'},status=401);return
                if u.path=='/api/status':self.sendx(owner.core.status());return
                if u.path=='/api/activity':self.sendx({'notifications':owner.core.notifications.recent(30),'processes':owner.core.system.processes(30)});return
                if u.path=='/api/chat':
                    cid=owner.core.chats.latest();chat=owner.core.chats.chats.get(cid,{'messages':[]});self.sendx({'chat_id':cid,'title':chat.get('title','New Chat'),'messages':chat.get('messages',[])[-40:]});return
                if u.path=='/api/clipboard':self.sendx({'text':owner.core.get_clipboard(remote=True)});return
                if u.path=='/api/files':self.sendx({'files':[{'name':p.name,'size':p.stat().st_size} for p in sorted(SHARE.iterdir(),key=lambda x:x.stat().st_mtime,reverse=True) if p.is_file()][:100]});return
                if u.path=='/api/download':
                    p=SHARE/Path((q.get('name') or [''])[0]).name
                    if not p.exists() or not p.is_file():self.sendx({'error':'not found'},status=404);return
                    self.sendx(p.read_bytes(),mimetypes.guess_type(p.name)[0] or 'application/octet-stream',extra={'Content-Disposition':f'attachment; filename="{p.name}"'});return
                self.send_error(404)
            def do_POST(self):
                u=urlparse(self.path);q=parse_qs(u.query)
                if u.path=='/pair':
                    n=min(int(self.headers.get('Content-Length','0')),4096)
                    form=parse_qs(self.rfile.read(n).decode('utf-8','replace'))
                    pin=(form.get('pin') or [''])[0].strip();name=(form.get('name') or ['My phone'])[0].strip() or 'My phone'
                    t=owner.pairing.pair(pin,name)
                    if not t:self.sendx(self.pair_page({'pin':[pin],'name':[name]},True),'text/html; charset=utf-8',403);return
                    owner.core.mesh.register_remote(name,'phone',['remote-control','aegis','files','notifications','clipboard'],True)
                    self.send_response(303);self.send_header('Location','/?token='+quote(t));self.send_header('Cache-Control','no-store');self.end_headers();return
                t=self.auth(q)
                if not t:self.sendx({'error':'unauthorized'},status=401);return
                if u.path=='/api/revoke':owner.pairing.revoke(t);self.sendx({'ok':True});return
                if u.path=='/api/aegis':
                    d=self.body(200000);cid=d.get('chat_id') or owner.core.chats.latest();r=owner.core.aegis_answer(str(d.get('message','')),source='phone',chat_id=cid);self.sendx({**r,'chat_id':cid});return
                if u.path=='/api/command':
                    request=str(self.body(100000).get('command','')).strip();plan=owner.core.agent.plan(request)
                    ask=set();denied=[]
                    for step in plan.steps:
                        spec=owner.core.tools.get(step.tool)
                        if not spec or not spec.permission:continue
                        decision=owner.core.security.decision(spec.permission)
                        if decision=='ask':ask.add(spec.permission)
                        elif decision=='deny':denied.append(spec.permission)
                    if denied:self.sendx({'ok':False,'message':'Denied by desktop policy: '+', '.join(sorted(set(denied)))});return
                    if ask:
                        rid=str(time.time_ns());owner.pending[rid]=(plan,ask);self.sendx({'ok':False,'requires_confirmation':True,'request_id':rid,'message':'Confirm on phone: '+', '.join(sorted(ask))});return
                    res=owner.core.agent.execute(plan);self.sendx({'ok':all(x.get('ok') for x in res),'message':'\n'.join(x.get('message','') for x in res),'results':res});return
                if u.path=='/api/confirm':
                    rid=str(self.body(10000).get('request_id',''));item=owner.pending.pop(rid,None)
                    if not item:self.sendx({'ok':False,'message':'Confirmation expired'},status=404);return
                    plan,perms=item;res=owner.core.agent.execute(plan,confirmed_permissions=perms);self.sendx({'ok':all(x.get('ok') for x in res),'message':'\n'.join(x.get('message','') for x in res),'results':res});return
                if u.path=='/api/clipboard':self.sendx({'ok':owner.core.set_clipboard(str(self.body(100000).get('text','')),remote=True)});return
                if u.path=='/api/upload':
                    d=self.body();name=Path(str(d.get('name','upload.bin'))).name;raw=base64.b64decode(d.get('data',''))
                    if len(raw)>8*1024*1024:self.sendx({'ok':False,'message':'8 MB upload limit'},status=413);return
                    p=SHARE/name;n=2
                    while p.exists():p=SHARE/(Path(name).stem+f'-{n}'+Path(name).suffix);n+=1
                    p.write_bytes(raw);owner.core.security.audit('remote.upload',{'file':p.name,'size':len(raw)},'phone');self.sendx({'ok':True,'message':'Uploaded '+p.name});return
                self.send_error(404)
            def log_message(self,*a):pass
        self.httpd=ThreadingHTTPServer(('0.0.0.0',self.port),H);self.thread=threading.Thread(target=self.httpd.serve_forever,daemon=True);self.thread.start();return self.url()
    def stop(self):
        if self.httpd:self.httpd.shutdown();self.httpd.server_close();self.httpd=None
