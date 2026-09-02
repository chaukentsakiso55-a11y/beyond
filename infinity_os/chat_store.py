import json,time,uuid,threading
from .paths import DATA
class ChatStore:
    def __init__(self):self.path=DATA/'chats.json';self.chats={};self.lock=threading.RLock();self.load()
    def load(self):
        try:self.chats=json.loads(self.path.read_text(encoding='utf-8'))
        except Exception:self.chats={}
    def save(self):
        with self.lock:self.path.write_text(json.dumps(self.chats,indent=2,ensure_ascii=False),encoding='utf-8')
    def create(self,title='New Chat'):
        cid=str(uuid.uuid4());now=time.time();self.chats[cid]={'id':cid,'title':title,'created':now,'updated':now,'messages':[]};self.save();return cid
    def latest(self):return max(self.chats.values(),key=lambda x:x.get('updated',0))['id'] if self.chats else self.create()
    def add(self,cid,role,content,provider='',model='',attachments=None):
        c=self.chats[cid];m={'id':str(uuid.uuid4()),'role':role,'content':content,'provider':provider,'model':model,'attachments':attachments or [],'at':time.time()};c['messages'].append(m);c['updated']=time.time()
        if c['title']=='New Chat' and role=='user':c['title']=(content.replace('\n',' ')[:45] or 'New Chat')
        self.save();return m
    def all(self,query=''):
        rows=list(self.chats.values());q=query.lower().strip()
        if q:rows=[c for c in rows if q in c.get('title','').lower() or any(q in m.get('content','').lower() for m in c.get('messages',[]))]
        return sorted(rows,key=lambda x:x.get('updated',0),reverse=True)
    def delete(self,cid):self.chats.pop(cid,None);self.save();return self.latest()
