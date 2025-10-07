"""Hub UI rendering and input handling extracted from project.py.

This module exposes three functions that operate on a MangoTamagotchi
instance: draw_home_screen(game), handle_click(game, pos), draw_game_over_screen(game).
They mirror the behavior previously defined as methods on MangoTamagotchi.
"""
import time
import os
import random
import pygame
import math
from datetime import datetime

def draw_home_screen(game):
    # Import project module for constants (done at runtime to avoid cycles)
    try:
        import project as _project
    except Exception:
        _project = None

    # Draw background (image or gradient). Do NOT autoplay music here;
    # browsers will block autoplay. Music should start after a user
    # interaction via game.start_music().
    try:
        game.draw_hub_background()
    except Exception:
        pass


    # Title
    try:
        title_text = game.title_font.render("Mango: The Virtual Lovebird", True, _project.WHITE if _project else (255,255,255))
        title_rect = title_text.get_rect(center=(getattr(_project, 'SCREEN_WIDTH', game.screen.get_width()) // 2, 40))
        game.screen.blit(title_text, title_rect)
    except Exception:
        pass

    # Core cage geometry
    cage_width = 280
    cage_height = 280
    gap = 20
    screen_w = getattr(game, 'SCREEN_WIDTH', game.screen.get_width())
    cage_x = max(20, (screen_w - cage_width) // 2)
    cage_y = 120

    # Draw cage shadow, frame and interior
    try:
        shadow = pygame.Surface((cage_width, cage_height), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 100))
        game.screen.blit(shadow, (cage_x + 5, cage_y + 5))
    except Exception:
        try:
            pygame.draw.rect(game.screen, (0, 0, 0), pygame.Rect(cage_x + 5, cage_y + 5, cage_width, cage_height), border_radius=15)
        except Exception:
            pass

    frame_rect = pygame.Rect(cage_x - 8, cage_y - 8, cage_width + 16, cage_height + 16)
    # draw only the outline for the frame so the interior overlay remains dark
    try:
        # make the gold frame thicker for emphasis
        pygame.draw.rect(game.screen, _project.GOLD if _project else (255,215,0), frame_rect, 6, border_radius=20)
    except Exception:
        # fallback: draw a slightly thicker rectangle border
        pygame.draw.rect(game.screen, _project.GOLD if _project else (255,215,0), frame_rect, 4)
    cage_rect = pygame.Rect(cage_x, cage_y, cage_width, cage_height)
    # Draw a semi-transparent black interior for the cage (transparent background)
    try:
        overlay = pygame.Surface((cage_width, cage_height), pygame.SRCALPHA)
        # overall translucent black fill
        overlay.fill((0, 0, 0, 140))
        # darker inner border for subtle edge
        try:
            pygame.draw.rect(overlay, (0, 0, 0, 200), pygame.Rect(1, 1, cage_width - 2, cage_height - 2), 2, border_radius=14)
        except Exception:
            # fallback: draw a simple rect if rounded rect isn't supported
            pygame.draw.rect(overlay, (0, 0, 0, 200), pygame.Rect(1, 1, cage_width - 2, cage_height - 2), 2)
        game.screen.blit(overlay, (cage_x, cage_y))
    except Exception:
        try:
            # ultimate fallback: solid dark rect
            pygame.draw.rect(game.screen, (20, 20, 20), cage_rect)
        except Exception:
            pass

    # Mango sprite - ensure uniform hub size and simple animation
    mood = game.get_mango_mood()
    # Base center inside the cage
    mango_x = cage_x + cage_width // 2
    mango_y = cage_y + cage_height // 2
    # Determine sprite mood before computing phase
    sprite_mood = mood if mood in ['happy', 'sad', 'tired', 'dirty'] else 'idle'
    # Make mango perfectly centered in the cage and only pulsate (scale)
    try:
        # keep the mango centered in the cage; avoid large positional offsets
        mango_x = int(cage_x + cage_width // 2)
        mango_y = int(cage_y + cage_height // 2)
        # use a phase so different moods pulse slightly out-of-sync
        phase = (hash(sprite_mood) % 100) / 100.0 * math.pi * 2
        # pulse between ~0.82 and 1.18 for a clear but tasteful pulse
        pulse = 1.0 + 0.18 * math.sin(game.animation_time * 3.2 + phase)
    except Exception:
        mango_x = int(mango_x)
        mango_y = int(mango_y)
        pulse = 1.0

    HUB_SPRITE_SIZE = (140, 140)
    drawn = False
    try:
        if hasattr(game, 'mango_sprites'):
            # build frame list: look for mood and mood2 variants
            frames = []
            base = game.mango_sprites.get(sprite_mood)
            if base:
                frames.append(base)
            # allow alternate frame like 'flying2' or mood+'2'
            alt = game.mango_sprites.get(sprite_mood + '2')
            if alt:
                frames.append(alt)

            if frames:
                # pick frame based on animation_time; speed up multiplier for liveliness
                try:
                    # previously *3, make it slightly faster across the board
                    idx = int(game.animation_time * 4.5) % len(frames)
                except Exception:
                    idx = 0
                frame = frames[idx]
                try:
                    # scale to uniform hub size with pulse
                    sw = max(8, int(HUB_SPRITE_SIZE[0] * pulse))
                    sh = max(8, int(HUB_SPRITE_SIZE[1] * pulse))
                    scaled = pygame.transform.smoothscale(frame, (sw, sh))
                    # always draw centered on the cage center; if single frame, add a tiny bob
                    if len(frames) == 1:
                        bob = int(math.sin(game.animation_time * 3.0) * 4)
                        game.screen.blit(scaled, scaled.get_rect(center=(mango_x, mango_y + bob)))
                    else:
                        game.screen.blit(scaled, scaled.get_rect(center=(mango_x, mango_y)))
                    # capture the actual scaled rect for accurate clicking
                    last_scaled_rect = scaled.get_rect(center=(mango_x, mango_y))
                    drawn = True
                except Exception:
                    drawn = False
    except Exception:
        drawn = False

    if not drawn:
        # fallback: draw consistent ellipse sized to HUB_SPRITE_SIZE
        try:
            mango_color = _project.ORANGE if _project else (255,152,0)
            w, h = HUB_SPRITE_SIZE
            pygame.draw.ellipse(game.screen, mango_color, (mango_x - w//2, mango_y - h//2, w, h))
        except Exception:
            pass

    # Ensure moods animate even if only a single frame is available by
    # generating a subtle alternate frame (scaled) and caching it on the game
    try:
        if hasattr(game, 'mango_sprites'):
            # if frames is defined and only a single frame is present, create a cached alternate
            if 'frames' in locals() and len(frames) == 1:
                try:
                    if not hasattr(game, '_hub_alt_frames'):
                        game._hub_alt_frames = {}
                    if sprite_mood not in game._hub_alt_frames:
                        try:
                            # create a subtly scaled variant for a two-frame animation
                            # use a slightly stronger scale so the pulsing/frame-swap is visible
                            alt = pygame.transform.rotozoom(frames[0], 0, 0.92)
                            game._hub_alt_frames[sprite_mood] = alt
                        except Exception:
                            game._hub_alt_frames[sprite_mood] = frames[0]
                    # append cached alt if available
                    altf = game._hub_alt_frames.get(sprite_mood)
                    if altf is not None:
                        frames.append(altf)
                except Exception:
                    pass
    except Exception:
        pass

    # Store the hub mango rect so clicks can target it for particles / interaction
    try:
        # Use the last drawn scaled rect if available for precise hit testing,
        # otherwise fall back to a padded area around the hub center.
        if 'last_scaled_rect' in locals():
            game._hub_mango_rect = last_scaled_rect.inflate(18, 18)
        else:
            pad = 18
            game._hub_mango_rect = pygame.Rect(int(mango_x - HUB_SPRITE_SIZE[0]//2 - pad), int(mango_y - HUB_SPRITE_SIZE[1]//2 - pad), HUB_SPRITE_SIZE[0] + pad*2, HUB_SPRITE_SIZE[1] + pad*2)
    except Exception:
        try:
            game._hub_mango_rect = pygame.Rect(int(mango_x - HUB_SPRITE_SIZE[0]//2), int(mango_y - HUB_SPRITE_SIZE[1]//2), HUB_SPRITE_SIZE[0], HUB_SPRITE_SIZE[1])
        except Exception:
            game._hub_mango_rect = None

    # Helpers
    try:
        from ui_helpers import draw_modern_button as _dmb, draw_modern_progress_bar as _dmpb
    except Exception:
        _dmb = None
        _dmpb = None

    # Action buttons: two vertical stacks (3 left, 3 right)
    button_width = 140
    button_height = 48
    v_spacing = 18
    all_buttons = [
        ("Feed", game.play_feed_minigame, getattr(game, 'GREEN', (76,175,80)), (0,200,0)),
        ("Bathe", game.bathe_mango, getattr(game, 'BLUE', (33,150,243)), (0,100,200)),
        ("Play", game.play_with_mango, getattr(game, 'YELLOW', (255,193,7)), (200,150,0)),
        ("Rest", game.rest_mango, getattr(game, 'PINK', (233,30,99)), (200,100,150)),
        ("Medicine", game.give_medicine, getattr(game, 'RED', (244,67,54)), (200,0,0)),
        ("Tickle", game.discipline, getattr(game, 'PURPLE', (156,39,176)), (100,0,100)),
    ]

    left_buttons = all_buttons[:3]
    right_buttons = all_buttons[3:]

    # move stacks 10px further from center for better spacing
    left_x = max(8, cage_x - gap - button_width - 10)
    right_x = min(screen_w - button_width - 8, cage_x + cage_width + gap + 10)
    stack_height = 3 * button_height + 2 * v_spacing
    stack_start_y = cage_y + (cage_height - stack_height) // 2

    # Use logical mouse position (set by project.run) when available so
    # hover/click detection is correct after scaling to fullscreen.
    mouse_pos = getattr(game, '_mouse_pos_logical', None)
    if not mouse_pos:
        mouse_pos = pygame.mouse.get_pos()
    game._hub_button_rects = []

    for i, (text, action, color, hover_color) in enumerate(left_buttons):
        by = stack_start_y + i * (button_height + v_spacing)
        rect = pygame.Rect(left_x, by, button_width, button_height)
        game._hub_button_rects.append((rect, action, text))
        if _dmb:
            try:
                _dmb(game, rect, text, color, hover_color, (255,255,255), rect.collidepoint(mouse_pos))
            except Exception:
                pass

    for i, (text, action, color, hover_color) in enumerate(right_buttons):
        by = stack_start_y + i * (button_height + v_spacing)
        rect = pygame.Rect(right_x, by, button_width, button_height)
        game._hub_button_rects.append((rect, action, text))
        if _dmb:
            try:
                _dmb(game, rect, text, color, hover_color, (255,255,255), rect.collidepoint(mouse_pos))
            except Exception:
                pass

    # Flappy Mango button (moved higher)
    flappy_x = screen_w - 200
    flappy_y = 20
    flappy_rect = pygame.Rect(flappy_x, flappy_y, 150, 60)
    game._flappy_button_rect = flappy_rect
    if _dmb:
        try:
            _dmb(game, flappy_rect, "Flappy Mango", getattr(game, 'ORANGE', (255,152,0)), getattr(game, 'GOLD', (255,215,0)), (255,255,255), flappy_rect.collidepoint(mouse_pos))
        except Exception:
            pass

    # draw small flapping sprite over Flappy button when recently clicked
    try:
        if getattr(game, '_flappy_click_at', None) and time.time() - game._flappy_click_at < 1.0:
            # try to use flying frames if available
            if hasattr(game, 'mango_sprites'):
                f1 = game.mango_sprites.get('flying')
                f2 = game.mango_sprites.get('flying2')
                frames = [f for f in (f1, f2) if f]
                if frames:
                    idx = int(game.animation_time * 6.0) % len(frames)
                    bf = frames[idx]
                    try:
                        bs = pygame.transform.smoothscale(bf, (48, 48))
                        cx, cy = flappy_rect.center
                        game.screen.blit(bs, bs.get_rect(center=(cx, cy - 10)))
                    except Exception:
                        pass
    except Exception:
        pass

    # Fullscreen toggle button (top-right corner)
    try:
        fs_w, fs_h = 28, 20
        # place the fullscreen button fixed to the top-right with a small margin
        try:
            fs_x = screen_w - fs_w - 12
        except Exception:
            fs_x = max(12, screen_w - fs_w - 12)
        fs_y = 12
        fs_rect = pygame.Rect(fs_x, fs_y, fs_w, fs_h)
        game._fullscreen_button_rect = fs_rect
        # Draw the compact fullscreen icon
        pygame.draw.rect(game.screen, (28, 28, 28), fs_rect, border_radius=6)
        pygame.draw.rect(game.screen, (255,255,255), fs_rect, 1, border_radius=6)
        try:
            # small corner marks
            pygame.draw.line(game.screen, (255,255,255), (fs_rect.left+4, fs_rect.top+8), (fs_rect.left+4, fs_rect.top+4))
            pygame.draw.line(game.screen, (255,255,255), (fs_rect.left+4, fs_rect.top+4), (fs_rect.left+8, fs_rect.top+4))
            pygame.draw.line(game.screen, (255,255,255), (fs_rect.right-4, fs_rect.bottom-8), (fs_rect.right-4, fs_rect.bottom-4))
            pygame.draw.line(game.screen, (255,255,255), (fs_rect.right-4, fs_rect.bottom-4), (fs_rect.right-8, fs_rect.bottom-4))
        except Exception:
            pass
    except Exception:
        pass

    # Stats panel: centered below cage and moved slightly higher (10px)
    try:
        stats_rect = getattr(game, '_stats_panel_rect', None)
        if not stats_rect:
            stats_w = min(screen_w - 80, 720)
            stats_h = 160
            stats_x = cage_x + (cage_width - stats_w) // 2
            stats_y = cage_y + cage_height + 28  # moved 10px higher than previous baseline
            stats_rect = pygame.Rect(stats_x, stats_y, stats_w, stats_h)
            game._stats_panel_rect = stats_rect

        panel_x, panel_y, panel_w, panel_h = stats_rect.x, stats_rect.y, stats_rect.width, stats_rect.height
        s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 160))
        game.screen.blit(s, (panel_x, panel_y))
        pygame.draw.rect(game.screen, getattr(game, 'GOLD', (255,215,0)), pygame.Rect(panel_x-3, panel_y-3, panel_w+6, panel_h+6), 3, border_radius=8)
        pygame.draw.rect(game.screen, getattr(game, 'SILVER', (192,192,192)), stats_rect, 2, border_radius=6)

        prev_clip = game.screen.get_clip()
        game.screen.set_clip(stats_rect)
        try:
            try:
                title = game.small_font.render('Mango Stats', True, (255,255,255))
                game.screen.blit(title, (panel_x + (panel_w - title.get_width()) // 2, panel_y + 6))
            except Exception:
                pass

            stat_items = [
                ('Hunger', game.mango_state.get('hunger', 0), (255,152,0)),
                ('Happiness', game.mango_state.get('happiness', 0), (76,175,80)),
                ('Cleanliness', game.mango_state.get('cleanliness', 0), (33,150,243)),
                ('Energy', game.mango_state.get('energy', 0), (255,193,7)),
                ('Health', game.mango_state.get('health', 0), (244,67,54)),
            ]

            spacing = 12
            y = panel_y + 8 + title.get_height()
            bar_h = max(12, (panel_h - (y - panel_y) - spacing * len(stat_items)) // (len(stat_items)))
            bar_w = panel_w - 160
            if not _dmpb:
                from ui_helpers import draw_modern_progress_bar as _dmpb

            for label, val, color in stat_items:
                try:
                    lbl = game.small_font.render(label, True, (255,255,255))
                    game.screen.blit(lbl, (panel_x + 12, y + (bar_h - lbl.get_height()) // 2))
                except Exception:
                    pass
                try:
                    bx = panel_x + 120
                    _dmpb(game, bx, y, bar_w, bar_h, val, 100, color)
                except Exception:
                    pass
                y += bar_h + spacing
        finally:
            game.screen.set_clip(prev_clip)
    except Exception:
        pass

    # High Score (centered under Flappy and raised)
    try:
        fl = getattr(game, '_flappy_button_rect', None)
        if fl:
            hs_text = game.font.render(f"High Score: {game.high_score}", True, (255,255,255))
            hs_x = fl.centerx - hs_text.get_width() // 2
            # lower the High Score slightly so it sits comfortably under the button
            hs_y = fl.bottom + 6
            game.screen.blit(hs_text, (hs_x, hs_y))
    except Exception:
        pass

    # Status messages and centered bird fact
    status_y = 620
    try:
        bird_fact = game.api_handler.get_bird_fact()
        if bird_fact:
            sw = screen_w
            fact_w, fact_h = 440, 40
            fact_x = (sw - fact_w) // 2
            fact_rect = pygame.Rect(fact_x, status_y, fact_w, fact_h)
            pygame.draw.rect(game.screen, getattr(game, 'GOLD', (255,215,0)), fact_rect, border_radius=20)
            pygame.draw.rect(game.screen, (255,255,255), fact_rect, 2, border_radius=20)
            fact_text = game.tiny_font.render(bird_fact, True, (0,0,0))
            game.screen.blit(fact_text, fact_text.get_rect(center=fact_rect.center))
    except Exception:
        pass

    # Occasionally play a background chirp in the hub so the world feels alive.
    # Use a cooldown so we don't spam sounds; fallback to direct sound playback
    # if the audio wrapper raises.
    try:
        now = time.time()
        if not hasattr(game, '_last_chirp_time'):
            game._last_chirp_time = 0.0
        # only consider chirping if at least 6 seconds passed since last chirp
        if now - game._last_chirp_time > 6.0:
            # ~2% chance per frame after cooldown — low and pleasant
            if random.random() < 0.02:
                try:
                    game._play_sfx('chirp')
                    game._last_chirp_time = now
                except Exception:
                    # fallback: direct channel play if available
                    try:
                        if 'chirp' in getattr(game, 'sounds', {}):
                            game.sounds['chirp'].play()
                            game._last_chirp_time = now
                    except Exception:
                        pass
    except Exception:
        pass

    # Compact audio settings dropdown (top-left)
    try:
        btn_w, btn_h = 100, 28
        btn_x, btn_y = 12, 8
        btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        game._audio_dropdown_btn_rect = btn_rect
        pygame.draw.rect(game.screen, (30, 30, 30), btn_rect, border_radius=8)
        pygame.draw.rect(game.screen, (255,255,255), btn_rect, 2, border_radius=8)
        btn_label = game.small_font.render("Audio", True, (255,255,255))
        game.screen.blit(btn_label, (btn_x + 12, btn_y + 7))

        if getattr(game, '_audio_dropdown_open', False):
            dd_w = btn_w + 40
            dd_h = 130
            dd_x = btn_x
            dd_y = btn_y + btn_h + 10
            dd_rect = pygame.Rect(dd_x, dd_y, dd_w, dd_h)
            pygame.draw.rect(game.screen, (25,25,25), dd_rect, border_radius=8)
            pygame.draw.rect(game.screen, (255,255,255), dd_rect, 1, border_radius=8)

            # ensure audio sliders dict exists
            if not hasattr(game, '_audio_sliders') or not isinstance(game._audio_sliders, dict):
                game._audio_sliders = {'master': {'value': game.master_volume}, 'music': {'value': game.music_volume}, 'sfx': {'value': game.sfx_volume}}

            def draw_compact_slider(key, y_offset, value):
                sx = dd_x + 8
                sw = max(80, dd_w - 16)
                sy = dd_y + y_offset
                tr = pygame.Rect(sx, sy + 6, sw, 8)
                pygame.draw.rect(game.screen, getattr(game, 'DARK_GRAY', (40,40,40)), tr, border_radius=4)
                fw = int(value * sw)
                fr = pygame.Rect(sx, sy + 6, fw, 8)
                pygame.draw.rect(game.screen, getattr(game, 'GREEN', (76,175,80)), fr, border_radius=4)
                tx = sx + fw
                tr_thumb = pygame.Rect(tx - 5, sy + 2, 10, 14)
                pygame.draw.rect(game.screen, (255,255,255), tr_thumb, border_radius=4)
                lbl = game.tiny_font.render(key[0].upper() + key[1:], True, (255,255,255))
                game.screen.blit(lbl, (sx, sy - 10))
                game._audio_sliders[key]['rect'] = pygame.Rect(sx, sy, sw, 24)

            draw_compact_slider('master', 18, max(0.0, min(1.0, game.master_volume)))
            draw_compact_slider('music', 58, max(0.0, min(1.0, game.music_volume)))
            draw_compact_slider('sfx', 98, max(0.0, min(1.0, game.sfx_volume)))
    except Exception:
        pass


def handle_click(game, pos):
    # Recreate hub button layout and dispatch clicks to the proper methods.
    try:
        # Ensure background music only starts after explicit user interaction
        try:
            game.start_music()
        except Exception:
            pass
        x, y = pos
        # Start music on the first user click (browsers require user gesture)
        try:
            if not getattr(game, '_music_started', False):
                try:
                    game.start_music('home')
                except Exception:
                    pass
        except Exception:
            pass
        # Audio dropdown toggle
        btn = getattr(game, '_audio_dropdown_btn_rect', None)
        if btn and btn.collidepoint(pos):
            game._audio_dropdown_open = not getattr(game, '_audio_dropdown_open', False)
            return

        # First user interaction: enable music playback if available
        try:
            if not getattr(game, '_music_started', False):
                try:
                    game.start_music()
                except Exception:
                    pass
        except Exception:
            pass

        # Check action buttons
        for rect, action, text in getattr(game, '_hub_button_rects', []):
            if rect.collidepoint(pos):
                try:
                    if callable(action):
                        # If action is a mini-game launcher (convention: name starts with 'play_'),
                        # perform a fade_out from the hub before entering so the transition is smooth.
                        try:
                            aname = getattr(action, '__name__', '')
                            # Only trigger a pre-launch fade when the player clicked the
                            # Feed button (so the hub fades to black before entering Feed).
                            if aname == 'play_feed_minigame' and hasattr(game, 'fade_out'):
                                try:
                                    game.fade_out()
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        # Trigger particle effects and temporary sprite animation for feedback
                        try:
                            if hasattr(game, 'particle_system') and game.particle_system:
                                # spawn at button center
                                bx, by = rect.centerx, rect.centery
                                try:
                                    game.particle_system.add_button_effect(bx, by, text.lower())
                                except Exception:
                                    pass
                                try:
                                    game.particle_system.add_sprite_animation(text.lower())
                                except Exception:
                                    pass
                        except Exception:
                            pass

                        ok = action()
                        # play button sound and show HUD message on success
                        try:
                            if ok:
                                # If this was the Medicine action, play only the medicine SFX.
                                try:
                                    # play medicine SFX when medicine was used
                                    if text and text.lower() == 'medicine':
                                        try:
                                            game._play_sfx('medicine')
                                        except Exception:
                                            try:
                                                if 'medicine' in getattr(game, 'sounds', {}):
                                                    game.sounds['medicine'].play()
                                            except Exception:
                                                pass
                                    # generic button click feedback (keeps previous behavior)
                                    try:
                                        game._play_sfx('button')
                                    except Exception:
                                        try:
                                            if 'button' in getattr(game, 'sounds', {}):
                                                game.sounds['button'].play()
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                # short feedback
                                try:
                                    game.hud_messages.append((f"{text} successful", time.time() + 1.5))
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    return
                except Exception:
                    return

        # Flappy button
        flappy_rect = getattr(game, '_flappy_button_rect', None)
        if flappy_rect and flappy_rect.collidepoint(pos):
            try:
                # Fade out from hub then start flappy mini-game for a smooth transition
                try:
                    if hasattr(game, 'fade_out'):
                        try:
                            game.fade_out()
                        except Exception:
                            pass
                except Exception:
                    pass
                # Start flappy mini-game
                try:
                    game._flappy_click_at = time.time()
                except Exception:
                    pass
                game.play_flappy_mango()
            except Exception:
                pass
            return

        # Mango clicked in the hub: spawn particle effects on the mango sprite
        try:
            hub_mango_rect = getattr(game, '_hub_mango_rect', None)
            if hub_mango_rect and hub_mango_rect.collidepoint(pos):
                try:
                    if hasattr(game, 'particle_system') and game.particle_system:
                        # spawn particles at the actual click coords so the effect matches the user's click
                        cx, cy = pos
                        game.particle_system.add_button_effect(cx, cy, 'tickle')
                        game.particle_system.add_sprite_animation('tickle')
                except Exception:
                    pass
                try:
                    game._play_sfx('chirp')
                except Exception:
                    pass
                return
        except Exception:
            pass

        # Fullscreen button click
        try:
            fs = getattr(game, '_fullscreen_button_rect', None)
            if fs and fs.collidepoint(pos):
                try:
                    ok = False
                    try:
                        ok = bool(game.toggle_fullscreen())
                    except Exception:
                        # fallback: try pygame toggle
                        try:
                            pygame.display.toggle_fullscreen()
                            ok = True
                            game.fullscreen = not getattr(game, 'fullscreen', False)
                        except Exception:
                            ok = False
                    try:
                        game._play_sfx('button')
                    except Exception:
                        pass
                    try:
                        if ok:
                            game.hud_messages.append(("Toggled fullscreen", time.time() + 1.5))
                        else:
                            game.hud_messages.append(("Fullscreen request failed", time.time() + 1.5))
                    except Exception:
                        pass
                except Exception:
                    pass
                return
        except Exception:
            pass

        # Sliders interaction: detect clicks on the slider rects and set dragging
        try:
            for key, meta in getattr(game, '_audio_sliders', {}).items():
                r = meta.get('rect')
                if r and r.collidepoint(pos):
                    meta['dragging'] = True
                    return
        except Exception:
            pass

    except Exception:
        pass


def draw_game_over_screen(game):
    # Deterministic game-over drawing
    try:
        game.draw_gradient_background()
        panel_rect = pygame.Rect(game.screen.get_width() // 2 - 300, game.screen.get_height() // 2 - 200, 600, 400)
        pygame.draw.rect(game.screen, (0,0,0,100), pygame.Rect(panel_rect.x + 5, panel_rect.y + 5, panel_rect.width, panel_rect.height), border_radius=25)
        pygame.draw.rect(game.screen, (255,255,255), panel_rect, border_radius=25)
        game_over_text = game.title_font.render("Mango has flown away!", True, (244,67,54))
        go_rect = game_over_text.get_rect(center=(panel_rect.centerx, panel_rect.y + 60))
        game.screen.blit(game_over_text, go_rect)
    except Exception:
        pass
