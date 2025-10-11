"""Lightweight pygame shim for local tests and environments where
pygbag's in-apk pygame shim may shadow the real pygame package.

This stub tries to import the real `pygame` package first. If unavailable,
it exposes a minimal set of attributes used by the test-suite so that
`unittest.mock.patch` can patch `pygame.init`, `pygame.display.set_mode`,
`pygame.font.Font`, etc.

This file is intentionally small and only used for test runs; the real
web build uses a vendored compiled extension and the preloader to make
`pygame` available inside the browser runtime.
"""
from types import SimpleNamespace
import importlib

try:
    _real_pygame = importlib.import_module('pygame')
except Exception:
    _real_pygame = None

if _real_pygame:
    # Expose the real pygame module
    globals().update({k: getattr(_real_pygame, k) for k in dir(_real_pygame) if not k.startswith('_')})
else:
    # Minimal shim objects
    class _Display:
        def set_mode(self, size, flags=0):
            return SimpleNamespace(get_size=lambda: size)
        def set_caption(self, *args, **kwargs):
            return None
        def Info(self):
            return SimpleNamespace(current_w=0, current_h=0)

    class _Font:
        def __init__(self, *args, **kwargs):
            pass
        def render(self, *args, **kwargs):
            return None

    class _Mouse:
        def get_pos(self):
            return (0, 0)
        def get_pressed(self):
            return (False, False, False)

    class _Event:
        def get(self):
            return []
        def pump(self):
            return None

    class _Time:
        def Clock(self):
            return SimpleNamespace(tick=lambda fps: None)
        def delay(self, ms):
            return None

    class _Mixer:
        def pre_init(self, *a, **k):
            return None
        def init(self, *a, **k):
            return None
        def get_init(self):
            return False
        def set_num_channels(self, n):
            return None
        def music(self):
            return None

    # module-level functions
    def init():
        return None

    def quit():
        return None

    display = _Display()
    font = SimpleNamespace(Font=lambda *a, **k: _Font(), SysFont=lambda *a, **k: _Font())
    mouse = _Mouse()
    event = _Event()
    time = _Time()
    mixer = _Mixer()
    Surface = lambda *a, **k: SimpleNamespace(get_size=lambda: (0, 0))
    transform = SimpleNamespace(smoothscale=lambda s, size: s, scale=lambda s, size: s)
    mixer = _Mixer()

    # expose names for tests to patch
    __all__ = [
        'init', 'quit', 'display', 'font', 'mouse', 'event', 'time', 'mixer', 'Surface', 'transform'
    ]
