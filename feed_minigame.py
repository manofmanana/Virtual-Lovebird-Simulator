"""Feed mini-game: move Mango to catch 20 falling seeds and fill his tummy.

Controls: LEFT/RIGHT arrows, or move the mouse / drag a finger. Seeds that hit
the ground cost a point.
"""
import os
import random

import pygame

from assets import fit_sprite, load_image
from config import ACCENT, FPS, SCREEN_HEIGHT, SCREEN_WIDTH, SPRITES, WHITE
from ui_helpers import BACK_BUTTON, blit_text, draw_back_button, draw_message_panel, draw_modern_progress_bar, glass_panel

TARGET = 20
MANGO_SIZE = (110, 88)
MANGO_SPEED = 420           # px per second with the arrow keys
FOLLOW_SPEED = 1000         # px per second when following the mouse / a finger
SEED_SIZE = (28, 28)
GROUND_H = 44

# Difficulty ramps up as Mango fills up: seeds fall faster and come more often
SEED_SPEED = (150, 210)     # px per second, at the start
SEED_SPEEDUP = 7            # extra px per second for every seed caught
SPAWN_EVERY = (1.3, 0.55)   # seconds between seeds: at the start -> near the end


def spawn_delay(caught):
    """Seconds until the next seed: shrinks from SPAWN_EVERY[0] to SPAWN_EVERY[1] as Mango fills up."""
    start, end = SPAWN_EVERY
    return start + (end - start) * min(1.0, caught / TARGET)


def seed_speed(caught, roll=None):
    """How fast a new seed falls (px/s); roll in 0..1 picks within SEED_SPEED (random if None)."""
    low, high = SEED_SPEED
    roll = random.random() if roll is None else roll
    return low + (high - low) * roll + SEED_SPEEDUP * caught


def _ground():
    """A strip of simple brown pixel-art dirt."""
    tile = pygame.Surface((8, 8))
    tile.fill((101, 67, 33))
    for pos, color in (((1, 1), (90, 50, 30)), ((2, 3), (120, 80, 50)), ((5, 2), (110, 70, 40))):
        tile.set_at(pos, color)
    ground = pygame.Surface((SCREEN_WIDTH, GROUND_H))
    for x in range(0, SCREEN_WIDTH, 8):
        for y in range(0, GROUND_H, 8):
            ground.blit(tile, (x, y))
    return ground


def _sprite(name, size):
    image = load_image(os.path.join(SPRITES, name))
    return fit_sprite(image, size) if image else None


