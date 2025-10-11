import os
import pytest

# Ensure SDL uses the dummy video driver when available to avoid opening a window
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

import pygame


@pytest.fixture(autouse=True)
def patch_pygame_display(monkeypatch):
    """Patch pygame.display.set_mode to return a Surface without opening a real window."""
    try:
        # ensure display module is initialized for Surface creation
        try:
            pygame.display.init()
        except Exception:
            pass

        def _dummy_set_mode(size, flags=0):
            # Return a plain Surface for tests
            return pygame.Surface(size)

        monkeypatch.setattr(pygame.display, 'set_mode', _dummy_set_mode)
    except Exception:
        # If pygame isn't present or can't be initialized, tests will mock further as needed
        pass
    yield
