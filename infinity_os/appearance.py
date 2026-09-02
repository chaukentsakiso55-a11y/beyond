import json
from .paths import CONFIG

PRESETS={
 'Infinity Neon':{'bg':'#050811','panel':'#09111f','card':'#101d30','border':'#18344e','text':'#edfaff','muted':'#7896aa','accent':'#46e6ff','accent2':'#a477ff','good':'#55efb3','warn':'#ffd86b','bad':'#ff6b86'},
 'Liquid Violet':{'bg':'#080610','panel':'#100c19','card':'#211735','border':'#3d2d58','text':'#fbf6ff','muted':'#a694b8','accent':'#b78cff','accent2':'#ff75d8','good':'#68efbd','warn':'#ffd66f','bad':'#ff718e'},
 'Cyber Blue':{'bg':'#020810','panel':'#061320','card':'#0c2740','border':'#14547c','text':'#effbff','muted':'#7faabe','accent':'#31cfff','accent2':'#5779ff','good':'#4de7ad','warn':'#ffd064','bad':'#ff647e'},
 'Emerald Matrix':{'bg':'#030908','panel':'#071411','card':'#0d2a21','border':'#18583e','text':'#ecfff7','muted':'#80ae99','accent':'#45f0a8','accent2':'#5ed9ff','good':'#55efb3','warn':'#f1d56c','bad':'#ff7288'},
 'Crimson Core':{'bg':'#0b0508','panel':'#16090e','card':'#32121d','border':'#68243a','text':'#fff3f6','muted':'#bd909c','accent':'#ff5475','accent2':'#ff995f','good':'#5be9ac','warn':'#ffd46b','bad':'#ff5475'},
 'OLED Black':{'bg':'#000000','panel':'#050505','card':'#101010','border':'#262626','text':'#ffffff','muted':'#999999','accent':'#ffffff','accent2':'#aaaaaa','good':'#62e7a9','warn':'#f0d36c','bad':'#ff6d82'}
}
DEFAULT={'preset':'Infinity Neon','accent':'','background':'','panel':'','card':'','density':'comfortable','sidebar':'standard','font_scale':1.0,'effects':'glass'}

class AppearanceManager:
    def __init__(self):self.path=CONFIG/'appearance.json';self.settings=self.load()
    def load(self):
        try:return {**DEFAULT,**json.loads(self.path.read_text(encoding='utf-8'))}
        except Exception:return dict(DEFAULT)
    def save(self,data):self.settings={**DEFAULT,**data};self.path.write_text(json.dumps(self.settings,indent=2),encoding='utf-8')
    def palette(self):
        p=dict(PRESETS.get(self.settings.get('preset'),PRESETS['Infinity Neon']))
        for key,setting in [('accent','accent'),('bg','background'),('panel','panel'),('card','card')]:
            if self.settings.get(setting):p[key]=self.settings[setting]
        return p
    def qss(self):
        p=self.palette();scale=float(self.settings.get('font_scale',1.0));font=max(11,round(13*scale));radius={'compact':8,'comfortable':12,'spacious':16}.get(self.settings.get('density','comfortable'),12);effects=self.settings.get('effects','glass').lower();card=p['card'];border=p['accent'] if effects=='glow' else p['border'];panel=p['panel']
        if effects=='minimal':radius=max(4,radius-5)
        return f"""QWidget{{background:{p['bg']};color:{p['text']};font-family:'Segoe UI';font-size:{font}px}}
QFrame#Sidebar{{background:{panel};border-right:1px solid {p['border']}}}
QFrame#Card{{background:{card};border:1px solid {border};border-radius:{radius}px}}
QPushButton{{background:{card};border:1px solid {p['border']};border-radius:{max(4,radius-2)}px;padding:9px 12px}}
QPushButton:hover{{border-color:{p['accent']};color:{p['accent']}}}
QPushButton#Primary{{background:{p['accent']};color:#051017;font-weight:700;border:none}}
QPushButton#Danger{{color:{p['bad']}}}
QLineEdit,QPlainTextEdit,QTextEdit,QComboBox,QSpinBox{{background:{card};border:1px solid {p['border']};border-radius:{max(4,radius-2)}px;padding:8px;selection-background-color:{p['accent']};selection-color:#061017}}
QListWidget,QTreeWidget,QTableWidget{{background:{panel};border:1px solid {p['border']};border-radius:{radius}px;alternate-background-color:{card}}}
QHeaderView::section{{background:{card};color:{p['accent']};padding:8px;border:0;border-bottom:1px solid {p['border']}}}
QTabWidget::pane{{border:1px solid {p['border']};border-radius:{radius}px}}
QTabBar::tab{{background:{panel};padding:10px 14px;border:1px solid {p['border']}}}
QTabBar::tab:selected{{color:{p['accent']};background:{card}}}
QProgressBar{{border:1px solid {p['border']};border-radius:7px;background:{panel};text-align:center}}
QProgressBar::chunk{{background:{p['accent']};border-radius:6px}}
QScrollBar:vertical{{background:{panel};width:10px}}
QScrollBar::handle:vertical{{background:{p['border']};border-radius:5px;min-height:28px}}"""
