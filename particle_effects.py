"""Lightweight particle effects for UI interactions and sprite animations.

This module provides a small ParticleSystem used by the hub UI to spawn
per-button particles and to temporarily override the mango sprite for
button-press animations.
"""
import time
import random
import math
try:
    import pygame
except Exception:
    pygame = None


class UIParticle:
    def __init__(self, x, y, color, effect='default', lifetime=1.2):
        self.x = float(x) + random.uniform(-6, 6)
        self.y = float(y) + random.uniform(-6, 6)
        self.vx = random.uniform(-2.5, 2.5)
        self.vy = random.uniform(-5.0, -1.0)
        self.color = color
        self.age = 0.0
        self.lifetime = lifetime
        self.size = random.uniform(2.0, 6.0)
        self.effect = effect

    def update(self, dt):
        self.age += dt
        # simple physics
        self.x += self.vx
        self.y += self.vy
        # gravity or float depending on effect
        if self.effect in ('tickle', 'rest'):
            self.vy -= 0.02  # float upward slightly
        else:
            self.vy += 0.15
        # slight damping
        self.vx *= 0.995
        return self.age < self.lifetime

    def draw(self, surface):
        if not pygame:
            return
        if self.age >= self.lifetime:
            return
        alpha = max(0.0, 1.0 - (self.age / self.lifetime))
        r, g, b = self.color[:3]
        col = (int(r * alpha), int(g * alpha), int(b * alpha))
        size = max(1, int(self.size * alpha))
        try:
            pygame.draw.circle(surface, col, (int(self.x), int(self.y)), size)
        except Exception:
            pass


class ParticleSystem:
    def __init__(self):
        self.particles = []
        # sprite_animations: map button_type -> {'sprite': 'mango_happy', 'end_time': t}
        self.sprite_animations = {}

    def add_button_effect(self, x, y, button_type):
        bt = (button_type or 'default').lower()
        mapping = {
            'feed': ([(160, 82, 45), (210, 180, 140)], 'feed'),
            'bathe': ([(135, 206, 250), (173, 216, 230)], 'bathe'),
            'play': ([(255, 255, 0), (255, 200, 0)], 'play'),
            'rest': ([(200, 200, 200), (255, 255, 255)], 'rest'),
            'medicine': ([(255, 0, 0), (255, 192, 203)], 'medicine'),
            'tickle': ([(255, 105, 180), (255, 192, 203)], 'tickle'),
        }
        colors, effect = mapping.get(bt, ([(255,255,255)], 'default'))
        count = random.randint(6, 12)
        for _ in range(count):
            c = random.choice(colors)
            p = UIParticle(x + random.uniform(-8,8), y + random.uniform(-8,8), c, effect)
            self.particles.append(p)

    def add_sprite_animation(self, button_type, duration=0.8):
        bt = (button_type or 'default').lower()
        sprite_map = {
            'feed': 'mango_happy',
            'bathe': 'mango_moving',
            'play': 'mango_happy',
            'rest': 'mango_tired',
            'medicine': 'mango_moving',
            'tickle': 'mango_happy',
        }
        sprite = sprite_map.get(bt, 'mango_idle')
        self.sprite_animations[bt] = {'sprite': sprite, 'end_time': time.time() + duration, 'start_time': time.time()}

    def get_current_sprite(self, default='mango_idle'):
        now = time.time()
        # purge expired
        expired = [k for k, v in self.sprite_animations.items() if v['end_time'] <= now]
        for k in expired:
            try:
                del self.sprite_animations[k]
            except Exception:
                pass
        if not self.sprite_animations:
            return default
        # return most recent
        latest = max(self.sprite_animations.values(), key=lambda v: v.get('start_time', 0))
        return latest.get('sprite', default)

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface):
        for p in list(self.particles):
            p.draw(surface)

    def clear(self):
        self.particles.clear()
        self.sprite_animations.clear()
