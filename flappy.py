"""Flappy Mango: fly Mango through the gaps between the crows' trees.

Controls: SPACE / UP / click / tap to flap. ESC or the Back button returns to the hub.
"""
import random
import time

import pygame

from config import ACCENT, BLACK, ORANGE, RED, SCREEN_HEIGHT, SCREEN_WIDTH, SOFT, WHITE
from ui_helpers import BACK_BUTTON, blit_text, draw_back_button, draw_message_panel, glass_panel, pill

GRAVITY = 0.75
FLAP_STRENGTH = -13
TREE_WIDTH = 70
TREE_SPEED = 3
TREE_GAP = 220
SPAWN_EVERY = 150      # frames between trees
MANGO_X = 150
SPRITE_SIZE = (90, 90)


def gap_center():
    """Where the next gap between trees is, vertically."""
    return random.randint(150, SCREEN_HEIGHT - 250)


def make_tree(game):
    """A pair of trees (top and bottom) with a gap Mango has to fly through."""
    center = gap_center()
    top_h = max(8, center - TREE_GAP // 2)
    bottom_h = max(8, SCREEN_HEIGHT - center - TREE_GAP // 2)
    tree = {"x": SCREEN_WIDTH, "center": center, "top_h": top_h, "bottom_h": bottom_h, "scored": False}
    if game.tree_texture:
        # scaled once per tree, not every frame
        tree["top_img"] = pygame.transform.smoothscale(game.tree_texture, (TREE_WIDTH, top_h))
        tree["bottom_img"] = pygame.transform.flip(
            pygame.transform.smoothscale(game.tree_texture, (TREE_WIDTH, bottom_h)), False, True
        )
    return tree


def tree_rects(tree):
    top = pygame.Rect(tree["x"], 0, TREE_WIDTH, tree["top_h"])
    bottom = pygame.Rect(tree["x"], SCREEN_HEIGHT - tree["bottom_h"], TREE_WIDTH, tree["bottom_h"])
    return top, bottom


def draw_crow(screen, x, y, facing_up):
    """A little crow head perched on the end of a tree."""
    beak_dir = -1 if facing_up else 1
    pygame.draw.circle(screen, BLACK, (x + 35, y), 12)
    pygame.draw.polygon(screen, (255, 140, 0), [(x + 35, y + 5 * beak_dir), (x + 30, y + 12 * beak_dir), (x + 40, y + 12 * beak_dir)])
    pygame.draw.circle(screen, WHITE, (x + 32, y + 2 * beak_dir), 3)
    pygame.draw.circle(screen, BLACK, (x + 32, y + 2 * beak_dir), 2)


def draw_tree(game, tree):
    top, bottom = tree_rects(tree)
    if "top_img" in tree:
        game.screen.blit(tree["top_img"], top)
        game.screen.blit(tree["bottom_img"], bottom)
    else:
        pygame.draw.rect(game.screen, (101, 67, 33), top, border_radius=12)
        pygame.draw.rect(game.screen, (101, 67, 33), bottom, border_radius=12)
    draw_crow(game.screen, tree["x"], top.bottom - 15, facing_up=True)
    draw_crow(game.screen, tree["x"], bottom.top + 15, facing_up=False)


async def play_flappy_mango(game):
    frames = [game.mango_sprites.get("flying"), game.mango_sprites.get("flying2")]
    frames = [pygame.transform.smoothscale(f, SPRITE_SIZE) for f in frames if f]
    shadow = pygame.Surface((60, 30), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 40), shadow.get_rect())

    def reset():
        game.effects.clear()
        game.particle_system.clear()
        return {"y": SCREEN_HEIGHT // 2, "velocity": 0.0, "trees": [], "timer": 0, "score": 0,
                "started": False, "over": False, "over_at": 0.0, "flap_at": 0.0}

    s = reset()

    def flap():
        s["started"] = True
        s["velocity"] = FLAP_STRENGTH
        s["flap_at"] = time.time()
        game.audio.play_sfx("flap")

    def crash():
        s["over"] = True
        s["over_at"] = time.time()
        game.audio.play_sfx("thump")
        game.effects.shake(10, 0.4)
        if s["score"] > 0:
            # recorded once per crash
            game.save_score(s["score"])
            game.mango_state["happiness"] = min(100, game.mango_state["happiness"] + min(25, s["score"] * 2))
            game.save_state()

    def draw():
        game.draw_background("flappy")
        for tree in s["trees"]:
            draw_tree(game, tree)

        game.screen.blit(shadow, shadow.get_rect(center=(MANGO_X + 4, int(s["y"]) + 14)))
        if frames:
            flapping = time.time() - s["flap_at"] < 0.25 and len(frames) > 1
            sprite = frames[1] if flapping else frames[0]
            game.screen.blit(sprite, sprite.get_rect(center=(MANGO_X, int(s["y"]))))
        else:
            pygame.draw.circle(game.screen, ORANGE, (MANGO_X, int(s["y"])), 18)

        board = pygame.Rect(SCREEN_WIDTH - 196, 16, 176, 76)
        glass_panel(game.screen, board, radius=20, alpha=175)
        blit_text(game.screen, game.title_font, str(s["score"]), WHITE, midleft=(board.x + 20, board.centery))
        blit_text(game.screen, game.small_font, "SCORE", ACCENT, shadow=False, topright=(board.right - 18, board.y + 16))
        blit_text(game.screen, game.small_font, f"Best {game.high_score}", SOFT, shadow=False,
                  bottomright=(board.right - 18, board.bottom - 14))
        game.effects.draw(game.screen)

        draw_back_button(game)
        if not s["started"]:
            draw_message_panel(game, "Flappy Mango", ["Dodge the crows' trees!", "Tap or press SPACE to start"])
        elif s["over"]:
            best = " - new best!" if s["score"] and s["score"] >= game.high_score else ""
            draw_message_panel(game, "Game over!", [f"You scored {s['score']}{best}", "Tap or press R to fly again"],
                               border=RED, size=(500, 220))
        else:
            pill(game.screen, game.small_font, "Tap or SPACE to flap", WHITE, alpha=140, bottomleft=(18, SCREEN_HEIGHT - 16))

    draw()
    await game.fade(fade_in=True)

    while game.running:
        for event in game.events():
            pressed = None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                pressed = "flap" if event.key in (pygame.K_SPACE, pygame.K_UP) else "restart" if event.key == pygame.K_r else None
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if BACK_BUTTON.collidepoint(event.pos):
                    game.audio.play_sfx("button")
                    return
                pressed = "flap"

            if s["over"]:
                # short pause so a frantic last flap doesn't instantly restart
                if pressed and time.time() - s["over_at"] > 0.6:
                    game.audio.play_sfx("button")
                    s = reset()
            elif pressed == "flap":
                flap()

        if s["started"] and not s["over"]:
            s["velocity"] += GRAVITY
            s["y"] += s["velocity"]

            s["timer"] += 1
            if s["timer"] >= SPAWN_EVERY:
                s["trees"].append(make_tree(game))
                s["timer"] = 0

            mango = pygame.Rect(MANGO_X - 15, int(s["y"]) - 15, 30, 30)
            for tree in s["trees"]:
                tree["x"] -= TREE_SPEED
                if not tree["scored"] and tree["x"] + TREE_WIDTH < MANGO_X:
                    tree["scored"] = True
                    s["score"] += 1
                    game.effects.float_text(game.large_font, "+1", (MANGO_X + 30, int(s["y"]) - 40), ACCENT)
            s["trees"] = [t for t in s["trees"] if t["x"] > -TREE_WIDTH]

            hit_tree = any(mango.colliderect(r) for t in s["trees"] for r in tree_rects(t))
            if hit_tree or s["y"] >= SCREEN_HEIGHT - 60 or s["y"] <= -150:
                crash()

        draw()
        await game.next_frame()
