# Infinity OS V7 REBORN — Ultimate Architecture

Infinity OS remains a native Windows desktop application. The browser surface is only the paired phone companion.

## Major systems

- Native PySide6/Qt desktop shell with theme studio
- AEGIS Agent Engine with plans, tool calls, retries, confirmations and audit history
- Windows UI Automation using pywinauto when available, with pyautogui fallback
- Browser Agent using Playwright
- AI Router 2.0: unlimited providers/models, health, latency, failover, routing policies, usage stats
- Model Arena for side-by-side multi-model evaluation
- Project Memory 2.0 backed by SQLite + FTS + lightweight semantic ranking
- Visual/JSON workflow engine with schedules and step dependencies
- Phone Companion 2.0 with QR pairing, AEGIS sync, system status, running apps, notifications, files, clipboard and controls
- Plugin + MCP registry with declared permissions
- Developer Forge 2.0 with project tree, editor, terminal, Git, tests/build actions and architecture locks
- Security Center with Always Allow / Ask / Session / Deny
- Voice AEGIS with configurable wake words and TTS
- Notification Center
- Startup diagnostics, Safe Mode and recovery reports
- GitHub release update/backup/rollback foundation
- Device Mesh capability registry and task assignment
- Safe Nearby Device Discovery: private-LAN discovery from the Mesh screen plus present/known Windows Bluetooth devices; no port scanning, credential testing, or public-network probing
- Rust/C++ native extension stubs retained for future hotspots
- No Firebase dependency on desktop

## First installation on Windows

Double-click:

    INSTALL-INFINITY.bat

The installer creates `.venv`, installs the Python dependencies, and creates a desktop shortcut named **Infinity OS V7 REBORN**. After that you can launch Infinity from the desktop icon.

If the shortcut is ever missing, moved, or deleted, double-click:

    CREATE-DESKTOP-SHORTCUT.bat

You can also launch directly with:

    START-INFINITY-OS.bat

If Playwright browser automation is wanted, run:

    INSTALL-BROWSER.bat

## Security model

Infinity is deliberately powerful, but local control is permission gated and audited. Actions that send messages, change files, execute commands, control applications, use the camera/microphone, or change computer power can be configured as:

- always_allow
- ask
- session
- deny

Infinity does not bypass Windows UAC, passwords, lock screens, administrator controls or OS security boundaries.

## Phone companion

Infinity Desktop stays native. The phone opens a companion dashboard on the same trusted LAN after QR/PIN pairing. Closing Infinity Desktop stops the phone server.

## Simple AI provider setup

AI Nexus now supports a simplified provider flow. For recognized cloud providers, enter only a display name and API key. Infinity automatically identifies the provider, fills the API endpoint, and discovers available models when the provider is first checked or used.

Recognized providers include OpenAI, Google Gemini, Anthropic Claude, OpenRouter, Groq, Mistral, xAI/Grok, DeepSeek, Perplexity, Together AI, Fireworks AI, Cerebras, NVIDIA NIM, SambaNova, Hugging Face, and Moonshot/Kimi.

Use **Advanced settings** only for local servers or custom OpenAI-compatible endpoints. The base URL field now rejects malformed values such as pasted cURL commands.

## Nearby device discovery

Open **Mesh** and use **Scan Same Network** to discover devices on the private IPv4 LAN that the laptop is already connected to. Infinity limits an active discovery action to the local /24 segment (up to 254 addresses) and combines ping presence with the Windows neighbor/ARP table. It does **not** scan ports, test credentials, or probe public Internet ranges. Use it only on networks you own or have permission to scan.

Use **Nearby Bluetooth** to list Bluetooth devices that Windows currently reports as present/known. This is not an attempt to bypass pairing or access another device. Both actions are controlled by the `network.discovery` Security Center permission, which defaults to **Ask**.

AEGIS can also use the permission-gated tools `network.discover_lan` and `network.discover_bluetooth`.

## Python requirements

`requirements.txt` is the authoritative complete Python dependency list for this build. `RUN-INFINITY.bat` installs the core dependencies first and then the full feature set from the staged requirements files. You can also install everything manually with:

    python -m pip install -r requirements.txt

The Playwright Python package is included in `requirements.txt`; its Chromium browser runtime is downloaded separately by running `INSTALL-BROWSER.bat` once. PyAudio is not required because voice input has a `sounddevice` + NumPy fallback. Use `CHECK-REQUIREMENTS.bat` to report missing Python libraries.
