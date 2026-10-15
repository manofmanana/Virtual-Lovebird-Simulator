"""The main hub screen: Mango's cage, care buttons, stats, and settings."""
import math
import random
import time

import pygame

from config import (
    BLUE, DARK_GRAY, GOLD, GREEN, IS_WEB, ORANGE, PINK, PURPLE, RED, SCREEN_HEIGHT, SCREEN_WIDTH,
    SILVER, WHITE, YELLOW,
)
from ui_helpers import draw_modern_button, draw_modern_progress_bar

CAGE = pygame.Rect((SCREEN_WIDTH - 280) // 2, 120, 280, 280)
HUB_SPRITE_SIZE = 140
BUTTON_W, BUTTON_H, BUTTON_GAP = 140, 48, 18
FLAPPY_RECT = pygame.Rect(SCREEN_WIDTH - 200, 20, 150, 60)
FULLSCREEN_RECT = pygame.Rect(SCREEN_WIDTH - 40, 12, 28, 20)
AUDIO_BUTTON = pygame.Rect(12, 8, 100, 28)
STATS_RECT = pygame.Rect(CAGE.centerx - 360, CAGE.bottom + 28, 720, 160)

# (label, method name, color, hover color, message when it works, message when it can't)
ACTIONS = [
    ("Feed", "play_feed_minigame", GREEN, (0, 200, 0), None, None),
    ("Bathe", "bathe_mango", BLUE, (0, 100, 200), "Splish splash! Mango is clean", "Mango is already squeaky clean"),
    ("Play", "play_with_mango", YELLOW, (200, 150, 0), "Mango loved playing!", "Mango is too tired to play"),
    ("Rest", "rest_mango", PINK, (200, 100, 150), "Mango had a nice nap", "Mango isn't sleepy"),
    ("Medicine", "give_medicine", RED, (200, 0, 0), None, None),
    ("Tickle", "play_tickle_minigame", PURPLE, (100, 0, 100), None, None),
]

STATS = [
    ("Hunger", "hunger", (255, 152, 0)),
    ("Happiness", "happiness", (76, 175, 80)),
    ("Cleanliness", "cleanliness", (33, 150, 243)),
    ("Energy", "energy", (255, 193, 7)),
    ("Health", "health", (244, 67, 54)),
]

SLIDERS = ("master", "music", "sfx")


def action_buttons():
    """[(rect, action)] for the two stacks of three buttons beside the cage."""
    stack_h = 3 * BUTTON_H + 2 * BUTTON_GAP
    top = CAGE.y + (CAGE.h - stack_h) // 2
    left_x = CAGE.x - 20 - BUTTON_W - 10
    right_x = CAGE.right + 20 + 10
    buttons = []
    for i, action in enumerate(ACTIONS):
        x = left_x if i < 3 else right_x
        y = top + (i % 3) * (BUTTON_H + BUTTON_GAP)
        buttons.append((pygame.Rect(x, y, BUTTON_W, BUTTON_H), action))
    return buttons


def slider_rect(index):
    return pygame.Rect(AUDIO_BUTTON.x + 8, AUDIO_BUTTON.bottom + 28 + index * 40, AUDIO_BUTTON.w + 24, 24)


def _panel(game, rect, alpha=160):
    shade = pygame.Surface(rect.size, pygame.SRCALPHA)
    shade.fill((0, 0, 0, alpha))
    game.screen.blit(shade, rect.topleft)


def draw_cage_and_mango(game):
    screen = game.screen
    _panel(game, CAGE.move(5, 5), 100)  # shadow
    _panel(game, CAGE, 140)             # dark interior
    pygame.draw.rect(screen, GOLD, CAGE.inflate(16, 16), 6, border_radius=20)

    # A button press briefly shows a matching reaction sprite; otherwise show the mood
    override = game.particle_system.get_current_sprite(None)
    mood = override.replace("mango_", "") if override else game.get_mango_mood()
    sprite = game.mango_sprites.get(mood) or game.mango_sprites.get("idle")

    pulse = 1.0 + 0.18 * math.sin(game.animation_time * 3.2)
    bob = int(math.sin(game.animation_time * 3.0) * 4)
    size = int(HUB_SPRITE_SIZE * pulse)
    center = (CAGE.centerx, CAGE.centery + bob)
    if sprite:
        scaled = pygame.transform.smoothscale(sprite, (size, size))
        screen.blit(scaled, scaled.get_rect(center=center))
    else:
        pygame.draw.ellipse(screen, ORANGE, pygame.Rect(0, 0, size, size).move(center[0] - size // 2, center[1] - size // 2))
    game._hub_mango_rect = pygame.Rect(0, 0, HUB_SPRITE_SIZE + 36, HUB_SPRITE_SIZE + 36)
    game._hub_mango_rect.center = CAGE.center


def draw_stats(game):
    screen = game.screen
    _panel(game, STATS_RECT)
    pygame.draw.rect(screen, GOLD, STATS_RECT.inflate(6, 6), 3, border_radius=8)
    pygame.draw.rect(screen, SILVER, STATS_RECT, 2, border_radius=6)

    title = game.small_font.render(f"Mango Stats  ·  Age {game.mango_state['age']} day{'s' if game.mango_state['age'] != 1 else ''}", True, WHITE)
    screen.blit(title, title.get_rect(midtop=(STATS_RECT.centerx, STATS_RECT.y + 6)))

    y = STATS_RECT.y + 14 + title.get_height()
    bar_h, spacing = 14, 12
    for label, key, color in STATS:
        text = game.small_font.render(label, True, WHITE)
        screen.blit(text, (STATS_RECT.x + 12, y + (bar_h - text.get_height()) // 2))
        draw_modern_progress_bar(game, STATS_RECT.x + 120, y, STATS_RECT.w - 160, bar_h, game.mango_state[key], 100, color, DARK_GRAY)
        y += bar_h + spacing


def draw_audio_menu(game):
    screen = game.screen
    pygame.draw.rect(screen, (30, 30, 30), AUDIO_BUTTON, border_radius=8)
    pygame.draw.rect(screen, WHITE, AUDIO_BUTTON, 2, border_radius=8)
    label = game.small_font.render("Audio", True, WHITE)
    screen.blit(label, label.get_rect(midleft=(AUDIO_BUTTON.x + 12, AUDIO_BUTTON.centery)))
    if not getattr(game, "_audio_menu_open", False):
        return

    menu = pygame.Rect(AUDIO_BUTTON.x, AUDIO_BUTTON.bottom + 10, AUDIO_BUTTON.w + 40, 130)
    pygame.draw.rect(screen, (25, 25, 25), menu, border_radius=8)
    pygame.draw.rect(screen, WHITE, menu, 1, border_radius=8)
    volumes = game.audio.volumes()
    for i, key in enumerate(SLIDERS):
        track = slider_rect(i)
        bar = pygame.Rect(track.x, track.y + 6, track.w, 8)
        filled = int(volumes[key] * track.w)
        pygame.draw.rect(screen, DARK_GRAY, bar, border_radius=4)
        pygame.draw.rect(screen, GREEN, (bar.x, bar.y, filled, bar.h), border_radius=4)
        pygame.draw.rect(screen, WHITE, (track.x + filled - 5, track.y + 2, 10, 14), border_radius=4)
        text = game.tiny_font.render(key.upper() if key == "sfx" else key.capitalize(), True, WHITE)
        screen.blit(text, (track.x, track.y - 10))


def draw_messages(game):
    """Short-lived feedback messages, stacked above the stats panel."""
    for i, (text, _) in enumerate(reversed(game.hud_messages[-3:])):
        surface = game.font.render(text, True, WHITE)
        box = surface.get_rect(center=(SCREEN_WIDTH // 2, CAGE.bottom - 24 - i * 34)).inflate(24, 10)
        pygame.draw.rect(game.screen, (20, 20, 20), box, border_radius=14)
        pygame.draw.rect(game.screen, GOLD, box, 2, border_radius=14)
        game.screen.blit(surface, surface.get_rect(center=box.center))


def draw_home_screen(game):
    screen = game.screen
    game.draw_background("hub")

    title = game.title_font.render("Mango: The Virtual Lovebird", True, WHITE)
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 40)))

    draw_cage_and_mango(game)

    mouse = pygame.mouse.get_pos()
    for rect, (label, _, color, hover_color, _, _) in action_buttons():
        draw_modern_button(game, rect, label, color, hover_color, WHITE, rect.collidepoint(mouse))

    draw_modern_button(game, FLAPPY_RECT, "Flappy Mango", ORANGE, GOLD, WHITE, FLAPPY_RECT.collidepoint(mouse))
    best = game.font.render(f"High Score: {game.high_score}", True, WHITE)
    screen.blit(best, best.get_rect(midtop=(FLAPPY_RECT.centerx, FLAPPY_RECT.bottom + 6)))

    if not IS_WEB:
        pygame.draw.rect(screen, (28, 28, 28), FULLSCREEN_RECT, border_radius=6)
        pygame.draw.rect(screen, WHITE, FULLSCREEN_RECT, 1, border_radius=6)
        r = FULLSCREEN_RECT
        pygame.draw.lines(screen, WHITE, False, [(r.left + 4, r.top + 8), (r.left + 4, r.top + 4), (r.left + 8, r.top + 4)])
        pygame.draw.lines(screen, WHITE, False, [(r.right - 5, r.bottom - 8), (r.right - 5, r.bottom - 5), (r.right - 8, r.bottom - 5)])

    draw_stats(game)

    fact = game.api_handler.get_bird_fact()
    if fact:
        pill = pygame.Rect((SCREEN_WIDTH - 480) // 2, 620, 480, 40)
        pygame.draw.rect(screen, GOLD, pill, border_radius=20)
        pygame.draw.rect(screen, WHITE, pill, 2, border_radius=20)
        text = game.small_font.render(fact, True, (0, 0, 0))
        screen.blit(text, text.get_rect(center=pill.center))

    game.particle_system.draw(screen)
    draw_messages(game)
    draw_audio_menu(game)

    if time.time() < game.flash_until:
        flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        flash.fill(WHITE)
        flash.set_alpha(70)
        screen.blit(flash, (0, 0))

    # Every so often Mango chirps on his own so the room feels alive
    now = time.time()
    if now - getattr(game, "_last_chirp", 0) > 6 and random.random() < 0.02:
        game.audio.play_sfx("chirp")
        game._last_chirp = now


def handle_click(game, pos):
    if AUDIO_BUTTON.collidepoint(pos):
        game._audio_menu_open = not getattr(game, "_audio_menu_open", False)
        game.audio.play_sfx("button")
        return

    if getattr(game, "_audio_menu_open", False):
        for i, key in enumerate(SLIDERS):
            if slider_rect(i).collidepoint(pos):
                game._dragging_slider = key
                handle_drag(game, pos)
                return

    for rect, (label, method, _, _, success, failure) in action_buttons():
        if rect.collidepoint(pos):
            game.particle_system.add_button_effect(rect.centerx, rect.centery, label.lower())
            game.particle_system.add_sprite_animation(label.lower())
            game.audio.play_sfx("button")
            worked = getattr(game, method)()
            if worked and success:
                game.show_message(success)
            elif not worked and failure:
                game.show_message(failure)
            return

    if FLAPPY_RECT.collidepoint(pos):
        game.audio.play_sfx("button")
        game.play_flappy_mango()
        return

    if not IS_WEB and FULLSCREEN_RECT.collidepoint(pos):
        game.toggle_fullscreen()
        return

    mango = getattr(game, "_hub_mango_rect", None)
    if mango and mango.collidepoint(pos):
        game.particle_system.add_button_effect(pos[0], pos[1], "tickle")
        game.particle_system.add_sprite_animation("tickle")
        game.audio.play_sfx("chirp")


def handle_drag(game, pos):
    key = getattr(game, "_dragging_slider", None)
    if key:
        track = slider_rect(SLIDERS.index(key))
        game.audio.set_volume(key, (pos[0] - track.x) / track.w)


def handle_release(game):
    if getattr(game, "_dragging_slider", None):
        game._dragging_slider = None
        game.save_settings()


def draw_game_over_screen(game):
    game.draw_gradient_background()
    panel = pygame.Rect(0, 0, 600, 360)
    panel.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    pygame.draw.rect(game.screen, (0, 0, 0), panel.move(5, 5), border_radius=25)
    pygame.draw.rect(game.screen, WHITE, panel, border_radius=25)

    lines = [
        (game.title_font, "Mango has flown away!", RED, 60),
        (game.font, "His health reached zero.", DARK_GRAY, 120),
        (game.font, f"He lived to {game.mango_state['age']} day{'s' if game.mango_state['age'] != 1 else ''} old.", DARK_GRAY, 155),
    ]
    for font, text, color, dy in lines:
        surface = font.render(text, True, color)
        game.screen.blit(surface, surface.get_rect(center=(panel.centerx, panel.y + dy)))

    sprite = game.mango_sprites.get("flying")
    if sprite:
        bob = int(math.sin(game.animation_time * 3) * 6)
        game.screen.blit(sprite, sprite.get_rect(center=(panel.centerx, panel.y + 230 + bob)))

    hint = game.font.render("Click anywhere to welcome a new Mango", True, BLUE)
    game.screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - 30)))
