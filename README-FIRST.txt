INFINITY OS V7 REBORN — QUICK START
====================================

1. EXTRACT this ZIP to a normal folder first.
2. Double-click RUN-INFINITY.bat.
3. On the first run it creates .venv and installs the desktop dependencies.
4. It creates the "Infinity OS V7 REBORN" Desktop shortcut.
5. It automatically runs main.py and opens Infinity OS.

You can also use INSTALL-INFINITY.bat or START-INFINITY-OS.bat. Both now call the same reliable launcher.

MANUAL COMMAND
--------------
If you already have the required Python packages installed, the direct command is:

    python main.py

If Infinity was prepared by RUN-INFINITY.bat, the exact private-environment command is:

    .venv\Scripts\python.exe main.py

BROWSER AUTOMATION
------------------
Infinity itself does not need Playwright just to open. If you want the Browser Agent, run INSTALL-BROWSER.bat after Infinity is working.

TROUBLESHOOTING
---------------
The launcher keeps a log here:

    data\logs\launcher.log

If installation fails, send the final lines of that file.

VOICE + GEMINI FIX NOTE
- Gemini model IDs returned as models/gemini-... are normalized automatically to gemini-... before Chat Completions.
- When the first cloud AI provider is added, Infinity makes it the default Answer-mode route instead of leaving the placeholder Local route selected.
- Voice input no longer depends only on PyAudio. Infinity first tries PyAudio and then falls back to sounddevice + NumPy, which RUN-INFINITY.bat installs automatically.
