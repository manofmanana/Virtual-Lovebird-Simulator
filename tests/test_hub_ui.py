import pygame
import sys
import os

# Ensure project root is on sys.path for test imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from project import MangoTamagotchi, GameState
import hub_ui


def test_draw_home_screen_runs(monkeypatch):
    game = MangoTamagotchi()
    game.state = GameState.TAMAGOTCHI_HUB
    # Ensure fonts exist
    game.title_font = game.title_font
    # call draw_home_screen - should not raise
    hub_ui.draw_home_screen(game)


def test_handle_click_no_error(monkeypatch):
    game = MangoTamagotchi()
    game.state = GameState.TAMAGOTCHI_HUB
    # simulate clicking center
    w, h = game.screen.get_width(), game.screen.get_height()
    pos = (w // 2, h // 2)
    # call handle_click - should not raise
    hub_ui.handle_click(game, pos)
