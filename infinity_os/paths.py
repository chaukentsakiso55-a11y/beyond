from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CONFIG = ROOT / "config"
LOGS = DATA / "logs"
SHARE = DATA / "remote_share"
BACKUPS = DATA / "backups"
for p in (DATA, CONFIG, LOGS, SHARE, BACKUPS):
    p.mkdir(parents=True, exist_ok=True)
