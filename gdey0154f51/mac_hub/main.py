from __future__ import annotations

import uvicorn

from gdey0154f51.mac_hub.app import create_app
from gdey0154f51.mac_hub.config import MacHubConfig


def main() -> None:
    config = MacHubConfig.from_env()
    app = create_app(config=config)
    uvicorn.run(app, host=config.bind_host, port=config.port)


if __name__ == "__main__":
    main()
