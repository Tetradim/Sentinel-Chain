"""Static checks for Windows first-run installer support."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_BAT = ROOT / "Launch-Auto-Crypto.bat"
LAUNCHER_PS1 = ROOT / "Launch-Auto-Crypto.ps1"
BUILD_WORKFLOW = ROOT / ".github" / "workflows" / "build.yml"
README = ROOT / "README.md"
WINDOWS_ENTRYPOINT = ROOT / "windows_entrypoint.py"


def test_launcher_supports_installed_and_source_modes():
    batch = LAUNCHER_BAT.read_text(encoding="utf-8")
    script = LAUNCHER_PS1.read_text(encoding="utf-8")

    assert "Launch-Auto-Crypto.ps1" in batch
    assert "AutoCrypto-Setup" in batch
    assert "if not exist" in batch.lower()
    assert "Auto-Crypto Launcher - Installed App" in script
    assert "AutoCrypto.exe" in script
    assert "Start-InstalledAutoCrypto" in script
    assert "Start-SourceAutoCrypto" in script
    assert "Ensure-InstalledRuntimeDependencies" in script
    assert "Test-VcRuntimeInstalled" in script
    assert "vc_redist.x64.exe" in script
    assert "/health" in script
    assert "/ui" in script


def test_packaged_entrypoint_supports_api_and_discord_modes():
    entrypoint = WINDOWS_ENTRYPOINT.read_text(encoding="utf-8")

    assert "AUTO_CRYPTO_HOST" in entrypoint
    assert "AUTO_CRYPTO_PORT" in entrypoint
    assert "autocrypto.app:create_app_from_env" in entrypoint
    assert "run_from_env" in entrypoint
    assert "--discord" in entrypoint
    assert "load_dotenv" in entrypoint


def test_build_workflow_creates_installer():
    workflow = BUILD_WORKFLOW.read_text(encoding="utf-8")

    assert "Build Auto-Crypto Windows Installer" in workflow
    assert "python -m PyInstaller" in workflow
    assert "windows_entrypoint.py" in workflow
    assert "AutoCrypto.exe" in workflow
    assert "Launch-Auto-Crypto.bat" in workflow
    assert "Launch-Auto-Crypto.ps1" in workflow
    assert "AutoCrypto-Setup-{#MyAppVersion}" in workflow
    assert 'Filename: "{app}\\Launch-Auto-Crypto.bat"' in workflow
    assert "Minionguyjpro/Inno-Setup-Action" in workflow
    assert "--collect-data autocrypto" in workflow


def test_readme_documents_beta_installer_first_run_behavior():
    readme = README.read_text(encoding="utf-8")

    assert "AutoCrypto-Setup-<version>.exe" in readme
    assert "downloads missing runtime dependencies on first launch" in readme
    assert "Visual C++ Runtime" in readme
    assert "Auto-Crypto.log" in readme
    assert "Python, Node.js, npm, or MongoDB" in readme
