"""Core initialization for the package."""
import asyncio
from .server import serve

__all__ = ['main', 'server']

from .server import serve


def main():
    """MCP Time Server - Time and timezone conversion functionality for MCP"""
    asyncio.run(serve())


if __name__ == "__main__":
    main()
