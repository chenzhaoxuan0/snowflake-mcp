from __future__ import annotations

import argparse
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from dedalus_mcp.client import MCPClient


async def main(allow_writes: bool = False) -> None:
    async with MCPClient("http://localhost:8080/mcp") as client:
        tools = await client.list_tools()
        print("Available tools:")
        for t in tools:
            print(f"  - {t.name}: {t.description[:80]}...")
        print()

        print("--- list_databases ---")
        result = await client.call_tool("list_databases", {})
        print(result)
        print()

        print("--- list_warehouses ---")
        result = await client.call_tool("list_warehouses", {})
        print(result)
        print()

        db = os.getenv("SNOWFLAKE_DATABASE", "")
        if db:
            print("--- list_schemas ---")
            result = await client.call_tool("list_schemas", {"database": db})
            print(result)
            print()

        schema = os.getenv("SNOWFLAKE_SCHEMA", "")
        if db and schema:
            print("--- list_tables ---")
            result = await client.call_tool("list_tables", {"database": db, "schema": schema})
            print(result)
            print()

        if db and schema:
            print("--- describe_table ---")
            table = os.getenv("SNOWFLAKE_TEST_TABLE", "")
            if table:
                result = await client.call_tool("describe_table", {
                    "table": table,
                    "database": db,
                    "schema": schema,
                })
                print(result)
                print()

        print("--- run_query (SELECT) ---")
        result = await client.call_tool("run_query", {"sql": "SELECT CURRENT_VERSION() AS ver"})
        print(result)
        print()

        if allow_writes:
            print("--- run_query (write, allow_writes=True) ---")
            result = await client.call_tool(
                "run_query", {"sql": "CREATE TEMPORARY TABLE _mcp_test (id INT)", "allow_writes": True}
            )
            print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-writes-demo", action="store_true", default=False)
    args = parser.parse_args()
    asyncio.run(main(allow_writes=args.allow_writes_demo))
