import sys,time
from PySide6.QtCore import Qt,QTimer,QPropertyAnimation,QEasingCurve,QThreadPool,Signal
from PySide6.QtWidgets import QMainWindow,QWidget,QHBoxLayout,QVBoxLayout,QFrame,QLabel,QPushButton,QStackedWidget,QLineEdit,QMessageBox,QGraphicsOpacityEffect
from .widgets import Worker
from .pages.core_pages import DashboardPage,AegisPage,AiNexusPage,MemoryPage,SystemPage
from .pages.advanced_pages import ForgePage,StudyPage,WorkflowsPage,ControlPage,PluginsPage,SecurityPage,NotificationsPage,SettingsPage,MeshPage,BrowserPage

class MainWindow(QMainWindow):
    voice_command=Signal(str)
    NAV=[('Dashboard','◈'),('AEGIS','✦'),('AI Nexus','◎'),('Browser','◌'),('Memory','◫'),('System','▥'),('Forge','⌘'),('Study','◷'),('Workflows','◇'),('Control','⌁'),('Mesh','◉'),('Plugins','⬢'),('Security','⬡'),('Notifications','●'),('Settings','⚙')]
    def __init__(self,core):
        super().__init__();self.core=core;self.pool=QThreadPool.globalInstance();self.voice_command.connect(self.run_command);self.setWindowTitle('Infinity OS V7 REBORN — Ultimate');self.resize(1500,920);self.setMinimumSize(1180,720);self.pages={};self.nav={};self._build();self.open_page('Dashboard');self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(1000);self.core.bus.on('notification.created',lambda n:QTimer.singleShot(0,self.update_notification_badge))
        if self.core.voice.config.get('enabled') and not self.core.diagnostics.safe_mode():
            self.core.voice.start_wake_listener(lambda cmd:self.voice_command.emit(cmd))
    def _build(self):
        central=QWidget();self.setCentralWidget(central);root=QHBoxLayout(central);root.setContentsMargins(0,0,0,0);root.setSpacing(0)
        self.sidebar=QFrame();self.sidebar.setObjectName('Sidebar');width={'compact':190,'standard':230,'wide':280}.get(self.core.appearance.settings.get('sidebar','standard'),230);self.sidebar.setFixedWidth(width);sl=QVBoxLayout(self.sidebar);sl.setContentsMargins(12,18,12,14);brand=QHBoxLayout();logo=QLabel('∞');logo.setStyleSheet('font-size:36px;color:#46e6ff;font-weight:900');names=QVBoxLayout();n=QLabel('INFINITY OS');n.setStyleSheet('font-size:15px;font-weight:900');v=QLabel('V7 REBORN · ULTIMATE');v.setStyleSheet('color:#a477ff;font-size:9px;font-weight:800');names.addWidget(n);names.addWidget(v);brand.addWidget(logo);brand.addLayout(names,1);sl.addLayout(brand);sl.addSpacing(14)
        for name,icon in self.NAV:
            b=QPushButton(f'{icon}   {name}');b.setCheckable(True);b.setStyleSheet('text-align:left;padding:10px');b.clicked.connect(lambda _,x=name:self.open_page(x));sl.addWidget(b);self.nav[name]=b
        sl.addStretch();self.core_state=QLabel('● INFINITY CORE ONLINE');self.core_state.setStyleSheet('color:#55efb3;font-size:10px;font-weight:800');sl.addWidget(self.core_state);self.badge=QLabel('0 unread');self.badge.setStyleSheet('color:#7896aa;font-size:10px');sl.addWidget(self.badge);root.addWidget(self.sidebar)
        main=QWidget();ml=QVBoxLayout(main);ml.setContentsMargins(22,14,22,18);top=QHBoxLayout();self.page_title=QLabel('Dashboard');self.page_title.setStyleSheet('font-size:22px;font-weight:850');self.command=QLineEdit();self.command.setPlaceholderText('Ask AEGIS or command Infinity…  e.g. open Chrome, search for Qt docs');self.command.returnPressed.connect(self.palette);self.clock=QLabel();self.clock.setStyleSheet('color:#7896aa');top.addWidget(self.page_title);top.addSpacing(30);top.addWidget(self.command,1);top.addWidget(self.clock);ml.addLayout(top);self.stack=QStackedWidget();ml.addWidget(self.stack,1);root.addWidget(main,1)
        classes={'Dashboard':DashboardPage,'AEGIS':AegisPage,'AI Nexus':AiNexusPage,'Browser':BrowserPage,'Memory':MemoryPage,'System':SystemPage,'Forge':ForgePage,'Study':StudyPage,'Workflows':WorkflowsPage,'Control':ControlPage,'Mesh':MeshPage,'Plugins':PluginsPage,'Security':SecurityPage,'Notifications':NotificationsPage,'Settings':SettingsPage}
        for name,_ in self.NAV:
            page=classes[name](self.core);self.pages[name]=page;self.stack.addWidget(page)
        self.update_notification_badge()
    def open_page(self,name):
        if name not in self.pages:return
        self.stack.setCurrentWidget(self.pages[name]);self.page_title.setText(name)
        for n,b in self.nav.items():b.setChecked(n==name)
        effect=QGraphicsOpacityEffect(self.stack.currentWidget());self.stack.currentWidget().setGraphicsEffect(effect);anim=QPropertyAnimation(effect,b'opacity',self);anim.setDuration(180);anim.setStartValue(.35);anim.setEndValue(1.0);anim.setEasingCurve(QEasingCurve.OutCubic);anim.finished.connect(lambda:self.stack.currentWidget().setGraphicsEffect(None));anim.start();self._anim=anim
        if name=='AI Nexus':self.pages[name].refresh()
        if name=='AEGIS':self.pages[name].refresh_providers();self.pages[name].refresh_chats()
        if name=='Memory':self.pages[name].search()
        if name=='Notifications':self.pages[name].refresh()
        if name=='Security':self.pages[name].refresh()
    def palette(self):
        text=self.command.text().strip();self.command.clear();
        if not text:return
        low=text.lower();aliases={'dashboard':'Dashboard','aegis':'AEGIS','ai nexus':'AI Nexus','browser':'Browser','memory':'Memory','system':'System','forge':'Forge','study':'Study','workflows':'Workflows','control':'Control','mesh':'Mesh','plugins':'Plugins','security':'Security','notifications':'Notifications','settings':'Settings'}
        for k,v in aliases.items():
            if low in (k,'open '+k,'go to '+k):self.open_page(v);return
        if low.startswith(('open ','launch ','start ','search ','google ','send ','message ','press ','click ','scroll ','type ','take screenshot','volume ','mute')):self.run_command(text);return
        self.open_page('AEGIS');self.pages['AEGIS'].input.setPlainText(text);self.pages['AEGIS'].send()
    def run_command(self,text):
        self.open_page('Control');self.pages['Control'].cmd.setPlainText(text);self.pages['Control'].execute()
    def tick(self):
        self.clock.setText(time.strftime('%a %d %b  ·  %H:%M:%S'));self.update_notification_badge()
    def update_notification_badge(self):self.badge.setText(f"{self.core.notifications.unread_count()} unread")
    def closeEvent(self,event):
        self.core.shutdown();event.accept()
