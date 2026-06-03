from __future__ import annotations

import os

from dedalus_mcp import MCPServer
from dedalus_mcp.server import TransportSecuritySettings

from snowflake_mcp import (
    describe_table,
    list_databases,
    list_schemas,
    list_tables,
    list_warehouses,
    run_query,
    snowflake_conn,
)


def create_server() -> MCPServer:
    as_url = os.getenv("DEDALUS_AS_URL", "https://as.dedaluslabs.ai")
    return MCPServer(
        name="snowflake-mcp",
        connections=[snowflake_conn],
        http_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        streamable_http_stateless=True,
        authorization_server=as_url,
    )


async def main() -> None:
    server = create_server()
    server.collect(
        list_databases,
        list_schemas,
        list_tables,
        describe_table,
        run_query,
        list_warehouses,
    )
    await server.serve(port=8080)
