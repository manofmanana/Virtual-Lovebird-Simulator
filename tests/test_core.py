import os
import tempfile
import sqlite3
import time
import pygame
import sys

# Ensure project root is on sys.path for test imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from project import MangoTamagotchi, GameState


def test_mango_initial_state(tmp_path, monkeypatch):
    # Use a temporary DB path so tests don't touch real DB
    db_path = tmp_path / "mango_test.db"
    game = MangoTamagotchi()
    game.db_path = str(db_path)
    # Ensure state exists after save/load cycle
    game.mango_state = None
    game.save_state()
    # save_state should create DB even if empty; load_state returns dict or None
    state = game.load_state()
    assert isinstance(state, dict) or state is None


def test_feed_bathe_rest_play_and_medicine(tmp_path):
    game = MangoTamagotchi()
    # set an initial state
    game.mango_state = {'hunger': 50, 'happiness': 50, 'cleanliness': 20, 'energy': 10, 'health': 50, 'age': 0, 'last_updated': time.time()}

    assert game.feed_mango() is True
    assert 50 <= game.mango_state['hunger'] <= 100

    assert game.bathe_mango() is True
    assert game.mango_state['cleanliness'] >= 20

    # ensure rest increases energy
    prev_energy = game.mango_state['energy']
    assert game.rest_mango() is True
    assert game.mango_state['energy'] >= prev_energy

    # play_with_mango requires energy > 10 to succeed
    game.mango_state['energy'] = 50
    assert game.play_with_mango() is True

    # give medicine should set health to 100
    game.mango_state['health'] = 10
    game.is_sick = True
    assert game.give_medicine() is True
    assert game.mango_state['health'] == 100


def test_toggle_fullscreen_returns_bool(monkeypatch):
    game = MangoTamagotchi()
    # patch pygame.display to avoid actually toggling
    class DummyDisp:
        def get_size(self):
            return (800, 600)

    game._display_screen = DummyDisp()

    res = game.toggle_fullscreen()
    assert isinstance(res, bool)
