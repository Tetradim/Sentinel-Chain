"""Static checks for Windows first-run installer support."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_BAT = ROOT / "Launch-Sentinel-Chain.bat"
LAUNCHER_PS1 = ROOT / "Launch-Sentinel-Chain.ps1"
BUILD_WORKFLOW = ROOT / ".github" / "workflows" / "build.yml"
README = ROOT / "README.md"
WINDOWS_ENTRYPOINT = ROOT / "windows_entrypoint.py"


def test_launcher_supports_installed_and_source_modes():
    batch = LAUNCHER_BAT.read_text(encoding="utf-8")
    script = LAUNCHER_PS1.read_text(encoding="utf-8")

    assert "Launch-Sentinel-Chain.ps1" in batch
    assert "SentinelChain-Setup" in batch
    assert "if not exist" in batch.lower()
    assert "Sentinel Chain Launcher - Installed App" in script
    assert "SentinelChain.exe" in script
    assert "Start-InstalledSentinelChain" in script
    assert "Start-SourceSentinelChain" in script
    assert "Ensure-InstalledRuntimeDependencies" in script
    assert "Test-VcRuntimeInstalled" in script
    assert "vc_redist.x64.exe" in script
    assert "/health" in script
    assert "/ui" in script


def test_packaged_entrypoint_supports_api_and_discord_modes():
    entrypoint = WINDOWS_ENTRYPOINT.read_text(encoding="utf-8")

    assert "AUTO_CRYPTO_HOST" in entrypoint
    assert "AUTO_CRYPTO_PORT" in entrypoint
    assert "sentinel_chain.app:create_app_from_env" in entrypoint
    assert "run_from_env" in entrypoint
    assert "--discord" in entrypoint
    assert "load_dotenv" in entrypoint


def test_build_workflow_creates_installer():
    workflow = BUILD_WORKFLOW.read_text(encoding="utf-8")

    assert "Build Sentinel Chain Windows Installer" in workflow
    assert "python -m PyInstaller" in workflow
    assert "windows_entrypoint.py" in workflow
    assert "SentinelChain.exe" in workflow
    assert "Launch-Sentinel-Chain.bat" in workflow
    assert "Launch-Sentinel-Chain.ps1" in workflow
    assert "SentinelChain-Setup-{#MyAppVersion}" in workflow
    assert 'Filename: "{app}\\Launch-Sentinel-Chain.bat"' in workflow
    assert "Minionguyjpro/Inno-Setup-Action" in workflow
    assert "--collect-data sentinel_chain" in workflow


def test_readme_documents_beta_installer_first_run_behavior():
    readme = README.read_text(encoding="utf-8")

    assert "SentinelChain-Setup-<version>.exe" in readme
    assert "downloads missing runtime dependencies on first launch" in readme
    assert "Visual C++ Runtime" in readme
    assert "Sentinel-Chain.log" in readme
    assert "Python, Node.js, npm, or MongoDB" in readme
