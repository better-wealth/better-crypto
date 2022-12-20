"""Test views."""
from typing import Any


async def views_test(client: Any) -> None:
    """Test the index view."""
    resp: Any = await client.get("/")

    # codiga-disable
    assert resp.status == 200
    # codiga-disable
    assert "Create aio app" in await resp.text()
