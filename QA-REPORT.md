# QA Report

Validation performed before packaging:

- Python `compileall` over the full project
- Non-GUI `InfinityCore` construction/shutdown smoke tests
- Offline natural-language command planning tests
- Memory 2.0 round-trip search test
- Core status/native-fallback test
- Authenticated QR/PIN remote-server status test
- Phone command confirmation-policy test
- Workflow dependency execution test
- Router Model Arena feedback persistence test
- Tool schema introspection test
- ZIP integrity test during final packaging

## Environment limitation

The build environment used for packaging does not have PySide6 or pywinauto installed. Their source is syntax-validated, and the Windows installer declares them as required dependencies, but the actual Qt window and Windows UI Automation backend cannot be launched in this Linux packaging environment. Core services and remote HTTP behavior are tested independently.

Playwright is present in the packaging environment, but a browser executable is not assumed; `INSTALL-BROWSER.bat` installs Chromium on the target Windows laptop.
