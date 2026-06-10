from __future__ import annotations

from dataclasses import dataclass

from dedalus_mcp import tool
from dedalus_mcp.types import ToolAnnotations


@dataclass(frozen=True)
class PingResult:
    ok: bool = True
    message: str = "pong"


@tool(
    description="Smoke test ping (no external Snowflake dispatch required)",
    tags=["smoke", "health"],
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
async def smoke_ping(message: str = "pong") -> PingResult:
    return PingResult(message=message)


smoke_tools = [smoke_ping]
