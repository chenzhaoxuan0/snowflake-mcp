from __future__ import annotations

import asyncio

from dotenv import load_dotenv

load_dotenv()

from server import main  # noqa: E402

if __name__ == "__main__":
    asyncio.run(main())
