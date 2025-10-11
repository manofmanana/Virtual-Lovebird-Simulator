import sys
import os
import importlib

# Ensure project root is first on sys.path when pytest runs to import top-level modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def test_tickle_minigame_importable():
    m = importlib.import_module('tickle_minigame')
    assert hasattr(m, 'play_tickle_minigame')


def test_feed_minigame_importable():
    m = importlib.import_module('feed_minigame')
    assert hasattr(m, 'play_feed_minigame')


def test_flappy_importable():
    m = importlib.import_module('flappy')
    assert hasattr(m, 'play_flappy_mango')
