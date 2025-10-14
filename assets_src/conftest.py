import sys
import types


def _ensure_module_attr(module, name, value):
    if not hasattr(module, name):
        setattr(module, name, value)


def _make_display():
    disp = types.ModuleType('pygame.display')

    def set_mode(size, flags=0):
        # Return a simple surface-like placeholder
        s = types.SimpleNamespace(get_size=lambda: size)
        return s

    def set_caption(caption):
        return None

    disp.set_mode = set_mode
    disp.set_caption = set_caption
    return disp


def _make_font():
    f = types.ModuleType('pygame.font')

    class Font:
        def __init__(self, *args, **kwargs):
            pass

        def render(self, *a, **k):
            return None

    def SysFont(*a, **k):
        return Font()

    f.Font = Font
    f.SysFont = SysFont
    return f


def _make_time():
    t = types.ModuleType('pygame.time')

    class Clock:
        def tick(self, *a, **k):
            return 0

    t.Clock = Clock
    return t


def _make_event():
    e = types.ModuleType('pygame.event')

    def get():
        return []

    e.get = get
    return e


def _make_mouse():
    m = types.ModuleType('pygame.mouse')

    def get_pos():
        return (0, 0)

    def get_pressed():
        return (False, False, False)

    m.get_pos = get_pos
    m.get_pressed = get_pressed
    return m


def _make_mixer():
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
    return mix


# This module runs at test-collection time when placed in the tests root (assets/).
# It ensures sys.modules['pygame'] is usable for tests that patch pygame attributes
def pytest_configure(config):
    # If a real pygame is importable, prefer it; otherwise ensure a minimal shim
    try:
        import pygame as real_pygame  # type: ignore
    except Exception:
        real_pygame = None

    if real_pygame is None:
        mod = types.ModuleType('pygame')
        # basic functions
        mod.init = lambda *a, **k: None
        mod.quit = lambda *a, **k: None
        mod.SCALED = 0
        # submodules
        mod.display = _make_display()
        mod.font = _make_font()
        mod.time = _make_time()
        mod.event = _make_event()
        mod.mouse = _make_mouse()
        mod.mixer = _make_mixer()
        # Surface/transform placeholders
        mod.Surface = lambda *a, **k: types.SimpleNamespace(fill=lambda *a, **k: None)
        mod.transform = types.SimpleNamespace(scale=lambda s, size: s)
        sys.modules['pygame'] = mod
    else:
        # Real pygame exists; make sure required members exist (to avoid AttributeError on patch)
        mod = real_pygame
        _ensure_module_attr(mod, 'init', getattr(mod, 'init', lambda *a, **k: None))
        _ensure_module_attr(mod, 'quit', getattr(mod, 'quit', lambda *a, **k: None))
        if not hasattr(mod, 'display'):
            mod.display = _make_display()
        if not hasattr(mod, 'font'):
            mod.font = _make_font()
        if not hasattr(mod, 'time'):
            mod.time = _make_time()
        if not hasattr(mod, 'event'):
            mod.event = _make_event()
        if not hasattr(mod, 'mouse'):
            mod.mouse = _make_mouse()
        if not hasattr(mod, 'mixer'):
            mod.mixer = _make_mixer()
