"""Music and sound effects.

Browsers won't play sound until the player has clicked or pressed a key, so
the mixer is started lazily: unlock() is called on the first click/keypress,
and any music requested before that starts as soon as audio is unlocked.
"""
import os

import pygame

from config import SOUNDS

SFX_FILES = {
    "flap": "flap.ogg",
    "thump": "thump.ogg",
    "button": "buttonpressed.ogg",
    "medicine": "medicine.ogg",
    "chirp": "chirp.ogg",
}
MUSIC_FILES = {
    "home": "home.ogg",
    "forest": "forest.ogg",
}


class AudioManager:
    def __init__(self, master=0.9, music=0.6, sfx=0.9):
        self.master_volume = master
        self.music_volume = music
        self.sfx_volume = sfx
        self.sounds = {}
        self.ready = False
        self.current_music = None
        self.wanted_music = None

    def unlock(self):
        """Start the mixer and load sounds. Safe to call repeatedly."""
        if self.ready:
            return True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
            for key, filename in SFX_FILES.items():
                path = os.path.join(SOUNDS, filename)
                if os.path.exists(path):
                    self.sounds[key] = pygame.mixer.Sound(path)
        except pygame.error as e:
            print(f"Audio unavailable: {e}")
            return False
        self.ready = True
        self.apply_volumes()
        if self.wanted_music:
            self.play_music(self.wanted_music)
        return True

    def apply_volumes(self):
        if not self.ready:
            return
        pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume * self.master_volume)

    def set_volume(self, channel, value):
        """Set 'master', 'music', or 'sfx' volume (0.0 to 1.0)."""
        setattr(self, f"{channel}_volume", max(0.0, min(1.0, value)))
        self.apply_volumes()

    def volumes(self):
        return {"master": self.master_volume, "music": self.music_volume, "sfx": self.sfx_volume}

    def play_sfx(self, key):
        sound = self.sounds.get(key)
        if sound is not None:
            sound.play()

    def play_music(self, key):
        """Loop a music track. Remembered and started later if audio isn't unlocked yet."""
        self.wanted_music = key
        if not self.ready or self.current_music == key:
            return
        path = os.path.join(SOUNDS, MUSIC_FILES[key])
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)
            self.current_music = key
        except pygame.error as e:
            print(f"Could not play {path}: {e}")

    def stop_music(self):
        self.wanted_music = None
        self.current_music = None
        if self.ready:
            pygame.mixer.music.stop()
