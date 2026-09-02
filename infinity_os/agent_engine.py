import json, re, time, uuid
from dataclasses import asdict
from .contracts import AgentPlan, AgentStep, ToolResult

class AgentEngine:
    def __init__(self,router,tools,security,memory,notifications=None,bus=None,confirm_callback=None):
        self.router=router;self.tools=tools;self.security=security;self.memory=memory;self.notifications=notifications;self.bus=bus;self.confirm_callback=confirm_callback

    def _deterministic_plan(self,request):
        request=(request or "").strip();steps=[]
        def add(title,tool,args):
            spec=self.tools.get(tool);steps.append(AgentStep(str(uuid.uuid4()),title,tool,args,spec.permission if spec else ""))
        # High-confidence compound messaging: the message tool can open WhatsApp itself.
        msg=re.search(r"(?:open\s+whatsapp\s+(?:and|then)\s+)?(?:send\s+(?:a\s+)?message|message)\s+(?:to\s+)?(.+?)\s+(?:on\s+whatsapp\s+)?(?:saying|that says|with message)\s+(.+)$",request,re.I)
        if msg:
            add("Send WhatsApp message","messages.whatsapp",{"recipient":msg.group(1).strip(),"message":msg.group(2).strip()})
            return AgentPlan(str(uuid.uuid4()),request,steps)
        # Open an app then type into it.
        typed=re.match(r"(?:open|launch|start)\s+(.+?)\s+(?:and|then)\s+type\s+(.+)$",request,re.I)
        if typed:
            add("Open application","windows.open_app",{"name":typed.group(1).strip()});add("Type text","windows.type",{"text":typed.group(2).strip()});return AgentPlan(str(uuid.uuid4()),request,steps)
        # Split explicit multi-step phrasing. Avoid generic 'and' because it often belongs inside content.
        clauses=[x.strip(" ,") for x in re.split(r"\s*(?:;|,\s*then\s+|\s+and\s+then\s+|\s+then\s+)\s*",request,flags=re.I) if x.strip(" ,")]
        if len(clauses)==1 and "," in request:
            candidate=[x.strip() for x in request.split(",") if x.strip()]
            if all(re.match(r"(?i)^(open|launch|start|search|google|go to|browse to|press|click|scroll|type|close|take screenshot|screenshot|volume|mute|shutdown|restart|reboot|sleep)",x) for x in candidate):clauses=candidate
        recognized=0
        for clause in clauses:
            c=clause.strip();low=c.lower()
            fm=re.match(r"(?:start\s+)?focus(?:\s+(\d+))?(?:\s+minutes?)?$",c,re.I)
            if fm:add("Start focus session","focus.start",{"minutes":int(fm.group(1) or 25)});recognized+=1;continue
            if low in ("stop focus","end focus","finish focus"):add("Stop focus session","focus.stop",{});recognized+=1;continue
            m=re.match(r"(?:open|launch|start)\s+(.+)$",c,re.I)
            if m:add("Open application","windows.open_app",{"name":m.group(1).strip()});recognized+=1;continue
            m=re.match(r"(?:close|quit)\s+(.+)$",c,re.I)
            if m:add("Close window","windows.close",{"title_contains":m.group(1).strip()});recognized+=1;continue
            m=re.match(r"(?:search(?: the)? web for|search for|google)\s+(.+)$",c,re.I)
            if m:add("Search web","browser.search",{"query":m.group(1).strip()});recognized+=1;continue
            m=re.match(r"(?:go to|browse to|open url)\s+(.+)$",c,re.I)
            if m:add("Open URL","windows.open_url",{"url":m.group(1).strip()});recognized+=1;continue
            m=re.match(r"type\s+(.+)$",c,re.I)
            if m:add("Type text","windows.type",{"text":m.group(1)});recognized+=1;continue
            m=re.match(r"press\s+(.+)$",c,re.I)
            if m:add("Press keyboard shortcut","windows.hotkey",{"keys":[x.strip() for x in re.split(r"\+|\s+and\s+",m.group(1),flags=re.I) if x.strip()]});recognized+=1;continue
            m=re.match(r"click\s+(?:at\s+)?(\d+)\s*[, ]\s*(\d+)$",c,re.I)
            if m:add("Click screen","windows.click",{"x":int(m.group(1)),"y":int(m.group(2))});recognized+=1;continue
            m=re.match(r"scroll\s+(up|down)(?:\s+(\d+))?$",c,re.I)
            if m:add("Scroll","windows.scroll",{"amount":(1 if m.group(1).lower()=="up" else -1)*int(m.group(2) or 5)});recognized+=1;continue
            if re.match(r"^(?:scan|discover|find|show)(?:\s+the)?(?:\s+devices)?(?:\s+on)?(?:\s+my)?\s+(?:local network|same network|lan|wifi|wi-fi)(?:\s+devices)?$",low):add("Discover LAN devices","network.discover_lan",{"active":True});recognized+=1;continue
            if re.match(r"^(?:scan|discover|find|show)(?:\s+nearby)?\s+bluetooth(?:\s+devices)?$",low) or low in ("scan nearby devices","discover nearby devices","find nearby devices"):add("Discover Bluetooth devices","network.discover_bluetooth",{});recognized+=1;continue
            if low in ("take screenshot","screenshot"):add("Take screenshot","system.screenshot",{});recognized+=1;continue
            if low in ("volume up","increase volume"):add("Increase volume","windows.volume_up",{});recognized+=1;continue
            if low in ("volume down","decrease volume"):add("Decrease volume","windows.volume_down",{});recognized+=1;continue
            if low in ("mute","mute volume"):add("Toggle mute","windows.mute",{});recognized+=1;continue
            if low in ("play pause","play/pause","pause media","play media"):add("Play or pause media","windows.media_play_pause",{});recognized+=1;continue
            if low in ("next track","next song"):add("Next media track","windows.media_next",{});recognized+=1;continue
            if low in ("previous track","previous song","last track"):add("Previous media track","windows.media_previous",{});recognized+=1;continue
            if low in ("shutdown","shutdown computer","shutdown laptop"):add("Shut down computer","power.shutdown",{});recognized+=1;continue
            if low in ("restart","reboot","restart computer","restart laptop"):add("Restart computer","power.restart",{});recognized+=1;continue
            if low in ("sleep","sleep computer","sleep laptop"):add("Sleep computer","power.sleep",{});recognized+=1;continue
        if steps and recognized==len(clauses):return AgentPlan(str(uuid.uuid4()),request,steps)
        return None

    def plan(self,request,workspace="Infinity OS"):
        simple=self._deterministic_plan(request)
        if simple:return simple
        specs=self.tools.specs();context=self.memory.context(request,workspace,6,7000)
        system="""You are the planner for AEGIS inside Infinity OS. Return ONLY JSON: {\"steps\":[{\"title\":...,\"tool\":...,\"args\":{...}}]}. Use only listed tools. Prefer a few robust steps. Never invent a tool. Do not put destructive or message-sending actions unless the user explicitly requested them."""
        prompt=f"USER REQUEST:\n{request}\n\nTOOLS:\n{json.dumps(specs)}\n\nPROJECT MEMORY:\n{context}"
        r=self.router.ask(prompt,task="coding" if any(x in request.lower() for x in ("code","build","project","git")) else "default",system=system)
        raw=r.get("text","");data=None
        try:
            raw=re.sub(r"^```(?:json)?|```$","",raw.strip(),flags=re.I|re.M).strip();data=json.loads(raw)
        except Exception:data={"steps":[]}
        steps=[]
        for x in data.get("steps",[])[:12]:
            tool=str(x.get("tool",""));spec=self.tools.get(tool)
            if spec:steps.append(AgentStep(str(uuid.uuid4()),str(x.get("title") or tool),tool,x.get("args") or {},spec.permission))
        if not steps:
            steps.append(AgentStep(str(uuid.uuid4()),"Ask AEGIS","aegis.answer",{"prompt":request},""))
        plan=AgentPlan(str(uuid.uuid4()),request,steps)
        if self.bus:self.bus.emit("agent.plan",asdict(plan))
        return plan

    def _authorize(self,spec,step,confirmed_permissions=None):
        if not spec.permission:return True
        if confirmed_permissions and spec.permission in confirmed_permissions:return True
        decision=self.security.decision(spec.permission)
        if decision=="allow":return True
        if decision=="deny":return False
        if self.confirm_callback:
            result=self.confirm_callback(spec.permission,step.title,step.args)
            if result=="session":self.security.grant_session(spec.permission);return True
            return bool(result)
        return False

    def execute(self,plan,retries=1,confirmed_permissions=None):
        plan.status="running";results=[]
        for step in plan.steps:
            spec=self.tools.get(step.tool)
            if not spec:step.status="failed";step.result={"ok":False,"message":"Tool missing"};results.append(step.result);break
            if not self._authorize(spec,step,confirmed_permissions):step.status="denied";step.result={"ok":False,"message":"Permission denied: "+spec.permission};results.append(step.result);break
            step.status="running";self.security.audit("agent.tool_start",{"tool":step.tool,"args":step.args,"plan":plan.id})
            attempt=0;result=None
            while attempt<=retries:
                result=self.tools.call(step.tool,step.args);attempt+=1
                if result.ok or not result.retryable:break
                time.sleep(.5)
            step.result={"ok":result.ok,"message":result.message,"data":result.data};step.status="done" if result.ok else "failed";results.append(step.result)
            self.security.audit("agent.tool_end",{"tool":step.tool,"ok":result.ok,"message":result.message,"plan":plan.id})
            if self.bus:self.bus.emit("agent.step",{"plan":plan.id,"step":asdict(step)})
            if not result.ok:break
        plan.status="done" if all(r.get("ok") for r in results) else "stopped"
        if self.notifications:self.notifications.push("AEGIS task "+plan.status,"; ".join(r.get("message","") for r in results[-3:]),"success" if plan.status=="done" else "warning","AEGIS")
        if self.bus:self.bus.emit("agent.finished",{"plan":asdict(plan),"results":results})
        return results
