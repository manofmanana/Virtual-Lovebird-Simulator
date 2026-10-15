"""Little bits of "juice": floating score text and screen shake."""
import random
import time

from ui_helpers import text


class Effects:
    def __init__(self):
        self.floaters = []      # rising, fading text like "+1" or "+30 Clean"
        self.shake_until = 0.0
        self.shake_strength = 0

    def float_text(self, font, label, pos, color, rise=46, duration=0.9):
        self.floaters.append({"surface": text(font, label, color), "pos": pos, "born": time.time(),
                              "rise": rise, "duration": duration})

    def shake(self, strength=8, duration=0.35):
        self.shake_strength = strength
        self.shake_until = time.time() + duration

    def clear(self):
        self.floaters.clear()
        self.shake_until = 0.0

    def draw(self, screen):
        now = time.time()
        alive = []
        for f in self.floaters:
            t = (now - f["born"]) / f["duration"]
            if t >= 1:
                continue
            alive.append(f)
            eased = 1 - (1 - t) ** 3  # fast at first, then settling
            surface = f["surface"].copy()
            surface.set_alpha(int(255 * (1 - t ** 2)))
            x, y = f["pos"]
            screen.blit(surface, surface.get_rect(center=(x, y - f["rise"] * eased)))
        self.floaters = alive

    def apply_shake(self, screen):
        """Nudge the finished frame around while a shake is active."""
        remaining = self.shake_until - time.time()
        if remaining <= 0:
            return
        strength = max(1, int(self.shake_strength * min(1, remaining / 0.2)))
        screen.scroll(random.randint(-strength, strength), random.randint(-strength, strength))
