from __future__ import annotations

from .server import build_app
from .config import get_settings
from .logging_setup import configure_logging


def main() -> None:
    settings = get_settings()
    configure_logging(settings)
    app = build_app(settings)
    app.run(
        transport="streamable-http",
        host=settings.host,
        port=settings.port,
        path="/mcp",
    )


if __name__ == "__main__":
    main()
