"""Small drawing helpers shared by the hub and the mini-games."""
import pygame

BACK_BUTTON = pygame.Rect(16, 16, 120, 40)


def draw_modern_button(game, rect, text, color, hover_color, text_color=(255, 255, 255), hover=False):
    """A rounded button with a drop shadow; brighter border when hovered."""
    pygame.draw.rect(game.screen, (0, 0, 0), rect.move(3, 3), border_radius=8)
    pygame.draw.rect(game.screen, hover_color if hover else color, rect, border_radius=8)
    pygame.draw.rect(game.screen, (255, 255, 255) if hover else (200, 200, 200), rect, 2, border_radius=8)
    label = game.small_font.render(text, True, text_color)
    game.screen.blit(label, label.get_rect(center=rect.center))
    return rect


def draw_modern_progress_bar(game, x, y, width, height, value, max_value, color, bg_color=(48, 48, 48)):
    """A rounded bar filled to value/max_value."""
    radius = max(1, height // 2)
    background = pygame.Rect(x, y, width, height)
    pygame.draw.rect(game.screen, bg_color, background, border_radius=radius)
    filled = int(width * value / max_value) if max_value else 0
    if filled > 0:
        pygame.draw.rect(game.screen, color, (x, y, filled, height), border_radius=radius)
    pygame.draw.rect(game.screen, (255, 255, 255), background, 2, border_radius=radius)


def draw_back_button(game):
    """'Back to hub' button for the mini-games (phones have no Escape key)."""
    hover = BACK_BUTTON.collidepoint(pygame.mouse.get_pos())
    return draw_modern_button(game, BACK_BUTTON, "< Back to hub", (40, 40, 40), (70, 70, 70), hover=hover)


def draw_message_panel(game, title, lines, border=(255, 215, 0), size=(480, 200)):
    """A white card in the middle of the screen with a title and a few lines of text."""
    panel = pygame.Rect(0, 0, *size)
    panel.center = (game.screen.get_width() // 2, game.screen.get_height() // 2)
    pygame.draw.rect(game.screen, (0, 0, 0), panel.move(4, 4), border_radius=20)
    pygame.draw.rect(game.screen, (250, 250, 250), panel, border_radius=20)
    pygame.draw.rect(game.screen, border, panel, 4, border_radius=20)
    heading = game.title_font.render(title, True, (20, 20, 20))
    game.screen.blit(heading, heading.get_rect(center=(panel.centerx, panel.y + 45)))
    for i, line in enumerate(lines):
        text = game.font.render(line, True, (50, 50, 50))
        game.screen.blit(text, text.get_rect(center=(panel.centerx, panel.y + 95 + i * 32)))
    return panel
