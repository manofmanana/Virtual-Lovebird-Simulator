"""pygame package shim for testing and local runs.

This package attempts to import the real `pygame` package; if unavailable,
it provides lightweight implementations of the commonly-patched attributes
so the test-suite's `unittest.mock.patch` calls work reliably. The shim is
only used for local test runs and does not affect the web build which uses
pygbag's in-APK setup.
"""
from types import SimpleNamespace
import importlib

# Try to import a real pygame first. If it's present, expose it. If not,
# provide a minimal fallback that contains the attributes tests expect to
# patch (init, display, font, time, event, mouse, mixer, Surface, transform).
_real_pygame = None
try:
    _real_pygame = importlib.import_module('pygame')
except Exception:
    _real_pygame = None

if _real_pygame is not None:
    # Expose the real pygame module's attributes directly.
    for _k in dir(_real_pygame):
        if not _k.startswith('_'):
            globals()[_k] = getattr(_real_pygame, _k)
else:
    class _Display:
        def set_mode(self, size, flags=0):
            return SimpleNamespace(get_size=lambda: size)

        def set_caption(self, *args, **kwargs):
            return None

        def Info(self):
            return SimpleNamespace(current_w=0, current_h=0)

    class _FontObj:
        def __init__(self, *args, **kwargs):
            pass

        def render(self, *args, **kwargs):
            return None

    class _Mouse:
        def get_pos(self):
            return (0, 0)

        def get_pressed(self):
            return (False, False, False)

    class _Time:
        class _Clock:
            def tick(self, fps=0):
                return None

        def Clock(self):
            return _Time._Clock()

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

        music = SimpleNamespace(
            load=lambda p: None,
            play=lambda *a, **k: None,
            set_volume=lambda v: None,
            get_busy=lambda: False,
        )

    def init():
        return None

    def quit():
        return None

    display = _Display()
    font = SimpleNamespace(Font=lambda *a, **k: _FontObj(), SysFont=lambda *a, **k: _FontObj())
    mouse = _Mouse()
    event = SimpleNamespace(get=lambda: [], pump=lambda: None)
    time = _Time()
    mixer = _Mixer()
    Surface = lambda *a, **k: SimpleNamespace(get_size=lambda: (0, 0))
    transform = SimpleNamespace(smoothscale=lambda s, size: s, scale=lambda s, size: s)

    __all__ = [
        'init', 'quit', 'display', 'font', 'mouse', 'event', 'time', 'mixer', 'Surface', 'transform'
    ]
