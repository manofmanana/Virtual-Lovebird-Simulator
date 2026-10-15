"""
Mango: The Virtual Lovebird
A Tamagotchi-inspired virtual pet, in loving memory of my lovebird Mango.
CS50P final project.

Runs on the desktop (python project.py) and in the browser via pygbag (main.py).
"""
import asyncio
import os
import random
import time
from datetime import datetime

import pygame

import db
from api import APIHandler
from assets import load_backgrounds, load_image, load_mango_sprites
from audio import AudioManager
from config import (
    BLACK, DEFAULT_STATE, FPS, GRADIENT_END, GRADIENT_START, IS_WEB, NIGHT_END, NIGHT_START,
    SCREEN_HEIGHT, SCREEN_WIDTH, SPRITES,
)
from particle_effects import ParticleSystem


class GameState:
    TAMAGOTCHI_HUB = "tamagotchi_hub"
    FLAPPY_MANGO = "flappy_mango"
    FEED = "feed"
    TICKLE = "tickle"
    GAME_OVER = "game_over"


def new_mango_state():
    """Stats for a brand-new Mango."""
    return dict(DEFAULT_STATE, last_updated=datetime.now().isoformat())


def is_night_hour(hour):
    """Night runs from 7 p.m. to 5:59 a.m."""
    return hour < 6 or hour > 18


def clamp(value, low=0, high=100):
    return max(low, min(high, value))


