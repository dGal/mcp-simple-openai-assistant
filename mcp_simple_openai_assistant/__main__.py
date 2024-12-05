"""Entry point when module is run directly."""
import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())