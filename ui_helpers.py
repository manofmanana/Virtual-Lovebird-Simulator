"""Drawing helpers for the game's UI: soft shadows, glass panels, buttons, bars, and text.

Everything that's expensive to build (shadows, translucent panels, rendered text) is cached,
because phones running the browser version have little CPU to spare.
"""
import pygame

from config import ACCENT, INK, MUTED, WHITE

BACK_BUTTON = pygame.Rect(16, 16, 112, 40)

_text_cache = {}
_shape_cache = {}


def text(font, string, color=WHITE):
    """Render text, reusing the surface when the same text is drawn again."""
    key = (id(font), string, color)
    surface = _text_cache.get(key)
    if surface is None:
        if len(_text_cache) > 400:
            _text_cache.clear()
        surface = _text_cache[key] = font.render(string, True, color)
    return surface


def blit_text(screen, font, string, color=WHITE, shadow=True, **position):
    """Draw text placed by any Rect keyword (center=, midleft=, topright=, ...), with a soft shadow."""
    surface = text(font, string, color)
    rect = surface.get_rect(**position)
    if shadow:
        key = ("shade", id(font), string)
        shade = _text_cache.get(key)
        if shade is None:
            shade = _text_cache[key] = font.render(string, True, (0, 0, 0))
            shade.set_alpha(90)
        screen.blit(shade, rect.move(0, 2))
    screen.blit(surface, rect)
    return rect


def soft_shadow(size, radius, strength=90, spread=10):
    """A blurred-looking shadow made of stacked translucent rounded rectangles."""
    key = ("shadow", size, radius, strength, spread)
    if key not in _shape_cache:
        w, h = size
        surface = pygame.Surface((w + spread * 2, h + spread * 2), pygame.SRCALPHA)
        for i in range(spread, 0, -2):
            alpha = int(strength * (1 - i / spread) ** 2 / 3) + 4
            rect = pygame.Rect(spread - i, spread - i, w + i * 2, h + i * 2)
            pygame.draw.rect(surface, (0, 0, 0, alpha), rect, border_radius=radius + i)
        _shape_cache[key] = surface
    return _shape_cache[key]


def draw_shadow(screen, rect, radius=16, strength=90, spread=10, offset=(0, 6)):
    shadow = soft_shadow(rect.size, radius, strength, spread)
    screen.blit(shadow, (rect.x - spread + offset[0], rect.y - spread + offset[1]))


def glass_panel(screen, rect, radius=18, alpha=165, border=(255, 255, 255, 40), shadow=True):
    """A dark, slightly see-through rounded panel with a hairline border."""
    if shadow:
        draw_shadow(screen, rect, radius)
    key = ("glass", rect.size, radius, alpha, border)
    if key not in _shape_cache:
        if len(_shape_cache) > 300:
            _shape_cache.clear()
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (*INK, alpha), surface.get_rect(), border_radius=radius)
        pygame.draw.rect(surface, border, surface.get_rect(), 1, border_radius=radius)
        _shape_cache[key] = surface
    screen.blit(_shape_cache[key], rect.topleft)


def _lighter(color, amount):
    return tuple(min(255, int(c + (255 - c) * amount)) for c in color[:3])


def _darker(color, amount):
    return tuple(int(c * (1 - amount)) for c in color[:3])


def draw_modern_button(game, rect, label, color, hover_color=None, text_color=WHITE, hover=False):
    """A rounded button that lifts on hover and presses down while held (mouse or finger)."""
    pressed = hover and pygame.mouse.get_pressed()[0]
    face = rect.move(0, 3) if pressed else rect
    depth = 1 if pressed else 4
    base = _lighter(color, 0.12) if hover else color

    draw_shadow(game.screen, rect, radius=14, strength=70 if pressed else 110, spread=8, offset=(0, 4 if pressed else 7))
    pygame.draw.rect(game.screen, _darker(color, 0.28), face.move(0, depth), border_radius=14)  # the button's "side"
    pygame.draw.rect(game.screen, base, face, border_radius=14)
    highlight = face.inflate(-6, -face.h // 2)
    highlight.top = face.top + 3
    pygame.draw.rect(game.screen, _lighter(base, 0.18), highlight, border_radius=11)
    blit_text(game.screen, game.small_font, label, text_color, center=face.center)
    return rect


def draw_modern_progress_bar(game, x, y, width, height, value, max_value, color, bg_color=None):
    """A rounded bar filled to value/max_value, with a light sheen on the filled part."""
    radius = height // 2
    track = pygame.Rect(x, y, width, height)
    key = ("track", track.size)
    if key not in _shape_cache:
        surface = pygame.Surface(track.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (255, 255, 255, 38), surface.get_rect(), border_radius=radius)
        _shape_cache[key] = surface
    game.screen.blit(_shape_cache[key], track.topleft)
    filled = int(width * max(0, min(1, value / max_value))) if max_value else 0
    if filled >= height:
        bar = pygame.Rect(x, y, filled, height)
        pygame.draw.rect(game.screen, color, bar, border_radius=radius)
        sheen = pygame.Rect(x + 3, y + 2, filled - 6, max(2, height // 3))
        pygame.draw.rect(game.screen, _lighter(color, 0.35), sheen, border_radius=radius)


def pill(screen, font, label, color=WHITE, alpha=175, pad=(18, 8), **position):
    """Text on a rounded glass pill; returns the pill's rect."""
    surface = text(font, label, color)
    rect = surface.get_rect().inflate(pad[0] * 2, pad[1] * 2)
    setattr(rect, *next(iter(position.items())))
    glass_panel(screen, rect, radius=rect.h // 2, alpha=alpha)
    screen.blit(surface, surface.get_rect(center=rect.center))
    return rect


def draw_back_button(game):
    """'Back' button for the mini-games (phones have no Escape key)."""
    hover = BACK_BUTTON.collidepoint(pygame.mouse.get_pos())
    return draw_modern_button(game, BACK_BUTTON, "< Back", (64, 52, 44), hover=hover)


def draw_message_panel(game, title, lines, border=ACCENT, size=(500, 220)):
    """A white card in the middle of the screen with a title and a few lines of text."""
    panel = pygame.Rect(0, 0, *size)
    panel.center = (game.screen.get_width() // 2, game.screen.get_height() // 2)
    draw_shadow(game.screen, panel, radius=26, strength=140, spread=16, offset=(0, 10))
    pygame.draw.rect(game.screen, (253, 250, 244), panel, border_radius=26)
    pygame.draw.rect(game.screen, border, (panel.x, panel.y, panel.w, 8), border_top_left_radius=26, border_top_right_radius=26)
    blit_text(game.screen, game.title_font, title, INK, shadow=False, center=(panel.centerx, panel.y + 52))
    for i, line in enumerate(lines):
        color = MUTED if i < len(lines) - 1 or len(lines) == 1 else (186, 110, 20)
        blit_text(game.screen, game.font, line, color, shadow=False, center=(panel.centerx, panel.y + 105 + i * 34))
    return panel
