from pathlib import Path
import json, shutil, time, urllib.request, zipfile, os
from .paths import ROOT, BACKUPS, CONFIG

class UpdateManager:
    def __init__(self,repo=None):
        if repo:self.repo=repo
        else:
            try:self.repo=json.loads((CONFIG/"update.json").read_text(encoding="utf-8")).get("github_repo","")
            except Exception:self.repo=""
        self.meta=BACKUPS/"backup_index.json"
    def check(self):
        if not self.repo:raise RuntimeError("Set github_repo in config/update.json")
        url=f"https://api.github.com/repos/{self.repo}/releases/latest"
        req=urllib.request.Request(url,headers={"Accept":"application/vnd.github+json","User-Agent":"InfinityOS"})
        with urllib.request.urlopen(req,timeout=15) as r:data=json.loads(r.read().decode())
        return {"tag":data.get("tag_name"),"name":data.get("name"),"body":data.get("body","")[:12000],"url":data.get("html_url")}
    def backup(self,label=None):
        stamp=time.strftime("%Y%m%d-%H%M%S");dest=BACKUPS/(label or stamp);dest.mkdir(parents=True,exist_ok=True)
        include=["infinity_os","config","plugins","README.md","ARCHITECTURE.md","main.py"]
        for name in include:
            src=ROOT/name
            if not src.exists():continue
            if src.is_dir():shutil.copytree(src,dest/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns("providers.json","secrets.json","__pycache__","*.pyc"))
            else:shutil.copy2(src,dest/name)
        return str(dest)
    def latest_backup(self):
        rows=[p for p in BACKUPS.iterdir() if p.is_dir()]
        return str(max(rows,key=lambda p:p.stat().st_mtime)) if rows else ''
    def rollback(self,backup_path):
        src=Path(backup_path)
        if not src.exists():raise FileNotFoundError(src)
        for p in src.iterdir():
            dest=ROOT/p.name
            if p.is_dir():shutil.copytree(p,dest,dirs_exist_ok=True)
            else:shutil.copy2(p,dest)
        return True
