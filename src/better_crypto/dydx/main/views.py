"""Render the HTML for the project."""
from typing import Dict

from better_crypto.dydx.constants import PROJECT_DIR

import aiohttp_jinja2
import markdown2
from aiohttp import web


@aiohttp_jinja2.template("index.html")
async def index(request: web.Request) -> Dict[str, str]:
    """
    Read the README .md file and return the content as a dict.

    Args:
        request (web.Request)
    Returns:
        Dict[str, str]
    """
    if not request:
        with open(PROJECT_DIR / "README.md", encoding="utf8") as open_file:
            text = markdown2.markdown(open_file.read())

        return {"text": text}
    return {"text": "ERROR"}
