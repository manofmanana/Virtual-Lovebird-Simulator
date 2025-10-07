"""UI helper functions extracted from project.py.

These are small, stateless drawing utilities that operate on a game
instance (providing screen, fonts, etc.).
"""
try:
    import pygame
except Exception:
    # Allow importing this module in environments without pygame (tests, packaging)
    pygame = None

# Simple availability flag so callers / tests can import this module even when
# pygame is not present. The draw helpers below become no-ops when pygame is
# unavailable which avoids raising on import or during headless tests.
PYGAME_AVAILABLE = pygame is not None


def draw_modern_button(game, rect, text, color, hover_color, text_color=(255,255,255), hover=False):
    """Draw a modern button using the provided game instance for surface/fonts.

    Parameters mirror the original method but the function accepts a `game`
    instance so it can be called from other modules without introducing
    circular imports.
    """
    # If pygame isn't available, behave as a safe no-op and return the rect.
    if not PYGAME_AVAILABLE:
        return rect

    # Button shadow
    shadow_rect = rect.copy()
    shadow_rect.x += 3
    shadow_rect.y += 3
    try:
        pygame.draw.rect(game.screen, (0, 0, 0, 50), shadow_rect, border_radius=8)
    except Exception:
        # Some backends ignore alpha in draw; ignore failures
        pass

    # Button background
    button_color = hover_color if hover else color
    pygame.draw.rect(game.screen, button_color, rect, border_radius=8)

    # Button border
    border_color = (255,255,255) if hover else getattr(game, 'LIGHT_GRAY', (200,200,200))
    pygame.draw.rect(game.screen, border_color, rect, 2, border_radius=8)

    # Button text
    text_surface = game.small_font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=rect.center)
    game.screen.blit(text_surface, text_rect)

    return rect


def draw_modern_progress_bar(game, x, y, width, height, value, max_value, color, bg_color=None):
    """Draw a modern progress bar using the provided game instance.

    Keeps the same visual contract as the original method.
    """
    if bg_color is None:
        bg_color = getattr(game, 'DARK_GRAY', (48,48,48))

    # Background
    bg_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(game.screen, bg_color, bg_rect, border_radius=max(1, height//2))

    # Progress
    progress_width = 0
    try:
        progress_width = int((value / float(max_value)) * width) if max_value else 0
    except Exception:
        progress_width = 0

    if progress_width > 0:
        progress_rect = pygame.Rect(x, y, progress_width, height)
        pygame.draw.rect(game.screen, color, progress_rect, border_radius=max(1, height//2))

    # Border
    pygame.draw.rect(game.screen, (255,255,255), bg_rect, 2, border_radius=max(1, height//2))
