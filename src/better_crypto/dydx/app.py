from pathlib import Path
from typing import List
from typing import Optional

from better_crypto.dydx.routes import init_routes
from better_crypto.dydx.utils.common import init_config

import aiohttp_jinja2
import jinja2
from aiohttp import web


path = Path(__file__).parent


def init_jinja2(app: web.Application) -> None:
    """
    Initialize jinja2 template for application.
    """
    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(str(path / "templates"))
    )


def init_app(config: Optional[List[str]] = None) -> web.Application:
    app = web.Application()

    init_jinja2(app)
    init_config(app, config=config)
    init_routes(app)

    return app
