from PySide6.QtCore import QObject, Signal, QRunnable, Slot, Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget

class WorkerSignals(QObject):
    result=Signal(object); error=Signal(str); finished=Signal()

class Worker(QRunnable):
    def __init__(self,fn,*args,**kwargs):
        super().__init__();self.fn=fn;self.args=args;self.kwargs=kwargs;self.signals=WorkerSignals()
    @Slot()
    def run(self):
        try:self.signals.result.emit(self.fn(*self.args,**self.kwargs))
        except Exception as exc:self.signals.error.emit(str(exc))
        finally:self.signals.finished.emit()

class Card(QFrame):
    def __init__(self,parent=None):super().__init__(parent);self.setObjectName('Card')

class StatCard(Card):
    def __init__(self,title,value='--',subtitle=''):
        super().__init__();lay=QVBoxLayout(self);lay.setContentsMargins(15,13,15,13);self.title=QLabel(title.upper());self.title.setStyleSheet('color:#7896aa;font-size:10px;font-weight:700;letter-spacing:1px');self.value=QLabel(value);self.value.setStyleSheet('font-size:24px;font-weight:800');self.subtitle=QLabel(subtitle);self.subtitle.setStyleSheet('color:#7896aa;font-size:11px');lay.addWidget(self.title);lay.addWidget(self.value);lay.addWidget(self.subtitle)

class SectionHeader(QWidget):
    def __init__(self,title,subtitle=''):
        super().__init__();lay=QVBoxLayout(self);lay.setContentsMargins(0,0,0,8);t=QLabel(title);t.setStyleSheet('font-size:22px;font-weight:800');lay.addWidget(t)
        if subtitle:
            s=QLabel(subtitle);s.setWordWrap(True);s.setStyleSheet('color:#7896aa');lay.addWidget(s)

class Sparkline(QWidget):
    def __init__(self,max_points=50,parent=None):super().__init__(parent);self.values=[];self.max_points=max_points;self.setMinimumHeight(54)
    def add(self,value):self.values=(self.values+[float(value)])[-self.max_points:];self.update()
    def paintEvent(self,event):
        if len(self.values)<2:return
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);pen=QPen(QColor('#46e6ff'));pen.setWidthF(2.0);p.setPen(pen);r=self.rect().adjusted(4,4,-4,-4);lo=min(self.values);hi=max(self.values);span=max(1e-6,hi-lo);pts=[]
        for i,v in enumerate(self.values):
            x=r.left()+r.width()*i/(len(self.values)-1);y=r.bottom()-r.height()*(v-lo)/span;pts.append((x,y))
        for a,b in zip(pts,pts[1:]):p.drawLine(a[0],a[1],b[0],b[1])

class MessageBubble(Card):
    def __init__(self,role,text,meta=''):
        super().__init__();lay=QVBoxLayout(self);lay.setContentsMargins(12,10,12,10);name=QLabel('YOU' if role=='user' else (meta or 'AEGIS'));name.setStyleSheet('color:#46e6ff;font-size:10px;font-weight:800' if role=='user' else 'color:#a477ff;font-size:10px;font-weight:800');body=QLabel(text);body.setWordWrap(True);body.setTextInteractionFlags(Qt.TextSelectableByMouse);lay.addWidget(name);lay.addWidget(body)
