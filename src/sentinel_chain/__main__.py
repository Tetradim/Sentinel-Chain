from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv


def main() -> None:
    load_dotenv(dotenv_path=Path.cwd() / ".env")
    host = os.getenv("AUTO_CRYPTO_HOST", "127.0.0.1")
    port = int(os.getenv("AUTO_CRYPTO_PORT", "8004"))
    uvicorn.run("sentinel_chain.app:create_app_from_env", host=host, port=port, reload=False, factory=True)


if __name__ == "__main__":
    main()
