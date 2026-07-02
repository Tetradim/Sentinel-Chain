# Sentinel Chain First-Run Installer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an installed Windows launcher and setup artifact that repair missing runtime dependencies on first launch.

**Architecture:** Source checkouts continue through the current virtual environment launcher. Installed packages are detected by `SentinelChain.exe`; that path repairs VC++ runtime, sets paper-mode local environment variables, starts the packaged API, and optionally starts the packaged Discord process.

**Tech Stack:** PowerShell, FastAPI, PyInstaller, Inno Setup, pytest static checks.

---

### Task 1: Static tests

**Files:**
- Create: `tests/test_windows_installer_bootstrap_static.py`

- [ ] Add tests covering installed/source launcher detection, VC++ runtime repair, packaged entrypoint modes, workflow packaging, and README tester instructions.
- [ ] Run `python -m pytest tests/test_windows_installer_bootstrap_static.py -q` and confirm it fails before implementation.

### Task 2: Packaged entrypoint

**Files:**
- Create: `windows_entrypoint.py`

- [ ] Load `.env` from the install directory.
- [ ] Start the API server by default using `AUTO_CRYPTO_HOST` and `AUTO_CRYPTO_PORT`.
- [ ] Start the Discord bot when invoked with `--discord`.

### Task 3: Launcher and workflow

**Files:**
- Modify: `Launch-Sentinel Chain.bat`
- Modify: `Launch-Sentinel Chain.ps1`
- Create: `.github/workflows/build.yml`
- Modify: `README.md`

- [ ] Harden the batch wrapper for partial extracts.
- [ ] Add installed launcher mode with VC++ runtime repair and `/health` wait.
- [ ] Package `SentinelChain.exe`, package static assets, and launcher pair.
- [ ] Build/upload `SentinelChain-Setup-<version>.exe`.
- [ ] Document beta installer behavior and support logs.
