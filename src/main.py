from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from server import create_server  # noqa: E402


def main() -> None:
    server = create_server()
    server.collect_all()
    server.run(8080)


if __name__ == "__main__":
    main()
