from __future__ import annotations

import uvicorn

from gdey0154f51.pi_server.app import create_app
from gdey0154f51.pi_server.config import PiServerConfig


def main() -> None:
    config = PiServerConfig.from_env()
    app = create_app(config=config)
    uvicorn.run(app, host=config.bind_host, port=config.port)


if __name__ == "__main__":
    main()
