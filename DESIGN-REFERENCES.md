# Architecture references from the GitHub scout

Infinity's implementation is original, but the scout informed several subsystem choices:

- `microsoft/UFO` — strong reference for separating a Windows device agent from higher-level orchestration, hybrid GUI/UI Automation, and future multi-device task assignment.
- `pywinauto/pywinauto` — Windows UI Automation backend used by Infinity when installed.
- `BerriAI/litellm` — architectural reference for the idea of routing many model providers behind one AI layer; Infinity's Router 2.0 is its own small local implementation.
- `open-webui/open-webui` — product reference for multi-provider chat/model UX; Infinity remains a native PySide6 desktop application.
- `openinterpreter/openinterpreter` — reference for natural-language computer/tool workflows; Infinity uses its own permission-gated Agent Engine.

No repository was copied wholesale into Infinity OS. Narrow ideas were adapted to Infinity Core's architecture so the project remains understandable and maintainable.
