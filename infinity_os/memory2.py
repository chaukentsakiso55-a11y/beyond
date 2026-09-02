import sqlite3, time, uuid, math, re, json
from collections import Counter
from pathlib import Path
from .paths import DATA

TOKEN_RE=re.compile(r"[A-Za-z0-9_]{2,}")
def tokens(text): return [x.lower() for x in TOKEN_RE.findall(text or "")]

def cosine(a,b):
    ca,cb=Counter(tokens(a)),Counter(tokens(b)); common=set(ca)&set(cb)
    dot=sum(ca[k]*cb[k] for k in common); na=math.sqrt(sum(v*v for v in ca.values())); nb=math.sqrt(sum(v*v for v in cb.values()))
    return dot/(na*nb) if na and nb else 0.0

class MemoryEngine2:
    def __init__(self):
        self.path=DATA/"memory2.sqlite3"; self.db=sqlite3.connect(self.path,check_same_thread=False); self.db.row_factory=sqlite3.Row; self._init()

    def _init(self):
        self.db.execute("CREATE TABLE IF NOT EXISTS memories(id TEXT PRIMARY KEY, workspace TEXT, title TEXT, content TEXT, tags TEXT, source TEXT, created REAL, updated REAL)")
        try:self.db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(id UNINDEXED,title,content,tags,workspace)")
        except sqlite3.OperationalError:pass
        self.db.execute("CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, workspace TEXT, name TEXT, path TEXT, content TEXT, created REAL)")
        self.db.commit()

    def add(self,workspace,title,content,tags=None,source="manual"):
        mid=str(uuid.uuid4());now=time.time();tagstr=",".join(tags or [])
        self.db.execute("INSERT INTO memories VALUES(?,?,?,?,?,?,?,?)",(mid,workspace,title,content,tagstr,source,now,now))
        try:self.db.execute("INSERT INTO memory_fts VALUES(?,?,?,?,?)",(mid,title,content,tagstr,workspace))
        except sqlite3.OperationalError:pass
        self.db.commit();return mid

    def update(self,mid,title,content,tags=None):
        now=time.time();tagstr=",".join(tags or [])
        self.db.execute("UPDATE memories SET title=?,content=?,tags=?,updated=? WHERE id=?",(title,content,tagstr,now,mid));self.db.commit()

    def search(self,query,workspace=None,limit=20):
        rows=[]
        if query.strip():
            try:
                sql="SELECT m.* FROM memory_fts f JOIN memories m ON m.id=f.id WHERE memory_fts MATCH ?"
                args=[query]
                if workspace:sql+=" AND m.workspace=?";args.append(workspace)
                sql+=" ORDER BY rank LIMIT ?";args.append(limit*3);rows=list(self.db.execute(sql,args))
            except Exception:rows=[]
        if not rows:
            sql="SELECT * FROM memories";args=[]
            if workspace:sql+=" WHERE workspace=?";args.append(workspace)
            sql+=" ORDER BY updated DESC LIMIT 300";rows=list(self.db.execute(sql,args))
        scored=[]
        for r in rows:
            s=cosine(query, r["title"]+" "+r["content"]+" "+r["tags"]) if query.strip() else 1.0
            scored.append((s,dict(r)))
        scored.sort(key=lambda x:(x[0],x[1]["updated"]),reverse=True)
        return [r for _,r in scored[:limit]]

    def index_document(self,path,workspace="Infinity OS"):
        p=Path(path); content=""
        ext=p.suffix.lower()
        if ext in {".txt",".md",".py",".js",".ts",".java",".kt",".json",".yaml",".yml",".xml",".html",".css",".csv",".log",".sql"}:
            content=p.read_text(encoding="utf-8",errors="replace")[:800000]
        elif ext==".pdf":
            try:
                from pypdf import PdfReader
                content="\n".join((page.extract_text() or "") for page in PdfReader(str(p)).pages)[:800000]
            except Exception: content="[PDF extraction unavailable]"
        elif ext==".docx":
            try:
                from docx import Document
                content="\n".join(x.text for x in Document(str(p)).paragraphs)[:800000]
            except Exception: content="[DOCX extraction unavailable]"
        did=str(uuid.uuid4());self.db.execute("INSERT INTO documents VALUES(?,?,?,?,?,?)",(did,workspace,p.name,str(p),content,time.time()));self.db.commit()
        self.add(workspace,"Document: "+p.name,content,["document",ext.lstrip('.')],"document-index")
        return did

    def context(self,query,workspace=None,limit=8,max_chars=12000):
        out=[];used=0
        for r in self.search(query,workspace,limit):
            block=f"[{r['workspace']}] {r['title']}\n{r['content']}\n"
            if used+len(block)>max_chars:block=block[:max(0,max_chars-used)]
            if block:out.append(block);used+=len(block)
            if used>=max_chars:break
        return "\n---\n".join(out)

    def summarize_chat(self,messages,workspace="Infinity OS",title="Chat summary"):
        text="\n".join(f"{m.get('role','')}: {m.get('content','')}" for m in messages[-40:])
        # Deterministic local summary fallback: preserve recent decisions and user requests without inventing details.
        lines=[x.strip() for x in text.splitlines() if x.strip()]
        summary="\n".join(lines[-20:])[:10000]
        return self.add(workspace,title,summary,["chat-summary"],"chat")

    def close(self):
        try:self.db.close()
        except Exception:pass
