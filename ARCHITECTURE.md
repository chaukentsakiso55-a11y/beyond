# Architecture

                              Native PySide6 Desktop
                                      │
                                 Infinity Core
         ┌───────────────┬────────────┼─────────────┬─────────────────┐
         ▼               ▼            ▼             ▼                 ▼
      Event Bus       AEGIS        Router 2      Memory 2        Security
                         │             │             │                 │
             ┌───────────┼───────┐     │             │                 │
             ▼           ▼       ▼     ▼             ▼                 ▼
         Windows      Browser   Forge  Model Arena  Workflows       Audit
         Control       Agent     2.0
             │
        Device Mesh ─────── Phone Companion (web on phone only)

Plugin/MCP tools register into AEGIS through capability manifests. AEGIS never calls desktop or browser actions directly; it calls permission-gated tool adapters.
