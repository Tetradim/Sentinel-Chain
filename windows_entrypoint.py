"""Windows packaged entrypoint for Sentinel Chain."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv


def load_installed_environment() -> None:
    load_dotenv(dotenv_path=Path.cwd() / ".env")


def run_api() -> None:
    host = os.getenv("AUTO_CRYPTO_HOST", "127.0.0.1")
    port = int(os.getenv("AUTO_CRYPTO_PORT", "8004"))
    uvicorn.run("sentinel_chain.app:create_app_from_env", host=host, port=port, reload=False, factory=True)


def run_discord() -> None:
    from sentinel_chain.discord_bot import run_from_env

    run_from_env()


def main() -> None:
    load_installed_environment()
    if "--discord" in sys.argv:
        run_discord()
        return
    run_api()


if __name__ == "__main__":
    main()
