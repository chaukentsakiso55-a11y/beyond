from pathlib import Path
import json, subprocess, shutil, time
from .paths import DATA

class Forge2:
    def __init__(self,security):self.security=security;self.locks_path=DATA/"architecture_locks.json";self.locks=self._load_locks()
    def _load_locks(self):
        try:return json.loads(self.locks_path.read_text(encoding="utf-8"))
        except Exception:return {}
    def save_locks(self):self.locks_path.write_text(json.dumps(self.locks,indent=2),encoding="utf-8")
    def set_lock(self,project,patterns):self.locks[str(Path(project).resolve())]=patterns;self.save_locks()
    def is_locked(self,project,path):
        root=str(Path(project).resolve());rel=str(Path(path).resolve().relative_to(Path(project).resolve())).replace("\\","/")
        patterns=self.locks.get(root,[])
        import fnmatch
        return any(fnmatch.fnmatch(rel,p) for p in patterns)
    def tree(self,project,max_items=1500):
        root=Path(project);rows=[]
        for p in root.rglob("*"):
            if any(x in p.parts for x in (".git",".venv","node_modules","build","dist","__pycache__")):continue
            try:rows.append({"path":str(p.relative_to(root)),"dir":p.is_dir(),"size":0 if p.is_dir() else p.stat().st_size})
            except Exception:pass
            if len(rows)>=max_items:break
        return rows
    def read(self,path,max_chars=500000):return Path(path).read_text(encoding="utf-8",errors="replace")[:max_chars]
    def write(self,project,path,content):
        target=Path(path)
        if self.is_locked(project,target):raise PermissionError("Architecture lock protects "+str(target))
        target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content,encoding="utf-8")
    def run(self,project,command,timeout=180):
        p=subprocess.run(command,cwd=str(project),shell=True,capture_output=True,text=True,timeout=timeout);return {"code":p.returncode,"stdout":p.stdout[-30000:],"stderr":p.stderr[-30000:]}
    def git_status(self,project):return self.run(project,"git status --short",30)
    def git_diff(self,project):return self.run(project,"git diff -- .",30)
    def test(self,project):
        root=Path(project)
        if (root/"pytest.ini").exists() or list(root.glob("test*.py")) or (root/"tests").exists():return self.run(project,"python -m pytest -q",180)
        if (root/"package.json").exists():return self.run(project,"npm test -- --runInBand",180)
        if (root/"gradlew.bat").exists():return self.run(project,"gradlew.bat test",300)
        return {"code":0,"stdout":"No recognized automated test command found.","stderr":""}