class MangoTamagotchi:
    def __init__(self, db_path="db/mango.db"):
        pygame.init()
        # SCALED lets the desktop window be resized/fullscreened while the game
        # keeps drawing at 1000x700; the browser canvas is scaled by pygbag instead.
        flags = 0 if IS_WEB else pygame.SCALED
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        pygame.display.set_caption("Mango: The Virtual Lovebird")
        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.Font(None, 48)
        self.large_font = pygame.font.Font(None, 32)
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)
        self.tiny_font = pygame.font.Font(None, 16)

        self.state = GameState.TAMAGOTCHI_HUB
        self.running = True
        self.pending_scene = None  # a mini-game coroutine waiting to run
        self.animation_time = 0.0
        self.hud_messages = []     # (text, expiry timestamp)
        self.flash_until = 0.0

        self.api_handler = APIHandler()
        self.particle_system = ParticleSystem()

        self.last_stat_update = time.time()
        self.last_random_event = time.time()
        self.is_sick = False
        self.misbehavior_count = 0
        self.current_hour = datetime.now().hour
        self.is_night = is_night_hour(self.current_hour)

        # Saved data
        self.db_path = db_path
        self.settings_path = os.path.join(os.path.dirname(db_path) or ".", "settings.json")
        self.init_database()
        self.mango_state = self.load_state() or new_mango_state()
        self.save_state()
        self.high_score = self.get_high_score()

        # Images and sound
        self.backgrounds = load_backgrounds()
        self.mango_sprites = load_mango_sprites()
        self.tree_texture = load_image(os.path.join(SPRITES, "tree.png"))
        self.audio = AudioManager(**db.load_settings(self.settings_path))
        self._gradients = {}

    # ---------- Saving ----------

    def init_database(self):
        db.init_database(self.db_path)

    def save_state(self):
        db.save_state(self.db_path, self.mango_state)

    def load_state(self):
        return db.load_state(self.db_path)

    def save_score(self, score):
        db.save_score(self.db_path, score)
        self.high_score = max(self.high_score, score)

    def get_high_score(self):
        return db.get_high_score(self.db_path)

    def save_settings(self):
        db.save_settings(self.settings_path, self.audio.volumes())

    # ---------- Caring for Mango ----------

    def feed_mango(self):
        """Feed Mango to increase hunger."""
        if self.mango_state["hunger"] >= 100:
            return False
        self.mango_state["hunger"] = clamp(self.mango_state["hunger"] + 25)
        self.mango_state["happiness"] = clamp(self.mango_state["happiness"] + 5)
        self.save_state()
        return True

    def bathe_mango(self):
        """Bathe Mango to increase cleanliness."""
        if self.mango_state["cleanliness"] >= 100:
            return False
        self.mango_state["cleanliness"] = clamp(self.mango_state["cleanliness"] + 30)
        self.mango_state["happiness"] = clamp(self.mango_state["happiness"] + 10)
        self.save_state()
        return True

    def play_with_mango(self):
        """Play with Mango to increase happiness (costs energy)."""
        if self.mango_state["energy"] <= 10:
            return False
        self.mango_state["happiness"] = clamp(self.mango_state["happiness"] + 20)
        self.mango_state["energy"] = clamp(self.mango_state["energy"] - 15)
        self.save_state()
        return True

    def rest_mango(self):
        """Let Mango rest to restore energy."""
        if self.mango_state["energy"] >= 100:
            return False
        self.mango_state["energy"] = clamp(self.mango_state["energy"] + 30)
        self.save_state()
        return True

    def give_medicine(self):
        """Fully heal Mango and lift any critically low stats to 25."""
        self.mango_state["health"] = 100
        self.is_sick = False
        for stat in ("hunger", "cleanliness", "energy"):
            self.mango_state[stat] = max(self.mango_state[stat], 25)
        self.last_stat_update = time.time()
        self.audio.play_sfx("medicine")
        self.show_message("Medicine used!")
        self.flash_until = time.time() + 0.25
        self.save_state()
        return True

    def discipline(self):
        """Calm a misbehaving Mango down (costs a little happiness)."""
        if self.misbehavior_count <= 0:
            return False
        self.misbehavior_count -= 1
        self.mango_state["happiness"] = clamp(self.mango_state["happiness"] - 5)
        self.save_state()
        return True

    # ---------- Time passing ----------

    def age_mango(self):
        """Mango has a birthday every 24 hours."""
        last_birthday = datetime.fromisoformat(self.mango_state["last_updated"])
        if (datetime.now() - last_birthday).total_seconds() >= 24 * 3600:
            self.mango_state["age"] += 1
            self.mango_state["last_updated"] = datetime.now().isoformat()
            self.save_state()

    def update_stats(self):
        """Every 30 seconds, stats drop a little; neglect hurts Mango's health."""
        now = time.time()
        if now - self.last_stat_update < 30:
            return
        for stat in ("hunger", "happiness", "cleanliness", "energy"):
            self.mango_state[stat] = clamp(self.mango_state[stat] - 1)

        # Bad weather can dampen Mango's mood (good weather doesn't raise it)
        weather_mood = self.api_handler.get_weather_mood_effect() or 0
        if weather_mood < 0:
            self.mango_state["happiness"] = clamp(self.mango_state["happiness"] + weather_mood)

        if min(self.mango_state[s] for s in ("hunger", "cleanliness", "energy")) <= 10:
            self.mango_state["health"] = clamp(self.mango_state["health"] - 3)
        if self.mango_state["health"] <= 30:
            self.is_sick = True

        self.check_random_events()
        self.last_stat_update = now
        self.save_state()

    def check_random_events(self):
        """Every 2 minutes there's a 30% chance Mango gets sick or misbehaves."""
        now = time.time()
        if now - self.last_random_event < 120:
            return
        if random.random() < 0.3:
            event = random.choice(["sick", "misbehavior"])
            if event == "sick" and not self.is_sick:
                self.is_sick = True
                self.mango_state["health"] = clamp(self.mango_state["health"] - 20)
            elif event == "misbehavior":
                self.misbehavior_count += 1
                self.mango_state["happiness"] = clamp(self.mango_state["happiness"] - 10)
        self.last_random_event = now

    def get_mango_mood(self):
        """Determine Mango's current mood based on stats."""
        if self.is_sick:
            return "sick"
        if self.mango_state["cleanliness"] < 30:
            return "dirty"
        if self.mango_state["energy"] < 20:
            return "tired"
        if self.mango_state["happiness"] > 70:
            return "happy"
        if self.mango_state["happiness"] < 30:
            return "sad"
        return "neutral"

    def is_game_over(self):
        return self.mango_state["health"] <= 0

    def restart_game(self):
        """Welcome a brand-new Mango."""
        self.mango_state = new_mango_state()
        self.is_sick = False
        self.misbehavior_count = 0
        self.last_stat_update = time.time()
        self.state = GameState.TAMAGOTCHI_HUB
        self.save_state()

    def show_message(self, text, seconds=1.8):
        self.hud_messages.append((text, time.time() + seconds))

    # ---------- Mini-games ----------

    def start_minigame(self, name):
        """Queue a mini-game; the main loop runs it on the next frame."""
        self.pending_scene = self._run_minigame(name)
        return True

    def play_feed_minigame(self):
        return self.start_minigame("feed")

    def play_tickle_minigame(self):
        return self.start_minigame("tickle")

    def play_flappy_mango(self):
        return self.start_minigame("flappy")

    async def _run_minigame(self, name):
        import feed_minigame
        import flappy
        import tickle_minigame

        games = {
            "feed": (feed_minigame.play_feed_minigame, GameState.FEED),
            "tickle": (tickle_minigame.play_tickle_minigame, GameState.TICKLE),
            "flappy": (flappy.play_flappy_mango, GameState.FLAPPY_MANGO),
        }
        play, state = games[name]
        await self.fade(fade_in=False)
        self.state = state
        self.audio.play_music("forest")
        await play(self)
        if not self.running:
            return
        self.state = GameState.TAMAGOTCHI_HUB
        self.audio.play_music("home")
        self.particle_system.clear()
        self.draw()
        await self.fade(fade_in=True)

    # ---------- Frame helpers (shared with the mini-games) ----------

    async def next_frame(self):
        """Show what was drawn, wait for the next frame, and let the browser breathe."""
        pygame.display.flip()
        self.clock.tick(FPS)
        await asyncio.sleep(0)  # essential in the browser: hands control back to the page

    def events(self):
        """Return this frame's events, handling quitting and the audio unlock for every scene."""
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN, pygame.FINGERDOWN):
                self.audio.unlock()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.toggle_fullscreen()
        return events

    async def fade(self, fade_in, frames=10):
        """Fade the current screen to black (fade_in=False) or up from black (fade_in=True)."""
        snapshot = self.screen.copy()
        overlay = pygame.Surface(self.screen.get_size())
        overlay.fill((0, 0, 0))
        for i in range(1, frames + 1):
            darkness = 255 * i // frames
            overlay.set_alpha(255 - darkness if fade_in else darkness)
            self.screen.blit(snapshot, (0, 0))
            self.screen.blit(overlay, (0, 0))
            await self.next_frame()

    def toggle_fullscreen(self):
        """Desktop only; in the browser the page handles the canvas size."""
        if IS_WEB:
            return False
        pygame.display.toggle_fullscreen()
        return True

    # ---------- Drawing ----------

    def draw_gradient_background(self):
        """Day or night sky gradient (cached, since it never changes)."""
        key = "night" if self.is_night else "day"
        if key not in self._gradients:
            start, end = (NIGHT_START, NIGHT_END) if self.is_night else (GRADIENT_START, GRADIENT_END)
            surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            for y in range(SCREEN_HEIGHT):
                t = y / SCREEN_HEIGHT
                color = tuple(int(a + (b - a) * t) for a, b in zip(start, end))
                pygame.draw.line(surface, color, (0, y), (SCREEN_WIDTH, y))
            self._gradients[key] = surface
        self.screen.blit(self._gradients[key], (0, 0))

    def draw_background(self, key):
        """Draw a background image ('hub', 'flappy', 'feed'), or the sky gradient if it's missing."""
        image = self.backgrounds.get(key)
        if image is None:
            self.draw_gradient_background()
            return
        self.screen.blit(image, (0, 0))
        if key == "hub":
            # darken slightly so text stays readable
            if "hub_shade" not in self._gradients:
                shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                shade.set_alpha(30)
                shade.fill(BLACK)
                self._gradients["hub_shade"] = shade
            self.screen.blit(self._gradients["hub_shade"], (0, 0))

    def draw(self):
        import hub_ui

        if self.state == GameState.GAME_OVER:
            hub_ui.draw_game_over_screen(self)
        else:
            hub_ui.draw_home_screen(self)

    # ---------- Main loop ----------

    def update(self, dt):
        self.animation_time += dt
        self.update_stats()
        self.age_mango()
        if self.mango_state["health"] <= 30:
            self.is_sick = True

        hour = datetime.now().hour
        if hour != self.current_hour:
            self.current_hour = hour
            self.is_night = is_night_hour(hour)

        if self.is_game_over():
            self.state = GameState.GAME_OVER
        self.particle_system.update(dt)
        self.hud_messages = [(text, until) for text, until in self.hud_messages if until > time.time()]

    def handle_event(self, event):
        import hub_ui

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == GameState.GAME_OVER:
                self.audio.play_sfx("button")
                self.restart_game()
            else:
                hub_ui.handle_click(self, event.pos)
        elif event.type == pygame.MOUSEMOTION:
            hub_ui.handle_drag(self, event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            hub_ui.handle_release(self)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not IS_WEB:
            self.running = False

    async def run(self):
        self.audio.unlock()  # works right away on desktop; in the browser it retries on first click
        self.audio.play_music("home")
        while self.running:
            for event in self.events():
                self.handle_event(event)
            if self.pending_scene is not None:
                scene, self.pending_scene = self.pending_scene, None
                await scene
                continue
            self.update(1.0 / FPS)
            self.draw()
            await self.next_frame()
        self.save_state()


def main():
    asyncio.run(MangoTamagotchi().run())
    pygame.quit()


if __name__ == "__main__":
    main()
