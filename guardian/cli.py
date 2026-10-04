"""Command-line entry point: `uv run guardian <command>`."""

import argparse

from guardian import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="guardian", description="VILPE Guardian backend tools")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("serve", help="run the API locally on :8000")
    args = parser.parse_args(argv)

    if args.command == "serve":
        import uvicorn

        uvicorn.run("guardian.api.app:app", port=8000, reload=True)
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
