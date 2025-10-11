import sys
import types


def _make_minimal_pygame():
    mod = types.ModuleType('pygame')
    mod.init = lambda *a, **k: None
    mod.quit = lambda *a, **k: None
    mod.SCALED = 0

    # display
    disp = types.ModuleType('pygame.display')

    def set_mode(size, flags=0):
        return types.SimpleNamespace(get_size=lambda: size)

    def set_caption(caption):
        return None

    disp.set_mode = set_mode
    disp.set_caption = set_caption
    mod.display = disp

    # font
    f = types.ModuleType('pygame.font')

    class Font:
        def __init__(self, *a, **k):
            pass

        def render(self, *a, **k):
            return None

    def SysFont(*a, **k):
        return Font()

    f.Font = Font
    f.SysFont = SysFont
    mod.font = f

    # time
    t = types.ModuleType('pygame.time')

    class Clock:
        def tick(self, *a, **k):
            return 0

    t.Clock = Clock
    mod.time = t

    # event
    e = types.ModuleType('pygame.event')

    def get():
        return []

    e.get = get
    mod.event = e

    # mouse
    m = types.ModuleType('pygame.mouse')

    def get_pos():
        return (0, 0)

    def get_pressed():
        return (False, False, False)

    m.get_pos = get_pos
    m.get_pressed = get_pressed
    mod.mouse = m

    # mixer
    mix = types.ModuleType('pygame.mixer')

    def pre_init(*a, **k):
        return None

    def init(*a, **k):
        return None

    class Sound:
        def __init__(self, *a, **k):
            pass

        def play(self, *a, **k):
            return None

    music = types.SimpleNamespace(load=lambda *a, **k: None, play=lambda *a, **k: None)
    mix.pre_init = pre_init
    mix.init = init
    mix.Sound = Sound
    mix.music = music
    mod.mixer = mix

    # surface/transform placeholders
    mod.Surface = lambda *a, **k: types.SimpleNamespace(fill=lambda *a, **k: None)
    mod.transform = types.SimpleNamespace(scale=lambda s, size: s)

    return mod


def pytest_configure(config):
    # If pygame exists but lacks expected attributes (because assets include a partial package),
    # replace it with a minimal shim so tests that patch attributes succeed.
    try:
        import pygame as existing  # type: ignore
    except Exception:
        existing = None

    if existing is None:
        sys.modules['pygame'] = _make_minimal_pygame()
    else:
        # If the existing module is missing key attributes, replace it.
        missing = False
        for attr in ('init', 'display'):
            if not hasattr(existing, attr):
                missing = True
                break
        if missing:
            sys.modules['pygame'] = _make_minimal_pygame()
import sys
from types import SimpleNamespace, ModuleType


def _ensure_pygame_attrs():
    """Ensure a module named 'pygame' exists in sys.modules and exposes
    the minimal attributes the test-suite patches (init, display, font,
    time, event, mouse, mixer, Surface, transform). If a real pygame is
    available, don't overwrite it.
    """
    mod = sys.modules.get('pygame')
    # If real pygame is already imported (C extension), assume it's fine.
    if mod is not None and getattr(mod, '__file__', None) and 'site-packages' in str(getattr(mod, '__file__', '')):
        return

    if mod is None:
        mod = ModuleType('pygame')
        sys.modules['pygame'] = mod

    # Provide missing attributes if they aren't present.
    if not hasattr(mod, 'init'):
        def init():
            return None

        def quit():
            return None

        mod.init = init
        mod.quit = quit

    if not hasattr(mod, 'display'):
        class _Display:
            def set_mode(self, size, flags=0):
                return SimpleNamespace(get_size=lambda: size)

            def set_caption(self, *a, **k):
                return None

            def Info(self):
                return SimpleNamespace(current_w=0, current_h=0)

        mod.display = _Display()

    if not hasattr(mod, 'font'):
        class _FontObj:
            def __init__(self, *a, **k):
                pass

            def render(self, *a, **k):
                return None

        mod.font = SimpleNamespace(Font=lambda *a, **k: _FontObj(), SysFont=lambda *a, **k: _FontObj())

    if not hasattr(mod, 'time'):
        class _Time:
            class _Clock:
                def tick(self, fps=0):
                    return None

            def Clock(self):
                return _Time._Clock()

            def delay(self, ms):
                return None

        mod.time = _Time()

    if not hasattr(mod, 'event'):
        mod.event = SimpleNamespace(get=lambda: [], pump=lambda: None)

    if not hasattr(mod, 'mouse'):
        class _Mouse:
            def get_pos(self):
                return (0, 0)

            def get_pressed(self):
                return (False, False, False)

        mod.mouse = _Mouse()

    if not hasattr(mod, 'mixer'):
        class _Mixer:
            def pre_init(self, *a, **k):
                return None

            def init(self, *a, **k):
                return None

            def get_init(self):
                return False

            music = SimpleNamespace(load=lambda p: None, play=lambda *a, **k: None, set_volume=lambda v: None, get_busy=lambda: False)

        mod.mixer = _Mixer()

    if not hasattr(mod, 'Surface'):
        mod.Surface = lambda *a, **k: SimpleNamespace(get_size=lambda: (0, 0))

    if not hasattr(mod, 'transform'):
        mod.transform = SimpleNamespace(smoothscale=lambda s, size: s, scale=lambda s, size: s)


# Run the ensure step at test collection/import time.
_ensure_pygame_attrs()
