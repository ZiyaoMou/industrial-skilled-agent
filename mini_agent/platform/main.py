"""CLI entrypoint for running the skill-build platform server."""

from __future__ import annotations

import argparse

import uvicorn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the skill-build platform API server.")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8001, help="Port number")
    parser.add_argument("--reload", action="store_true", help="Enable auto reload for development")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    uvicorn.run("mini_agent.platform.api:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()

