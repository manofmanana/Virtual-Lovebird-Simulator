"""Minimal pygame shim placed under assets/pygame so tests importing the package
from the copied assets folder see expected attributes.

This file is intentionally simple: it provides the functions and submodules the
test-suite mocks (init, display, font, time, event, mouse, mixer, Surface).
It will be used only in test environments where a full pygame is not present.
"""
from types import SimpleNamespace, ModuleType


def init(*a, **k):
    return None


def quit(*a, **k):
    return None


SCALED = 0


# display
display = ModuleType('pygame.display')

def set_mode(size, flags=0):
    """Minimal pygame shim placed under assets/pygame so tests importing the package
    from the copied assets folder see expected attributes.

    This file is intentionally simple: it provides the functions and submodules the
    test-suite mocks (init, display, font, time, event, mouse, mixer, Surface).
    It will be used only in test environments where a full pygame is not present.
    """
    from types import SimpleNamespace, ModuleType


    def init(*a, **k):
        return None


    def quit(*a, **k):
        return None


    SCALED = 0


    # display
    display = ModuleType('pygame.display')

    def set_mode(size, flags=0):
        return SimpleNamespace(get_size=lambda: size)


    def set_caption(caption):
        return None


    display.set_mode = set_mode
    display.set_caption = set_caption


    # font
    font = ModuleType('pygame.font')

    class Font:
        def __init__(self, *a, **k):
            pass

        def render(self, *a, **k):
            return None


    def SysFont(*a, **k):
        return Font()


    font.Font = Font
    font.SysFont = SysFont


    # time
    time = ModuleType('pygame.time')

    class Clock:
        def tick(self, *a, **k):
            return 0


    time.Clock = Clock


    # event
    event = ModuleType('pygame.event')

    def get():
        return []


    event.get = get


    # mouse
    mouse = ModuleType('pygame.mouse')

    def get_pos():
        return (0, 0)


    def get_pressed():
        return (False, False, False)


    mouse.get_pos = get_pos
    mouse.get_pressed = get_pressed


    # mixer
    mixer = ModuleType('pygame.mixer')

    def pre_init(*a, **k):
        return None


    def m_init(*a, **k):
        return None


    class Sound:
        def __init__(self, *a, **k):
            pass

        def play(self, *a, **k):
            return None


    music = SimpleNamespace(load=lambda *a, **k: None, play=lambda *a, **k: None)

    mixer.pre_init = pre_init
    mixer.init = m_init
    mixer.Sound = Sound
    mixer.music = music


    # Surface and transform placeholders
    def Surface(*a, **k):
        return SimpleNamespace(fill=lambda *a, **k: None)


    transform = SimpleNamespace(scale=lambda s, size: s)
