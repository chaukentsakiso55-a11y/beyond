import sys, traceback
from .diagnostics import Diagnostics

def launch():
    diagnostics=Diagnostics()
    try:
        from PySide6.QtWidgets import QApplication,QMessageBox
        from PySide6.QtGui import QIcon
        from .paths import ROOT
    except Exception:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root=tk.Tk();root.withdraw();messagebox.showerror('Infinity OS','PySide6 is not installed.\n\nDouble-click RUN-INFINITY.bat to install the required packages and open Infinity.');root.destroy()
        except Exception:print('PySide6 is not installed. Double-click RUN-INFINITY.bat.')
        return
    app=QApplication(sys.argv);app.setApplicationName('Infinity OS');app.setOrganizationName('Cyber Pulse');icon=ROOT/'assets'/'infinity.ico';app.setWindowIcon(QIcon(str(icon))) if icon.exists() else None
    try:
        from .core import InfinityCore
        core=InfinityCore();app.setStyleSheet(core.appearance.qss());report=core.start()
        from .ui.main_window import MainWindow
        win=MainWindow(core);win.show();sys.exit(app.exec())
    except Exception as exc:
        diagnostics.record_crash(exc);QMessageBox.critical(None,'Infinity OS Startup Error',f'{exc}\n\nA crash report was saved to data/last_crash.txt.');raise
