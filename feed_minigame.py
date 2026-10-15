"""Feed mini-game: move Mango to catch 20 falling seeds and fill his tummy.

Controls: LEFT/RIGHT arrows, or move the mouse / drag a finger. Seeds that hit
the ground cost a point.
"""
import os
import random

import pygame

from assets import fit_sprite, load_image
from config import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, SPRITES
from ui_helpers import BACK_BUTTON, draw_back_button, draw_message_panel

TARGET = 20
MANGO_SIZE = (110, 88)
MANGO_SPEED = 180         # px per second
SEED_SIZE = (28, 28)
SPAWN_EVERY = 3.0         # seconds
GROUND_H = 44


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

        # progress bar
        bar = pygame.Rect(SCREEN_WIDTH // 2 - 110, 22, 220, 16)
        pygame.draw.rect(game.screen, (40, 40, 40), bar, border_radius=8)
        filled = int(bar.w * min(1, s["caught"] / TARGET))
        if filled:
            pygame.draw.rect(game.screen, (100, 200, 100), (bar.x, bar.y, filled, bar.h), border_radius=8)
        pygame.draw.rect(game.screen, (255, 255, 255), bar, 2, border_radius=8)
        label = game.font.render(f"Seeds: {s['caught']}/{TARGET}", True, (255, 255, 255))
        backing = label.get_rect(midleft=(bar.right + 12, bar.centery)).inflate(12, 6)
        pygame.draw.rect(game.screen, (0, 0, 0), backing, border_radius=8)
        game.screen.blit(label, label.get_rect(center=backing.center))

        draw_back_button(game)
        if not s["started"]:
            draw_message_panel(game, "Feed Mango", [
                "Catch the falling seeds!", "Arrow keys, or move the mouse / your finger",
                "Press SPACE or click to start"], size=(520, 220))
        elif s["done"]:
            draw_message_panel(game, "Mango is full!", ["Congrats! Mango had fun!", "Click or press R to play again"])

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
        step = MANGO_SPEED * dt
        if keys[pygame.K_LEFT]:
            s["x"] -= step
        elif keys[pygame.K_RIGHT]:
            s["x"] += step
        elif s["target_x"] is not None:
            # following a finger needs to be a bit quicker than the arrow keys
            gap = s["target_x"] - s["x"]
            s["x"] += max(-step * 3, min(step * 3, gap))
        half = MANGO_SIZE[0] // 2
        s["x"] = max(half, min(SCREEN_WIDTH - half, s["x"]))
        s["moving"] = abs(s["x"] - previous_x) > 0.5

        if s["started"] and not s["done"]:
            s["spawn_in"] -= dt
            if s["spawn_in"] <= 0:
                s["spawn_in"] = SPAWN_EVERY
                s["seeds"].append({"x": random.randint(20, SCREEN_WIDTH - 20), "y": -10.0,
                                   "speed": random.uniform(25, 56)})

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
                elif seed["y"] >= ground_y:
                    s["caught"] = max(0, s["caught"] - 1)
                    s["seeds"].remove(seed)

            if s["caught"] >= TARGET:
                s["done"] = True
                s["seeds"].clear()
                game.mango_state["hunger"] = 100
                game.save_state()
                game.show_message("Mango is full!")
                game.audio.play_sfx("thump")

        draw()
        await game.next_frame()
