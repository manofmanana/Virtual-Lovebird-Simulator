"""Tickle mini-game: Mango zooms around the room; click or tap him 12 times.

Finishing makes Mango happier and calms down any misbehaving.
"""
import math
import os
import random

import pygame

from assets import load_image
from config import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, SPRITES
from ui_helpers import BACK_BUTTON, draw_back_button, draw_message_panel

TARGET = 12
MANGO_SIZE = (120, 96)
SPEED = 480.0  # px per second
ERIC_SIZE = (400, 600)


async def play_tickle_minigame(game):
    flying = game.mango_sprites.get("still")
    flying = pygame.transform.smoothscale(flying, MANGO_SIZE) if flying else None
    eric = load_image(os.path.join(SPRITES, "ericv.png"))
    eric = pygame.transform.smoothscale(eric, ERIC_SIZE) if eric else None  # a cameo from a friend

    def reset():
        return {"x": SCREEN_WIDTH / 2, "y": SCREEN_HEIGHT / 2, "vx": 0.0, "vy": 0.0,
                "tickles": 0, "started": False, "done": False}

    s = reset()

    def mango_rect():
        rect = pygame.Rect(0, 0, *MANGO_SIZE)
        rect.center = (int(s["x"]), int(s["y"]))
        return rect

    def draw():
        game.draw_background("hub")
        title = game.title_font.render("Tickle Mango!", True, (255, 255, 255))
        game.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 60)))

        if s["started"] and not s["done"] and flying:
            sprite = flying
        else:
            mood_sprite = game.mango_sprites.get(game.get_mango_mood()) or game.mango_sprites.get("idle")
            sprite = pygame.transform.smoothscale(mood_sprite, MANGO_SIZE) if mood_sprite else None
        if sprite:
            game.screen.blit(sprite, mango_rect())
        else:
            pygame.draw.ellipse(game.screen, (255, 152, 0), mango_rect())

        game.particle_system.draw(game.screen)
        draw_back_button(game)

        if not s["started"]:
            if eric:
                game.screen.blit(eric, eric.get_rect(bottomright=(SCREEN_WIDTH + 40, SCREEN_HEIGHT + 60)))
            draw_message_panel(game, "Tickle Mango!", [
                "Click or tap Mango to tickle him!", "He'll fly around once you start.",
                "Press SPACE or click to start"], size=(500, 220))
        elif s["done"]:
            draw_message_panel(game, "Hee hee!", ["Congrats! Mango had fun!", "Click or press R to play again"])
        else:
            count = game.font.render(f"Tickles: {s['tickles']}/{TARGET}", True, (255, 255, 255))
            box = count.get_rect(topright=(SCREEN_WIDTH - 20, 20)).inflate(16, 8)
            pygame.draw.rect(game.screen, (0, 0, 0), box, border_radius=10)
            game.screen.blit(count, count.get_rect(center=box.center))

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
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if BACK_BUTTON.collidepoint(event.pos):
                    game.audio.play_sfx("button")
                    return
                if not s["started"]:
                    s["started"] = True
                elif s["done"]:
                    s = reset()
                    s["started"] = True
                elif mango_rect().collidepoint(event.pos):
                    s["tickles"] += 1
                    game.particle_system.add_button_effect(*event.pos, "tickle")
                    game.audio.play_sfx("chirp")
                    if s["tickles"] >= TARGET:
                        s["done"] = True
                        game.mango_state["happiness"] = min(100, game.mango_state["happiness"] + 20)
                        game.misbehavior_count = max(0, game.misbehavior_count - 2)
                        game.save_state()
                        game.show_message("Mango is giggling!")

        if s["started"] and not s["done"]:
            # change direction often so Mango zips around unpredictably
            if random.random() < 0.08:
                angle = random.uniform(0, 2 * math.pi)
                speed = SPEED * random.uniform(0.7, 1.4)
                s["vx"], s["vy"] = math.cos(angle) * speed, math.sin(angle) * speed
            half_w, half_h = MANGO_SIZE[0] / 2, MANGO_SIZE[1] / 2
            s["x"] = max(half_w, min(SCREEN_WIDTH - half_w, s["x"] + s["vx"] * dt))
            s["y"] = max(half_h, min(SCREEN_HEIGHT - half_h, s["y"] + s["vy"] * dt))

        game.particle_system.update(dt)
        draw()
        await game.next_frame()
