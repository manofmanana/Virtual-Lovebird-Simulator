"""Early startup hook to ensure a usable `pygame` module exists for tests.

pytest and other test runners may import modules from a copied workspace
path. To avoid import-shadowing issues where a partial `pygame` package is
present without the attributes tests expect to patch, we populate
sys.modules['pygame'] at interpreter startup with a safe fallback module
if a real pygame isn't available.
"""
import sys
from types import ModuleType, SimpleNamespace


def _ensure_pygame_module():
    mod = sys.modules.get('pygame')
    if mod is not None:
        # If the existing module already has init and display, assume it's fine.
        if hasattr(mod, 'init') and hasattr(mod, 'display'):
            return

    # Create a minimal pygame-like module and insert it into sys.modules so
    # subsequent imports (including unittest.mock.patch('pygame.init')) will
    # observe these attributes.
    pg = ModuleType('pygame')

    def init():
        return None

    def quit():
        return None

    class _Display:
        def set_mode(self, size, flags=0):
            return SimpleNamespace(get_size=lambda: size)

        def set_caption(self, *a, **k):
            return None

        def Info(self):
            return SimpleNamespace(current_w=0, current_h=0)

    class _FontObj:
        def __init__(self, *a, **k):
            pass

        def render(self, *a, **k):
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

        music = SimpleNamespace(load=lambda p: None, play=lambda *a, **k: None, set_volume=lambda v: None, get_busy=lambda: False)

    pg.init = init
    pg.quit = quit
    pg.display = _Display()
    pg.font = SimpleNamespace(Font=lambda *a, **k: _FontObj(), SysFont=lambda *a, **k: _FontObj())
    pg.mouse = _Mouse()
    pg.event = SimpleNamespace(get=lambda: [], pump=lambda: None)
    pg.time = _Time()
    pg.mixer = _Mixer()
    pg.Surface = lambda *a, **k: SimpleNamespace(get_size=lambda: (0, 0))
    pg.transform = SimpleNamespace(smoothscale=lambda s, size: s, scale=lambda s, size: s)

    sys.modules['pygame'] = pg


# Execute immediately on interpreter startup.
_ensure_pygame_module()
