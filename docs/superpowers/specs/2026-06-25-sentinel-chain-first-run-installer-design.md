# Sentinel Chain first-run installer design

Date: 2026-06-25

## Goal

Windows beta testers should install Sentinel Chain from `SentinelChain-Setup-<version>.exe`, double-click the installed shortcut, and have missing runtime dependencies handled automatically on first launch.

## Design

- Keep the existing source launcher for developers and the workstation suite.
- Add an installed-package branch to `Launch-Sentinel Chain.ps1` when `SentinelChain.exe` exists beside the launcher.
- The installed launcher checks/downloads the Microsoft Visual C++ Runtime, starts the packaged API with local paper-mode SQLite storage, waits for `/health`, and opens `/ui`.
- Preserve the optional Discord process in installed mode by allowing the packaged entrypoint to run either the API server or the Discord bot from the same executable.
- Add a GitHub Actions Windows workflow that packages the Python app, bundled operator UI static assets, and launcher pair into `SentinelChain-Setup-<version>.exe` with Inno Setup.

## Non-goals

- No live exchange activation by default; the installer keeps paper-only startup.
- No separate Node.js frontend dependency; Sentinel Chain already serves static UI from the Python package.
- No macOS installer redesign.
