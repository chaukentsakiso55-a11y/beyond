# Infinity OS Ultimate Feature Matrix

| Area | Implemented | Notes |
|---|---|---|
| Native UI | PySide6/Qt shell, sidebar, page animation, theme QSS | PySide6 installed by `INSTALL-INFINITY.bat` |
| Appearance Studio | 6 presets, custom accent/background/panel/card, density, sidebar width, font scale, Minimal/Glass/Glow modes | Sidebar width applies after restart |
| AEGIS Live | Persistent chats, provider/model selection, attachments, voice, Project Memory, Agent Mode | AI replies require a configured provider/local endpoint |
| Agent Engine | Tool planning, offline common-command parser, permission tags, plan preview, retries, audit | Advanced free-form planning uses configured AI |
| Windows Control | App open/close, focus, named-control UIA click, typing, hotkeys, clicks, scrolling, volume, screenshots, URLs | `pywinauto` preferred; `pyautogui` fallback |
| Browser Agent | Playwright navigate/read/click/fill/press/screenshot | Chromium installed by `INSTALL-BROWSER.bat` |
| AI Router 2.0 | Unlimited providers/models, routing, priority, failover, health probes, latency stats, token/cost stats | OpenAI-compatible endpoint adapter |
| Model Arena | Parallel provider comparison, latency display, quality feedback | Feedback influences later routing scores |
| Memory 2.0 | SQLite, FTS5, lightweight semantic ranking, document indexing, workspace context, chat summaries | Local storage only |
| Workflows | Prompt-to-workflow, dependency/DAG steps, schedules, visual graph, history | Scheduled steps require pre-allowed permissions |
| Phone Companion | QR/PIN auth, status, AEGIS sync, commands, confirmations, files, clipboard, notifications, running apps, focus quick control | Phone web UI only; desktop remains native |
| Plugins | Manifest-based Python plugins | Disabled example included |
| MCP | stdio JSON-RPC initialize, tools/list, tools/call, registration into AEGIS | Server command configured locally |
| Forge 2.0 | Project tree, multi-file tabs, terminal, Git status/diff, tests, AEGIS review, architecture locks | Writes/commands security-gated |
| Security | always_allow / ask / session / deny, session grants, action audit | Power actions denied by default |
| Voice AEGIS | TTS, push-to-talk STT, configurable wake words | Microphone backend required for STT |
| Notifications | Persistent unified notification timeline | Local only |
| Recovery | Diagnostics, missing dependency/provider checks, Safe Mode, crash report | Safe Mode disables plugins/schedules/wake listener |
| Performance | Background telemetry, background router probes, worker threads, optional Rust/C++ bridge | Native DLLs optional |
| Update Manager | GitHub release check, local backup, rollback | Release check needs repo to be reachable |
| Device Mesh | Capability registry, paired phone registration, device selection | First-stage mesh; cross-device executor protocol can expand later |
| Study/Focus | Core focus service, desktop timer, phone quick start, memory reflection | Not a replacement for StudyLock |

## Deliberate boundaries

Infinity does not bypass Windows UAC, passwords, administrator policy, device lock screens or application security. Browser/mobile limitations can also prevent some PWA or Wake-on-LAN behavior from a normal local-network web page.

- **Nearby Device Discovery** — Mesh screen can discover devices on the connected private LAN (capped local segment, no port scan) and list present/known Bluetooth devices on Windows. Permission: `network.discovery`.
