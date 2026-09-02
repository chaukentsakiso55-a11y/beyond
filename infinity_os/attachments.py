from pathlib import Path
import shutil,uuid,mimetypes
from .paths import DATA
class AttachmentManager:
    TEXT={'.txt','.md','.py','.js','.ts','.tsx','.jsx','.java','.kt','.kts','.c','.cpp','.h','.hpp','.rs','.go','.rb','.php','.html','.css','.scss','.json','.xml','.yaml','.yml','.toml','.ini','.cfg','.log','.csv','.sql','.sh','.bat','.ps1','.gradle','.properties'}
    def __init__(self):self.base=DATA/'chat_uploads';self.base.mkdir(exist_ok=True)
    def import_file(self,path,chat_id):
        src=Path(path);folder=self.base/chat_id;folder.mkdir(exist_ok=True);target=folder/(uuid.uuid4().hex[:8]+'_'+src.name);shutil.copy2(src,target)
        meta={'name':src.name,'path':str(target),'size':target.stat().st_size,'mime':mimetypes.guess_type(src.name)[0] or 'application/octet-stream','text':''}
        ext=target.suffix.lower()
        if ext in self.TEXT:meta['text']=target.read_text(encoding='utf-8',errors='replace')[:500000]
        elif ext=='.pdf':
            try:
                from pypdf import PdfReader
                meta['text']='\n'.join((p.extract_text() or '') for p in PdfReader(str(target)).pages)[:500000]
            except Exception:meta['text']='[PDF extraction unavailable]'
        elif ext=='.docx':
            try:
                from docx import Document
                meta['text']='\n'.join(p.text for p in Document(str(target)).paragraphs)[:500000]
            except Exception:meta['text']='[DOCX extraction unavailable]'
        return meta
    def context(self,items):return '\n'.join(f"--- {x['name']} ---\n{x.get('text','')}" for x in items if x.get('text'))[:120000]
