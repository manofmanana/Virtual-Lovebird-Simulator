"""The main hub screen: Mango's cage, care buttons, stats, and settings."""
import math
import random
import time

import pygame

from config import (
    ACCENT, BLUE, GREEN, INK, IS_WEB, MUTED, ORANGE, PINK, PURPLE, RED, SCREEN_HEIGHT, SCREEN_WIDTH, SOFT, WHITE,
)
from ui_helpers import blit_text, draw_modern_button, draw_modern_progress_bar, draw_shadow, glass_panel, pill

CAGE = pygame.Rect((SCREEN_WIDTH - 280) // 2, 112, 280, 280)
HUB_SPRITE_SIZE = 140
BUTTON_W, BUTTON_H, BUTTON_GAP = 150, 52, 16
FLAPPY_RECT = pygame.Rect(SCREEN_WIDTH - 196, 22, 172, 56)
FULLSCREEN_RECT = pygame.Rect(SCREEN_WIDTH - 52, SCREEN_HEIGHT - 52, 36, 36)
AUDIO_BUTTON = pygame.Rect(16, 22, 104, 40)
STATS_RECT = pygame.Rect(CAGE.centerx - 340, CAGE.bottom + 26, 680, 182)

# (label, method name, color, message when it works, message when it can't)
ACTIONS = [
    ("Feed", "play_feed_minigame", GREEN, None, None),
    ("Bathe", "bathe_mango", BLUE, "Splish splash! Mango is clean", "Mango is already squeaky clean"),
    ("Play", "play_with_mango", (240, 170, 0), "Mango loved playing!", "Mango is too tired to play"),
    ("Rest", "rest_mango", PINK, "Mango had a nice nap", "Mango isn't sleepy"),
    ("Medicine", "give_medicine", RED, None, None),
    ("Tickle", "play_tickle_minigame", PURPLE, None, None),
]

STATS = [
    ("Hunger", "hunger", (255, 152, 0)),
    ("Happiness", "happiness", (102, 200, 92)),
    ("Cleanliness", "cleanliness", (64, 168, 255)),
    ("Energy", "energy", (255, 205, 40)),
    ("Health", "health", (244, 80, 70)),
]

SLIDERS = ("master", "music", "sfx")


def action_buttons():
    """[(rect, action)] for the two stacks of three buttons beside the cage."""
    stack_h = 3 * BUTTON_H + 2 * BUTTON_GAP
    top = CAGE.y + (CAGE.h - stack_h) // 2
    left_x = CAGE.x - 36 - BUTTON_W
    right_x = CAGE.right + 36
    buttons = []
    for i, action in enumerate(ACTIONS):
        x = left_x if i < 3 else right_x
        y = top + (i % 3) * (BUTTON_H + BUTTON_GAP)
        buttons.append((pygame.Rect(x, y, BUTTON_W, BUTTON_H), action))
    return buttons


def slider_rect(index):
    return pygame.Rect(AUDIO_BUTTON.x + 14, AUDIO_BUTTON.bottom + 40 + index * 42, 132, 24)


def draw_cage_and_mango(game):
    screen = game.screen
    glass_panel(screen, CAGE, radius=28, alpha=150, border=(255, 201, 60, 200))
    pygame.draw.rect(screen, ACCENT, CAGE, 3, border_radius=28)

    # A button press briefly shows a matching reaction sprite; otherwise show the mood
    override = game.particle_system.get_current_sprite(None)
    mood = override.replace("mango_", "") if override else game.get_mango_mood()
    sprite = game.mango_sprites.get(mood) or game.mango_sprites.get("idle")

    pulse = 1.0 + 0.06 * math.sin(game.animation_time * 3.2)
    bob = int(math.sin(game.animation_time * 2.4) * 6)
    size = int(HUB_SPRITE_SIZE * pulse)
    center = (CAGE.centerx, CAGE.centery + bob)

    # soft shadow under Mango that shrinks as he bobs up
    shadow = pygame.Surface((110 - bob * 2, 18), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
    screen.blit(shadow, shadow.get_rect(center=(CAGE.centerx, CAGE.centery + 78)))

    if sprite:
        scaled = pygame.transform.smoothscale(sprite, (size, size))
        screen.blit(scaled, scaled.get_rect(center=center))
    else:
        pygame.draw.ellipse(screen, ORANGE, pygame.Rect(0, 0, size, size).move(center[0] - size // 2, center[1] - size // 2))
    game._hub_mango_rect = pygame.Rect(0, 0, HUB_SPRITE_SIZE + 36, HUB_SPRITE_SIZE + 36)
    game._hub_mango_rect.center = CAGE.center


def draw_stats(game):
    screen = game.screen
    glass_panel(screen, STATS_RECT, radius=22, alpha=170)
    age = game.mango_state["age"]
    blit_text(screen, game.small_font, "MANGO'S STATS", ACCENT, shadow=False, topleft=(STATS_RECT.x + 22, STATS_RECT.y + 14))
    blit_text(screen, game.small_font, f"Age {age} day{'s' if age != 1 else ''}", SOFT, shadow=False,
              topright=(STATS_RECT.right - 22, STATS_RECT.y + 14))

    y = STATS_RECT.y + 46
    bar_x, bar_w, bar_h = STATS_RECT.x + 142, STATS_RECT.w - 214, 14
    previous = getattr(game, "_stat_targets", {})
    pulse = (math.sin(game.animation_time * 8) + 1) / 2
    for label, key, color in STATS:
        value = game.mango_state[key]
        shown = game.shown_stats.get(key, value)
        # stats that are getting dangerously low gently flash
        label_color = (255, 140 + int(60 * pulse), 130) if value <= 25 else WHITE
        blit_text(screen, game.font, label, label_color, shadow=False, midleft=(STATS_RECT.x + 22, y + bar_h // 2))
        draw_modern_progress_bar(game, bar_x, y, bar_w, bar_h, shown, 100, color)
        blit_text(screen, game.small_font, str(int(round(shown))), SOFT, shadow=False,
                  midright=(STATS_RECT.right - 22, y + bar_h // 2))
        # a stat jumped up: float the gain above its bar
        if key in previous and value - previous[key] >= 5:
            game.effects.float_text(game.small_font, f"+{value - previous[key]}",
                                    (bar_x + int(bar_w * value / 100), y - 4), color)
        y += bar_h + 15
    game._stat_targets = {key: game.mango_state[key] for _, key, _ in STATS}


def draw_audio_menu(game):
    screen = game.screen
    hover = AUDIO_BUTTON.collidepoint(pygame.mouse.get_pos())
    glass_panel(screen, AUDIO_BUTTON, radius=20, alpha=200 if hover else 160)
    blit_text(screen, game.small_font, "Sound", WHITE, shadow=False, center=AUDIO_BUTTON.center)
    if not getattr(game, "_audio_menu_open", False):
        return

    menu = pygame.Rect(AUDIO_BUTTON.x, AUDIO_BUTTON.bottom + 10, 160, 140)
    glass_panel(screen, menu, radius=16, alpha=220)
    volumes = game.audio.volumes()
    for i, key in enumerate(SLIDERS):
        track = slider_rect(i)
        blit_text(screen, game.tiny_font, key.upper() if key == "sfx" else key.capitalize(), SOFT, shadow=False,
                  bottomleft=(track.x, track.y + 4))
        bar = pygame.Rect(track.x, track.y + 8, track.w, 8)
        filled = int(volumes[key] * track.w)
        pygame.draw.rect(screen, (90, 80, 72), bar, border_radius=4)
        pygame.draw.rect(screen, GREEN, (bar.x, bar.y, max(8, filled), bar.h), border_radius=4)
        pygame.draw.circle(screen, WHITE, (track.x + filled, bar.centery), 8)


def draw_messages(game):
    """Toasts that slide in under the title and fade away."""
    now = time.time()
    for i, (message, until, shown_at) in enumerate(reversed(game.hud_messages[-2:])):
        eased = 1 - (1 - min(1, (now - shown_at) / 0.25)) ** 3
        fade = max(0.0, min(1, (until - now) / 0.35))
        rect = pill(game.screen, game.font, message, WHITE, alpha=int(215 * fade), pad=(24, 10),
                    midtop=(SCREEN_WIDTH // 2, int(64 + 14 * (1 - eased)) + i * 50))
        if fade > 0.3:
            pygame.draw.circle(game.screen, ACCENT, (rect.x + 13, rect.centery), 4)


def draw_home_screen(game):
    screen = game.screen
    game.draw_background("hub")

    blit_text(screen, game.title_font, "Mango: The Virtual Lovebird", WHITE, midtop=(SCREEN_WIDTH // 2, 14))

    draw_cage_and_mango(game)

    mouse = pygame.mouse.get_pos()
    for rect, (label, _, color, _, _) in action_buttons():
        draw_modern_button(game, rect, label, color, hover=rect.collidepoint(mouse))

    draw_modern_button(game, FLAPPY_RECT, "Flappy Mango", ORANGE, hover=FLAPPY_RECT.collidepoint(mouse))
    blit_text(screen, game.small_font, f"Best: {game.high_score}", WHITE, midtop=(FLAPPY_RECT.centerx, FLAPPY_RECT.bottom + 10))

    if not IS_WEB:
        glass_panel(screen, FULLSCREEN_RECT, radius=10, alpha=170)
        r = FULLSCREEN_RECT.inflate(-16, -16)
        for corner, dx, dy in ((r.topleft, 1, 1), (r.topright, -1, 1), (r.bottomleft, 1, -1), (r.bottomright, -1, -1)):
            pygame.draw.line(screen, WHITE, corner, (corner[0] + 6 * dx, corner[1]), 2)
            pygame.draw.line(screen, WHITE, corner, (corner[0], corner[1] + 6 * dy), 2)

    draw_stats(game)

    fact = game.api_handler.get_bird_fact()
    if fact:
        rect = pill(screen, game.small_font, f"Did you know?  {fact}", WHITE, alpha=170, pad=(22, 10),
                    midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 18))
        pygame.draw.circle(screen, ACCENT, (rect.x + 12, rect.centery), 3)

    game.particle_system.draw(screen)
    game.effects.draw(screen)
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
            if slider_rect(i).inflate(12, 12).collidepoint(pos):
                game._dragging_slider = key
                handle_drag(game, pos)
                return

    for rect, (label, method, _, success, failure) in action_buttons():
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
        game.effects.float_text(game.small_font, "chirp!", pos, ACCENT)
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
    panel = pygame.Rect(0, 0, 560, 380)
    panel.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    draw_shadow(game.screen, panel, radius=28, strength=150, spread=18, offset=(0, 12))
    pygame.draw.rect(game.screen, (253, 250, 244), panel, border_radius=28)

    age = game.mango_state["age"]
    blit_text(game.screen, game.title_font, "Mango has flown away", INK, shadow=False, center=(panel.centerx, panel.y + 56))
    blit_text(game.screen, game.font, "His health reached zero.", MUTED, shadow=False, center=(panel.centerx, panel.y + 104))
    blit_text(game.screen, game.font, f"He lived to {age} day{'s' if age != 1 else ''} old.", MUTED, shadow=False,
              center=(panel.centerx, panel.y + 136))

    sprite = game.mango_sprites.get("flying")
    if sprite:
        bob = int(math.sin(game.animation_time * 3) * 6)
        small = pygame.transform.smoothscale(sprite, (110, 110))
        game.screen.blit(small, small.get_rect(center=(panel.centerx, panel.y + 222 + bob)))

    button = pygame.Rect(0, 0, 300, 52)
    button.midbottom = (panel.centerx, panel.bottom - 26)
    draw_modern_button(game, button, "Welcome a new Mango", ORANGE, hover=button.collidepoint(pygame.mouse.get_pos()))
