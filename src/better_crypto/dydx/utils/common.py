"""Common utils."""
import argparse
import os
import pathlib
from typing import Any
from typing import List
from typing import Optional

import trafaret
from aiohttp import web
from trafaret_config import commandline


PATH = pathlib.Path(".")
settings_file = os.environ.get("SETTINGS_FILE", "api.dev.yml")
DEFAULT_CONFIG_PATH = PATH / "config" / settings_file


CONFIG_TRAFARET = trafaret.Dict(
    {
        trafaret.Key("app"): trafaret.Dict(
            {"host": trafaret.String(), "port": trafaret.Int()}
        )
    }
)


def get_config(argv: Any = None) -> Any:
    """Get application config."""
    arg_parser = argparse.ArgumentParser()
    commandline.standard_argparse_options(
        arg_parser, default_config=DEFAULT_CONFIG_PATH
    )
    options = arg_parser.parse_args(argv)

    return commandline.config_from_options(options, CONFIG_TRAFARET)


def init_config(
    app: web.Application, *, config: Optional[List[str]] = None
) -> None:
    """Init application config."""
    app["config"] = get_config(config or ["-c", DEFAULT_CONFIG_PATH.as_posix()])
