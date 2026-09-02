import json, time, uuid, threading
from .paths import DATA

class WorkflowEngine:
    def __init__(self,tools,security,bus=None,notifications=None):
        self.path=DATA/"workflows.json";self.tools=tools;self.security=security;self.bus=bus;self.notifications=notifications;self.workflows=[];self._stop=threading.Event();self._thread=None;self.load()
    def load(self):
        try:self.workflows=json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:self.workflows=[]
    def save(self):self.path.write_text(json.dumps(self.workflows,indent=2),encoding="utf-8")
    def create(self,name,steps,interval_minutes=0,enabled=True):
        normalized=[];previous=None
        for raw in steps:
            step=dict(raw);step.setdefault("id",str(uuid.uuid4()));step.setdefault("depends_on",[previous] if previous else []);normalized.append(step);previous=step["id"]
        item={"id":str(uuid.uuid4()),"name":name,"steps":normalized,"interval_minutes":int(interval_minutes or 0),"enabled":enabled,"created":time.time(),"last_run":0,"next_run":0,"history":[]}
        if item["interval_minutes"]:item["next_run"]=time.time()+item["interval_minutes"]*60
        self.workflows.append(item);self.save();return item
    def delete(self,wid):self.workflows=[x for x in self.workflows if x["id"]!=wid];self.save()
    def toggle(self,wid):
        for x in self.workflows:
            if x["id"]==wid:x["enabled"]=not x.get("enabled",True)
        self.save()
    def run(self,wid):
        wf=next((x for x in self.workflows if x["id"]==wid),None)
        if not wf:return {"ok":False,"message":"Workflow not found"}
        steps=[dict(x) for x in wf.get("steps",[])];completed={};output=[];guard=0
        while len(completed)<len(steps) and guard<len(steps)*3+3:
            guard+=1;progress=False
            for step in steps:
                sid=step.get("id") or str(uuid.uuid4());step["id"]=sid
                if sid in completed:continue
                deps=step.get("depends_on") or []
                if not all(d in completed and completed[d].get("ok") for d in deps):continue
                spec=self.tools.get(step.get("tool",""))
                if not spec:r={"ok":False,"message":"Unknown tool "+step.get("tool","")}
                elif spec.permission and self.security.decision(spec.permission)!="allow":r={"ok":False,"message":"Workflow requires permission: "+spec.permission}
                else:
                    result=self.tools.call(spec.name,step.get("args") or {});r={"ok":result.ok,"message":result.message,"data":result.data}
                completed[sid]=r;output.append({"step":sid,**r});progress=True
            if not progress:break
        blocked=[s.get("id") for s in steps if s.get("id") not in completed]
        if blocked:output.append({"ok":False,"message":"Blocked dependencies or cycle: "+", ".join(blocked),"blocked":blocked})
        wf["last_run"]=time.time();wf["history"]=(wf.get("history",[])+[{"at":wf["last_run"],"results":output}])[-30:]
        if wf.get("interval_minutes"):wf["next_run"]=time.time()+wf["interval_minutes"]*60
        self.save();ok=bool(output) and all(x.get("ok") for x in output)
        if self.notifications:self.notifications.push("Workflow finished",wf["name"]+": "+("success" if ok else "stopped"),"success" if ok else "warning","Workflows")
        return {"ok":ok,"results":output}

    def start_scheduler(self):
        if self._thread and self._thread.is_alive():return
        self._stop.clear()
        def loop():
            while not self._stop.wait(15):
                now=time.time()
                for wf in list(self.workflows):
                    if wf.get("enabled") and wf.get("interval_minutes") and wf.get("next_run",0)<=now:
                        threading.Thread(target=self.run,args=(wf["id"],),daemon=True).start()
        self._thread=threading.Thread(target=loop,daemon=True);self._thread.start()
    def stop(self):self._stop.set()
