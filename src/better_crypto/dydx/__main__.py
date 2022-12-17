"""Runs the uvloop."""
from better_crypto.dydx.app import init_app

import aiohttp_debugtoolbar
import uvloop
from aiohttp import web


def create_app() -> web.Application:
    """Create the app."""
    app = init_app()
    aiohttp_debugtoolbar.setup(app, check_host=False)

    return app


def main() -> None:
    """Run uvloop."""
    app = init_app()
    app_settings = app["config"]["app"]
    uvloop.install()
    web.run_app(app, host=app_settings["host"], port=app_settings["port"])


if __name__ == "__main__":
    main()
