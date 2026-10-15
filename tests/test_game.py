"""Play the hub and each mini-game headlessly with scripted input."""
import asyncio
import json
import sys
import types

import pygame
import pytest

import db
import feed_minigame
import flappy
import hub_ui
import tickle_minigame
from config import SCREEN_HEIGHT, SCREEN_WIDTH
from project import GameState, MangoTamagotchi


@pytest.fixture
def game(tmp_path):
    g = MangoTamagotchi(db_path=str(tmp_path / "mango.db"))
    g.clock = types.SimpleNamespace(tick=lambda fps=0: 0)  # run frames as fast as possible
    return g


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="")


def click(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


def script(game, frames):
    """Post one list of events per frame into pygame's queue, then let the game read them as usual."""
    queue = list(frames)
    read_events = game.events

    def scripted():
        for event in queue.pop(0) if queue else []:
            pygame.event.post(event)
        return read_events()

    game.events = scripted


def run(coroutine):
    """Run a scene, failing if it never finishes (e.g. a loop that ignores input)."""
    return asyncio.run(asyncio.wait_for(coroutine, timeout=30))


# ---------- Hub ----------

def button_center(label):
    return next(rect.center for rect, action in hub_ui.action_buttons() if action[0] == label)


def test_hub_draws_and_bathe_button_works(game):
    game.mango_state["cleanliness"] = 40
    hub_ui.draw_home_screen(game)
    hub_ui.handle_click(game, button_center("Bathe"))
    assert game.mango_state["cleanliness"] == 70
    assert any("clean" in m[0] for m in game.hud_messages)


def test_hub_explains_why_an_action_did_nothing(game):
    game.mango_state["energy"] = 5
    hub_ui.handle_click(game, button_center("Play"))
    assert any("too tired" in m[0] for m in game.hud_messages)


@pytest.mark.parametrize("label", ["Feed", "Tickle"])
def test_minigame_buttons_queue_a_scene(game, label):
    hub_ui.handle_click(game, button_center(label))
    assert game.pending_scene is not None
    game.pending_scene.close()


def test_flappy_button_queues_a_scene(game):
    hub_ui.handle_click(game, hub_ui.FLAPPY_RECT.center)
    assert game.pending_scene is not None
    game.pending_scene.close()


def test_clicking_game_over_screen_restarts(game):
    game.mango_state["health"] = 0
    game.update(1 / 60)
    assert game.state == GameState.GAME_OVER
    game.draw()
    game.handle_event(click((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
    assert game.state == GameState.TAMAGOTCHI_HUB
    assert game.mango_state["health"] == 100


def test_volume_slider_saves_settings(game):
    hub_ui.handle_click(game, hub_ui.AUDIO_BUTTON.center)
    track = hub_ui.slider_rect(1)  # music
    hub_ui.handle_click(game, (track.x + 1, track.centery))
    hub_ui.handle_release(game)
    assert game.audio.music_volume < 0.05
    assert db.load_settings(game.settings_path)["music"] < 0.05


# ---------- Mini-games ----------

def test_flappy_start_crash_and_leave(game, monkeypatch):
    saved = []
    monkeypatch.setattr(game, "save_score", saved.append)
    # flap once, then let Mango fall into the ground; wait out the game-over screen, then ESC
    script(game, [[key(pygame.K_SPACE)]] + [[]] * 200 + [[key(pygame.K_ESCAPE)]])
    run(flappy.play_flappy_mango(game))
    assert saved == []  # a score of 0 isn't recorded


def test_flappy_records_a_crash_score_exactly_once(game, monkeypatch):
    saved = []
    monkeypatch.setattr(game, "save_score", saved.append)
    # Mango hovers in place: three trees have their gap right on him (he scores 3),
    # then the gaps move to the top of the screen and he crashes into the next tree
    monkeypatch.setattr(flappy, "GRAVITY", 0)
    monkeypatch.setattr(flappy, "FLAP_STRENGTH", 0)
    monkeypatch.setattr(flappy, "SPAWN_EVERY", 40)
    gaps = iter([SCREEN_HEIGHT // 2] * 3 + [150] * 50)
    monkeypatch.setattr(flappy, "gap_center", lambda: next(gaps))
    script(game, [[key(pygame.K_SPACE)]] + [[]] * 700 + [[key(pygame.K_ESCAPE)]])
    run(flappy.play_flappy_mango(game))
    assert saved == [3]


def test_feed_catching_seeds_fills_mango_up(game, monkeypatch):
    game.mango_state["hunger"] = 10
    monkeypatch.setattr(feed_minigame, "TARGET", 2)
    monkeypatch.setattr(feed_minigame, "SPAWN_EVERY", (0.05, 0.05))
    # drop every seed right on top of Mango, quickly
    monkeypatch.setattr(feed_minigame.random, "randint", lambda a, b: SCREEN_WIDTH // 2)
    monkeypatch.setattr(feed_minigame, "SEED_SPEED", (2000, 2000))
    script(game, [[click((SCREEN_WIDTH // 2, 300))]] + [[]] * 120 + [[click(feed_minigame.BACK_BUTTON.center)]])
    run(feed_minigame.play_feed_minigame(game))
    assert game.mango_state["hunger"] == 100


def test_feed_gets_harder_as_mango_fills_up():
    assert feed_minigame.spawn_delay(0) == pytest.approx(1.3)
    assert feed_minigame.spawn_delay(feed_minigame.TARGET) == pytest.approx(0.55)
    assert feed_minigame.spawn_delay(10) < feed_minigame.spawn_delay(5)
    slowest_start, _ = feed_minigame.SEED_SPEED
    assert feed_minigame.seed_speed(0, roll=0.0) == slowest_start
    assert feed_minigame.seed_speed(15, roll=0.0) > feed_minigame.seed_speed(5, roll=0.0)


def test_tickle_ends_after_enough_tickles(game, monkeypatch):
    game.mango_state["happiness"] = 50
    game.misbehavior_count = 3
    monkeypatch.setattr(tickle_minigame, "TARGET", 2)
    monkeypatch.setattr(tickle_minigame.random, "random", lambda: 1.0)  # Mango stays put
    center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    script(game, [[key(pygame.K_SPACE)], [click(center)], [click(center)], [], [key(pygame.K_ESCAPE)]])
    run(tickle_minigame.play_tickle_minigame(game))
    assert game.mango_state["happiness"] == 70
    assert game.misbehavior_count == 1


def test_main_loop_runs_a_minigame_and_returns_to_hub(game):
    game.play_tickle_minigame()
    frames = [[]] * 15 + [[key(pygame.K_ESCAPE)]] + [[]] * 15 + [[pygame.event.Event(pygame.QUIT)]]
    script(game, frames)
    run(game.run())
    assert game.state == GameState.TAMAGOTCHI_HUB
    assert not game.running


# ---------- Browser saving ----------

def test_browser_save_uses_local_storage(monkeypatch, tmp_path):
    store = {}
    fake_storage = types.SimpleNamespace(getItem=store.get, setItem=store.__setitem__)
    monkeypatch.setitem(sys.modules, "platform", types.SimpleNamespace(window=types.SimpleNamespace(localStorage=fake_storage)))
    monkeypatch.setattr(db, "IS_WEB", True)

    state = {"hunger": 1, "happiness": 2, "cleanliness": 3, "energy": 4, "health": 5, "age": 6, "last_updated": "x"}
    db.save_state("ignored", state)
    db.save_score("ignored", 7)
    db.save_score("ignored", 3)

    assert db.load_state("ignored") == state
    assert db.get_high_score("ignored") == 7
    assert json.loads(store["mango_state"])["age"] == 6
    assert not (tmp_path / "ignored").exists()