async def play_feed_minigame(game):
    mango_still = _sprite("mango_still.png", MANGO_SIZE)
    mango_moving = _sprite("mango_moving.png", MANGO_SIZE)
    seed_image = _sprite("seed.png", SEED_SIZE)
    ground = _ground()
    ground_y = SCREEN_HEIGHT - GROUND_H
    mango_y = SCREEN_HEIGHT - 120

    def reset():
        game.effects.clear()
        game.particle_system.clear()
        return {"x": SCREEN_WIDTH / 2, "target_x": None, "seeds": [], "spawn_in": 0.0,
                "caught": 0, "started": False, "done": False, "moving": False}

    s = reset()

    def draw():
        game.draw_background("feed")
        game.screen.blit(ground, (0, ground_y))
        for seed in s["seeds"]:
            if seed_image:
                game.screen.blit(seed_image, seed_image.get_rect(center=(int(seed["x"]), int(seed["y"]))))
            else:
                pygame.draw.circle(game.screen, (210, 180, 140), (int(seed["x"]), int(seed["y"])), 12)

        # Mango's "still" pose is drawn mid-flight and his "moving" pose while he waits
        sprite = mango_still if s["moving"] else mango_moving
        if sprite:
            game.screen.blit(sprite, sprite.get_rect(center=(int(s["x"]), mango_y)))
        else:
            pygame.draw.ellipse(game.screen, (255, 152, 0), pygame.Rect(0, 0, *MANGO_SIZE).move(int(s["x"]) - 55, mango_y - 44))

        # progress toward a full tummy
        hud = pygame.Rect(SCREEN_WIDTH // 2 - 170, 16, 340, 56)
        glass_panel(game.screen, hud, radius=20, alpha=175)
        blit_text(game.screen, game.small_font, "SEEDS", ACCENT, shadow=False, midleft=(hud.x + 18, hud.centery))
        draw_modern_progress_bar(game, hud.x + 84, hud.centery - 7, 170, 14, s["caught"], TARGET, (102, 200, 92))
        blit_text(game.screen, game.font, f"{s['caught']}/{TARGET}", WHITE, shadow=False, midright=(hud.right - 16, hud.centery))
        game.particle_system.draw(game.screen)
        game.effects.draw(game.screen)

        draw_back_button(game)
        if not s["started"]:
            draw_message_panel(game, "Feed Mango", [
                f"Catch {TARGET} seeds - they speed up!", "Drag your finger, move the mouse, or use the arrows",
                "Tap or press SPACE to start"], size=(560, 230))
        elif s["done"]:
            draw_message_panel(game, "Mango is full!", ["Yum! That hit the spot.", "Tap or press R to play again"])

    draw()
    await game.fade(fade_in=True)

    while game.running:
        dt = 1.0 / FPS
        for event in game.events():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if event.key == pygame.K_SPACE and not s["started"]:
                    s["started"] = True
                elif event.key == pygame.K_r and s["done"]:
                    s = reset()
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    s["target_x"] = None
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if BACK_BUTTON.collidepoint(event.pos):
                    game.audio.play_sfx("button")
                    return
                if not s["started"]:
                    s["started"] = True
                elif s["done"]:
                    s = reset()
                    s["started"] = True
                s["target_x"] = event.pos[0]
            elif event.type == pygame.MOUSEMOTION and s["started"]:
                s["target_x"] = event.pos[0]

        # Move: arrow keys take priority, otherwise glide toward the pointer
        previous_x = s["x"]
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            s["x"] -= MANGO_SPEED * dt
        elif keys[pygame.K_RIGHT]:
            s["x"] += MANGO_SPEED * dt
        elif s["target_x"] is not None:
            reach = FOLLOW_SPEED * dt
            s["x"] += max(-reach, min(reach, s["target_x"] - s["x"]))
        half = MANGO_SIZE[0] // 2
        s["x"] = max(half, min(SCREEN_WIDTH - half, s["x"]))
        s["moving"] = abs(s["x"] - previous_x) > 0.5

        if s["started"] and not s["done"]:
            s["spawn_in"] -= dt
            if s["spawn_in"] <= 0:
                s["spawn_in"] = spawn_delay(s["caught"])
                s["seeds"].append({"x": random.randint(20, SCREEN_WIDTH - 20), "y": -10.0,
                                   "speed": seed_speed(s["caught"])})

            mango = pygame.Rect(0, 0, *MANGO_SIZE)
            mango.center = (int(s["x"]), mango_y)
            for seed in s["seeds"][:]:
                seed["y"] += seed["speed"] * dt
                seed_rect = pygame.Rect(0, 0, *SEED_SIZE)
                seed_rect.center = (int(seed["x"]), int(seed["y"]))
                if seed_rect.colliderect(mango):
                    s["caught"] += 1
                    s["seeds"].remove(seed)
                    game.audio.play_sfx("chirp")
                    game.particle_system.add_button_effect(seed_rect.centerx, seed_rect.centery, "feed")
                    game.effects.float_text(game.large_font, "+1", (seed_rect.centerx, mango.top - 10), (140, 230, 120))
                elif seed["y"] >= ground_y:
                    if s["caught"] > 0:
                        game.effects.float_text(game.large_font, "-1", (seed_rect.centerx, ground_y - 10), (255, 110, 100))
                    s["caught"] = max(0, s["caught"] - 1)
                    s["seeds"].remove(seed)

            if s["caught"] >= TARGET:
                s["done"] = True
                s["seeds"].clear()
                game.mango_state["hunger"] = 100
                game.save_state()
                game.show_message("Mango is full!")
                game.audio.play_sfx("thump")

        game.particle_system.update(dt)
        draw()
        await game.next_frame()
