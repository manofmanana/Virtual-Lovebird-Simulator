"""Browser entry point. pygbag looks for main.py and runs it as WebAssembly.

To play on the desktop instead, run `python project.py`.
"""
import asyncio

import pygame  # noqa: F401  pygbag only loads pygame if main.py itself imports it

from project import MangoTamagotchi


async def main():
    game = MangoTamagotchi()
    await game.run()


asyncio.run(main())
