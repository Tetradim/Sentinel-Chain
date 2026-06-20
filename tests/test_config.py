from decimal import Decimal
from pathlib import Path

from autocrypto.config import load_settings


def test_load_settings_maps_environment_to_risk_webhook_and_repository_config(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    db_path = tmp_path / "configured.sqlite3"
    monkeypatch.setenv("AUTO_CRYPTO_DB_PATH", str(db_path))
    monkeypatch.setenv("AUTO_CRYPTO_MAX_ORDER_NOTIONAL", "250")
    monkeypatch.setenv("AUTO_CRYPTO_MAX_OPEN_NOTIONAL", "750")
    monkeypatch.setenv("AUTO_CRYPTO_MAX_POSITION_EQUITY_PCT", "5")
    monkeypatch.setenv("AUTO_CRYPTO_MAX_RISK_PER_TRADE_PCT", "2")
    monkeypatch.setenv("AUTO_CRYPTO_MAX_LEVERAGE", "2")
    monkeypatch.setenv("AUTO_CRYPTO_MAX_CONSECUTIVE_LOSSES", "3")
    monkeypatch.setenv("AUTO_CRYPTO_REQUIRE_STOP_LOSS", "false")
    monkeypatch.setenv("AUTO_CRYPTO_MAX_STOP_LOSS_PCT", "4")
    monkeypatch.setenv("AUTO_CRYPTO_MAX_TRAILING_STOP_PCT", "6")
    monkeypatch.setenv("AUTO_CRYPTO_MIN_REWARD_RISK_RATIO", "2")
    monkeypatch.setenv("AUTO_CRYPTO_MIN_TOTAL_REWARD_RISK_RATIO", "1.5")
    monkeypatch.setenv("AUTO_CRYPTO_MAX_TAKE_PROFIT_TARGETS", "3")
    monkeypatch.setenv("AUTO_CRYPTO_ALLOWED_EXCHANGES", "paper,binance, kraken")
    monkeypatch.setenv("AUTO_CRYPTO_WEBHOOK_SECRET", "secret")
    monkeypatch.setenv("AUTO_CRYPTO_WEBHOOK_TOLERANCE_SECONDS", "120")
    monkeypatch.setenv("AUTO_CRYPTO_REQUIRE_APPROVAL", "true")

    settings = load_settings()

    assert settings.db_path == db_path
    assert settings.webhook_secret == "secret"
    assert settings.webhook_tolerance_seconds == 120
    assert settings.require_approval is True
    assert settings.risk.max_order_notional == Decimal("250")
    assert settings.risk.max_open_notional == Decimal("750")
    assert settings.risk.max_position_equity_pct == Decimal("5")
    assert settings.risk.max_risk_per_trade_pct == Decimal("2")
    assert settings.risk.max_leverage == Decimal("2")
    assert settings.risk.max_consecutive_losses == 3
    assert settings.risk.require_stop_loss is False
    assert settings.risk.max_stop_loss_pct == Decimal("4")
    assert settings.risk.max_trailing_stop_pct == Decimal("6")
    assert settings.risk.min_reward_risk_ratio == Decimal("2")
    assert settings.risk.min_total_reward_risk_ratio == Decimal("1.5")
    assert settings.risk.max_take_profit_targets == 3
    assert settings.risk.allowed_exchanges == {"paper", "binance", "kraken"}


def test_zero_webhook_tolerance_disables_timestamp_staleness_window(monkeypatch):
    monkeypatch.setenv("AUTO_CRYPTO_WEBHOOK_TOLERANCE_SECONDS", "0")

    settings = load_settings()

    assert settings.webhook_tolerance_seconds is None


def test_load_settings_reads_dotenv_from_current_working_directory(monkeypatch, tmp_path):
    db_path = tmp_path / "dotenv.sqlite3"
    (tmp_path / ".env").write_text(f"AUTO_CRYPTO_DB_PATH={db_path}\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AUTO_CRYPTO_DB_PATH", raising=False)

    settings = load_settings()

    assert settings.db_path == db_path


def test_docker_entrypoint_uses_env_backed_app_factory():
    dockerfile = Path(__file__).resolve().parents[1] / "Dockerfile"

    text = dockerfile.read_text(encoding="utf-8")

    assert "autocrypto.app:create_app_from_env" in text
    assert "--factory" in text
