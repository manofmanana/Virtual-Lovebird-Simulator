"""Browser entry point. pygbag looks for main.py and runs it as WebAssembly.

To play on the desktop instead, run `python project.py`.
"""
import asyncio
import traceback

import pygame  # noqa: F401  pygbag only loads pygame if main.py itself imports it


def report_crash():
    """Show the error on the loading screen (and the browser console) instead of hanging silently."""
    details = traceback.format_exc()
    print(details)
    try:
        import platform
        platform.window.mango_error(details)
    except Exception:
        pass


async def main():
    try:
        from project import MangoTamagotchi
        game = MangoTamagotchi()
        await game.run()
    except Exception:
        report_crash()
        raise


asyncio.run(main())
