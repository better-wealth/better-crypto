"""Check requirements."""
import json
import re
import subprocess  # nosec
from functools import partial
from pathlib import Path
from typing import Dict

import click


req_dir = Path(".").parent.parent / "requirements"
PIP_LIST = "pip list -o --format=json"


def upgrade_requirements() -> None:
    """Upgrade requirements."""
    warning_message = False
    req_files = [
        req_file for req_file in req_dir.iterdir() if req_file.is_file()
    ]

    for req_file in req_files:
        with req_file.open() as open_file:
            old_req = open_file.read()
            fresh_version = json.loads(
                subprocess.check_output(PIP_LIST, shell=True).decode(  # nosec
                    "utf-8"
                )
            )

            packages: Dict[str, str] = {
                package["name"]: package["latest_version"]
                for package in fresh_version
                if package
            }

        with req_file.open("w") as open_file:
            new_req = old_req
            for name, version in packages.items():
                new_req = re.sub(
                    rf"{name}==[\d .]*", f"{name}=={version}", new_req
                )
            open_file.seek(0)
            open_file.write(new_req)
            open_file.truncate()

        if old_req != new_req:
            warning_message = True

    if warning_message:
        echo = partial(click.echo, err=True)
        echo(
            click.style(
                "Please rebuild your docker container with ", fg="bright_green"
            )
            + click.style("'make build'", fg="bright_blue")
        )


if __name__ == "__main__":
    upgrade_requirements()
