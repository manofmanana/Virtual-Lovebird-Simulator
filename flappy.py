"""Flappy Mango mini-game logic extracted from project.py.

This module provides a single function `play_flappy_mango(game, flappy_state, exit_state)`
which runs the Flappy mini-game using the passed `game` instance. It intentionally
imports the main module at runtime so it can reference constants without creating
an import-cycle during module import time.
"""
import time
import os
import random
import math

try:
    import pygame
except Exception:
    pygame = None

# Try to import project for constants; if unavailable at import-time we fall back
# to resolving it at runtime inside the function. This keeps the module import
# safe in test/analysis environments that may not have the full runtime ready.
try:
    import project as _project
except Exception:
    _project = None


def play_flappy_mango(game, flappy_state, exit_state):
    """Run the Flappy Mango mini-game using the provided game instance.

    Args:
        game: instance of MangoTamagotchi
        flappy_state: GameState value representing the flappy state
        exit_state: GameState value to set when exiting Flappy (hub)
    """
    # set state
    try:
        game.state = flappy_state
    except Exception:
        pass

    # Reload sprites to ensure they persist when returning
    try:
        game.load_mango_sprites()
    except Exception:
        pass

    # Draw and present an initial frame immediately so the UI updates
    # before any audio or heavy initialization happens. This ensures the
    # player sees the Flappy screen promptly (fixes fullscreen visual lag).
    try:
        game.draw_flappy_background()
        try:
            game.present()
            # Fade in gently when entering the mini-game if supported
            try:
                if hasattr(game, 'fade_in'):
                    game.fade_in()
            except Exception:
                pass
        except Exception:
            try:
                pygame.display.flip()
            except Exception:
                pass
    except Exception:
        pass

    # Local helpers to access constants from the main module
    SCREEN_WIDTH = getattr(_project, 'SCREEN_WIDTH', game.screen.get_width())
    SCREEN_HEIGHT = getattr(_project, 'SCREEN_HEIGHT', game.screen.get_height())
    FPS = getattr(_project, 'FPS', 60)

    # Flappy Mango game variables
    mango_x = 150
    mango_y = SCREEN_HEIGHT // 2
    mango_velocity = 0
    gravity = 0.75
    jump_strength = -13

    crows = []
    crow_spawn_timer = 0
    crow_spawn_interval = 150

    score = 0
    game_over = False
    game_started = False
    last_score_update = 0

    # Start flappy background music and exercise SFX path (safe, non-fatal)
    try:
        game._ensure_audio_ready()
    except Exception:
        pass

    try:
        # Force-play quick flap/thump to exercise SFX path; tolerate failures
        flap_path = "assets/sounds/flap.wav"
        thump_path = "assets/sounds/thump.wav"
        if os.path.exists(flap_path):
            try:
                s = pygame.mixer.Sound(flap_path)
                s.set_volume(min(1.0, game.sfx_volume * game.master_volume))
                try:
                    if getattr(game, 'audio', None):
                        ch0 = game.audio._get_sfx_channel() or pygame.mixer.Channel(0)
                    else:
                        ch0 = pygame.mixer.Channel(0)
                    try:
                        ch0.set_volume(min(1.0, game.sfx_volume * game.master_volume))
                    except Exception:
                        pass
                    ch0.play(s)
                except Exception:
                    s.play()
            except Exception:
                pass
        if os.path.exists(thump_path):
            try:
                t = pygame.mixer.Sound(thump_path)
                t.set_volume(min(1.0, game.sfx_volume * game.master_volume))
                try:
                    if getattr(game, 'audio', None):
                        ch1 = game.audio._get_sfx_channel() or pygame.mixer.Channel(1)
                    else:
                        ch1 = pygame.mixer.Channel(1)
                    try:
                        ch1.set_volume(min(1.0, game.sfx_volume * game.master_volume))
                    except Exception:
                        pass
                    ch1.play(t)
                except Exception:
                    t.play()
            except Exception:
                pass
    except Exception:
        pass

    # Enable forced short flap tone while in Flappy and other flags
    game._force_short_flap_in_flappy = True
    game._last_sfx_event = None

    try:
        # Only start music if the user already initiated audio (browsers block autoplay).
        if getattr(game, '_music_started', False):
            game._play_music('forest')
            if getattr(game, 'audio', None):
                try:
                    game.audio.start_watchdog('forest')
                except Exception:
                    pass
            else:
                game._music_watchdog = True
        else:
            # Queue music so start_music() will play it when the user clicks
            try:
                game._queued_music = 'forest'
            except Exception:
                pass
    except Exception:
        pass

    # Temporary audio boost for entry
    try:
        game._audio_saved_volumes = (game.master_volume, game.music_volume, game.sfx_volume)
        game.master_volume = max(game.master_volume, 1.0)
        game.music_volume = max(game.music_volume, 0.6)
        game.sfx_volume = max(game.sfx_volume, 0.85)
        try:
            game._apply_volume_settings()
        except Exception:
            pass
        game._audio_temp_restore_at = time.time() + 3.0
        try:
            if getattr(game, '_dev_mode', False):
                try:
                    game._play_debug_tone(freq=900, duration_ms=400, volume=1.0)
                except Exception:
                    pass
        except Exception:
            pass
    except Exception:
        pass

    # Main flappy loop
    while getattr(game, 'state', None) == flappy_state:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                try:
                    game.state = exit_state
                    # Always stop current music immediately
                    try:
                        game._stop_music()
                    except Exception:
                        pass
                    # Resume hub/home music only if user already allowed audio
                    if getattr(game, '_music_started', False):
                        try:
                            game._play_music('home')
                        except Exception:
                            pass
                    else:
                        try:
                            game._queued_music = 'home'
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    game._force_short_flap_in_flappy = False
                except Exception:
                    pass
                try:
                    if getattr(game, 'audio', None):
                        game.audio.stop_watchdog()
                    else:
                        game._music_watchdog = False
                except Exception:
                    pass
                # Fade out back to hub if possible
                try:
                    if hasattr(game, 'fade_out'):
                        game.fade_out()
                except Exception:
                    pass
                return

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not game_started:
                        game_started = True
                    if not game_over:
                        mango_velocity = jump_strength
                        try:
                            if getattr(game, '_force_short_flap_in_flappy', False):
                                try:
                                    debug_path = 'assets/sounds/_flap_short_debug.wav'
                                    if not os.path.exists(debug_path):
                                        try:
                                            game._write_short_tone(debug_path, freq=1500, duration_ms=160, volume=1.0)
                                        except Exception:
                                            pass
                                    try:
                                        game._play_debug_tone(freq=1500, duration_ms=160, volume=1.0)
                                        game._last_sfx_event = 'flap (debug)'
                                    except Exception:
                                        game._play_sfx('flap', maxtime=2000)
                                except Exception:
                                    game._play_sfx('flap', maxtime=2000)
                            else:
                                game._play_sfx('flap', maxtime=2000)
                            if game._last_sfx_event is None:
                                game._last_sfx_event = 'flap'
                        except Exception:
                            pass
                        game._flap_start = time.time()
                        game._flap_duration = 0.25

                elif event.key == pygame.K_ESCAPE:
                    try:
                        game._play_sfx('button')
                    except Exception:
                        pass
                    game.state = exit_state
                    try:
                        game._stop_music()
                        if getattr(game, '_music_started', False):
                            try:
                                game._play_music('home')
                            except Exception:
                                pass
                        else:
                            try:
                                game._queued_music = 'home'
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        game._force_short_flap_in_flappy = False
                    except Exception:
                        pass
                    try:
                        if getattr(game, 'audio', None):
                            game.audio.stop_watchdog()
                        else:
                            game._music_watchdog = False
                    except Exception:
                        pass
                    # Fade to black before returning to hub
                    try:
                        if hasattr(game, 'fade_out'):
                            game.fade_out()
                    except Exception:
                        pass
                    return

                elif event.key == pygame.K_r and game_over:
                    try:
                        game._play_sfx('button')
                    except Exception:
                        pass
                    mango_x = 150
                    mango_y = SCREEN_HEIGHT // 2
                    mango_velocity = 0
                    crows = []
                    score = 0
                    game_over = False
                    game_started = False
                    last_score_update = 0

                elif event.key == pygame.K_d:
                    try:
                        game._play_debug_tone(freq=1200, duration_ms=300, volume=1.0)
                    except Exception:
                        pass

        if not game_over and game_started:
            mango_velocity += gravity
            mango_y += mango_velocity

            crow_spawn_timer += 1
            if crow_spawn_timer >= crow_spawn_interval:
                crows.append({
                    'x': SCREEN_WIDTH,
                    'y': random.randint(150, SCREEN_HEIGHT - 250),
                    'gap': 220,
                    'scored': False
                })
                crow_spawn_timer = 0

            for crow in crows[:]:
                crow['x'] -= 3
                if crow['x'] < -50:
                    crows.remove(crow)
                if not crow['scored'] and crow['x'] + 50 < mango_x:
                    score += 1
                    crow['scored'] = True
                    last_score_update = time.time()

            mango_rect = pygame.Rect(mango_x - 15, mango_y - 15, 30, 30)
            for crow in crows:
                top_rect = pygame.Rect(crow['x'], 0, 70, crow['y'] - crow['gap'] // 2)
                bottom_rect = pygame.Rect(crow['x'], crow['y'] + crow['gap'] // 2, 70, SCREEN_HEIGHT - crow['y'] - crow['gap'] // 2)
                if mango_rect.colliderect(top_rect) or mango_rect.colliderect(bottom_rect):
                    game_over = True
                    try:
                        game._play_sfx('thump')
                    except Exception:
                        pass
                    break

            if mango_y >= SCREEN_HEIGHT - 60 or mango_y <= -150:
                game_over = True
                try:
                    game._play_sfx('thump')
                except Exception:
                    pass

        # Draw background and UI elements via game helpers
        try:
            game.draw_flappy_background()
        except Exception:
            pass

        # Dev overlay, watchdog, volume restore and drawing logic reused from project
        if getattr(game, '_dev_mode', False):
            try:
                ox, oy = 8, 8
                box_w, box_h = 320, 120
                dbg_rect = pygame.Rect(ox, oy, box_w, box_h)
                s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                s.fill((20, 20, 20, 180))
                game.screen.blit(s, (ox, oy))
                try:
                    init = bool(pygame.mixer.get_init())
                except Exception:
                    init = False
                try:
                    nch = pygame.mixer.get_num_channels()
                except Exception:
                    nch = 'N/A'
                lines = [f"mixer_init: {init}", f"channels: {nch}", f"master: {game.master_volume:.2f}", f"music: {game.music_volume:.2f}", f"sfx: {game.sfx_volume:.2f}"]
                for i, ln in enumerate(lines):
                    txt = game.tiny_font.render(ln, True, _project.WHITE)
                    game.screen.blit(txt, (ox + 8, oy + 8 + i * 18))
                try:
                    if os.path.exists('audio_debug.log'):
                        with open('audio_debug.log', 'r') as _lf:
                            tail = _lf.read().splitlines()[-4:]
                        for j, ln in enumerate(tail):
                            txt = game.tiny_font.render(ln[-60:], True, (200, 200, 200))
                            game.screen.blit(txt, (ox + 8, oy + 8 + (5 + j) * 16))
                except Exception:
                    pass
            except Exception:
                pass

        try:
            if getattr(game, '_music_restore_at', None) and time.time() >= game._music_restore_at:
                try:
                    if getattr(game, '_music_started', False):
                        game._play_music('forest')
                    else:
                        game._queued_music = 'forest'
                except Exception:
                    pass
                game._music_restore_at = None
        except Exception:
            pass

        for crow in crows:
            try:
                shadow_offset = 3
                pygame.draw.rect(game.screen, (0, 0, 0, 100), (crow['x'] + shadow_offset, shadow_offset, 70, crow['y'] - crow['gap'] // 2))
                pygame.draw.rect(game.screen, (0, 0, 0, 100), (crow['x'] + shadow_offset, crow['y'] + crow['gap'] // 2 + shadow_offset, 70, SCREEN_HEIGHT - crow['y'] - crow['gap'] // 2))
                top_h = max(8, crow['y'] - crow['gap'] // 2)
                bottom_h = max(8, SCREEN_HEIGHT - crow['y'] - crow['gap'] // 2)
                if getattr(game, 'tree_texture', None):
                    tex_top = pygame.transform.smoothscale(game.tree_texture, (70, top_h))
                    game.screen.blit(tex_top, (crow['x'], 0))
                    tex_bot = pygame.transform.smoothscale(game.tree_texture, (70, bottom_h))
                    try:
                        tex_bot = pygame.transform.flip(tex_bot, False, True)
                    except Exception:
                        pass
                    game.screen.blit(tex_bot, (crow['x'], crow['y'] + crow['gap'] // 2))
                else:
                    WOOD_BROWN = (101, 67, 33)
                    crow_top_rect = pygame.Rect(crow['x'], 0, 70, top_h)
                    pygame.draw.rect(game.screen, WOOD_BROWN, crow_top_rect, border_radius=12)
                    crow_bottom_rect = pygame.Rect(crow['x'], crow['y'] + crow['gap'] // 2, 70, bottom_h)
                    pygame.draw.rect(game.screen, WOOD_BROWN, crow_bottom_rect, border_radius=12)
                head_y_top = crow['y'] - crow['gap'] // 2 - 15
                head_y_bottom = crow['y'] + crow['gap'] // 2 + 15
                pygame.draw.circle(game.screen, _project.BLACK, (crow['x'] + 35, head_y_top), 12)
                beak_points = [(crow['x'] + 35, head_y_top - 5), (crow['x'] + 30, head_y_top - 12), (crow['x'] + 40, head_y_top - 12)]
                pygame.draw.polygon(game.screen, (255, 140, 0), beak_points)
                pygame.draw.circle(game.screen, _project.WHITE, (crow['x'] + 32, head_y_top - 2), 3)
                pygame.draw.circle(game.screen, _project.BLACK, (crow['x'] + 32, head_y_top - 2), 2)
                pygame.draw.circle(game.screen, _project.BLACK, (crow['x'] + 35, head_y_bottom), 12)
                beak_points = [(crow['x'] + 35, head_y_bottom + 5), (crow['x'] + 30, head_y_bottom + 12), (crow['x'] + 40, head_y_bottom + 12)]
                pygame.draw.polygon(game.screen, (255, 140, 0), beak_points)
                pygame.draw.circle(game.screen, _project.WHITE, (crow['x'] + 32, head_y_bottom + 2), 3)
                pygame.draw.circle(game.screen, _project.BLACK, (crow['x'] + 32, head_y_bottom + 2), 2)
            except Exception:
                crow_top_rect = pygame.Rect(crow['x'], 0, 70, 10)
                pygame.draw.rect(game.screen, _project.BLACK, crow_top_rect, border_radius=12)
                crow_bottom_rect = pygame.Rect(crow['x'], crow['y'] + crow['gap'] // 2, 70, 10)
                pygame.draw.rect(game.screen, _project.BLACK, crow_bottom_rect, border_radius=12)

        mango_wing_offset = int(3 * math.sin(game.animation_time * 4)) if not game_over else 0

        try:
            shadow_surf = pygame.Surface((60, 30), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 40), shadow_surf.get_rect())
            shadow_rect = shadow_surf.get_rect(center=(int(mango_x + 4), int(mango_y + 14)))
            game.screen.blit(shadow_surf, shadow_rect)
        except Exception:
            pass

        if hasattr(game, 'mango_sprites') and game.mango_sprites.get('flying'):
            sprite1 = game.mango_sprites.get('flying')
            sprite2 = game.mango_sprites.get('flying2')
            flappy_sprite1 = pygame.transform.scale(sprite1, (90, 90)) if sprite1 else None
            flappy_sprite2 = pygame.transform.scale(sprite2, (90, 90)) if sprite2 else None
            use_alt = False
            if hasattr(game, '_flap_start') and flappy_sprite2:
                if time.time() - getattr(game, '_flap_start', 0) < getattr(game, '_flap_duration', 0.5):
                    use_alt = True
            try:
                if use_alt and flappy_sprite2:
                    sprite_rect = flappy_sprite2.get_rect(center=(int(mango_x), int(mango_y)))
                    game.screen.blit(flappy_sprite2, sprite_rect)
                else:
                    sprite_rect = flappy_sprite1.get_rect(center=(int(mango_x), int(mango_y)))
                    game.screen.blit(flappy_sprite1, sprite_rect)
            except Exception:
                try:
                    sprite_rect = flappy_sprite1.get_rect(center=(int(mango_x), int(mango_y)))
                    game.screen.blit(flappy_sprite1, sprite_rect)
                except Exception:
                    pass
        else:
            pygame.draw.circle(game.screen, _project.ORANGE, (int(mango_x), int(mango_y)), 18)
            pygame.draw.ellipse(game.screen, (255, 140, 0), (mango_x - 20, mango_y - 5 + mango_wing_offset, 15, 10))
            pygame.draw.ellipse(game.screen, (255, 140, 0), (mango_x + 5, mango_y - 5 + mango_wing_offset, 15, 10))
            pygame.draw.circle(game.screen, _project.BLACK, (int(mango_x - 6), int(mango_y - 5)), 2)
            pygame.draw.circle(game.screen, _project.BLACK, (int(mango_x + 6), int(mango_y - 5)), 2)
            beak_points = [(mango_x, mango_y + 3), (mango_x - 2, mango_y + 7), (mango_x + 2, mango_y + 7)]
            pygame.draw.polygon(game.screen, _project.ORANGE, beak_points)

        # UI panels, score and game-over drawing
        try:
            score_panel = pygame.Rect(SCREEN_WIDTH - 220, 20, 200, 80)
            pygame.draw.rect(game.screen, _project.SILVER, score_panel, border_radius=15)
            pygame.draw.rect(game.screen, _project.GOLD, score_panel, 3, border_radius=15)
            score_text = game.large_font.render(f"Score: {score}", True, _project.BLACK)
            game.screen.blit(score_text, (SCREEN_WIDTH - 205, 35))
            high_score_text = game.small_font.render(f"Best: {game.high_score}", True, _project.DARK_GRAY)
            game.screen.blit(high_score_text, (SCREEN_WIDTH - 205, 65))
        except Exception:
            pass

        if not game_started:
            try:
                start_panel = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100, 400, 200)
                pygame.draw.rect(game.screen, _project.WHITE, start_panel, border_radius=20)
                pygame.draw.rect(game.screen, _project.GOLD, start_panel, 4, border_radius=20)
                start_text = game.title_font.render("Flappy Mango", True, _project.BLACK)
                start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
                game.screen.blit(start_text, start_rect)
                instruction_text = game.font.render("Press SPACE to start!", True, _project.BLACK)
                inst_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
                game.screen.blit(instruction_text, inst_rect)
                esc_text = game.small_font.render("ESC to return to hub", True, _project.DARK_GRAY)
                esc_rect = esc_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
                game.screen.blit(esc_text, esc_rect)
            except Exception:
                pass
        elif not game_over:
            try:
                instruction_text = game.small_font.render("SPACE to flap | ESC to quit", True, _project.WHITE)
                game.screen.blit(instruction_text, (20, SCREEN_HEIGHT - 40))
            except Exception:
                pass
        else:
            try:
                game_over_panel = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 150, 500, 300)
                pygame.draw.rect(game.screen, _project.WHITE, game_over_panel, border_radius=20)
                pygame.draw.rect(game.screen, _project.RED, game_over_panel, 4, border_radius=20)
                game_over_text = game.title_font.render("Game Over!", True, _project.RED)
                go_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
                game.screen.blit(game_over_text, go_rect)
                final_score_text = game.large_font.render(f"Final Score: {score}", True, _project.BLACK)
                fs_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
                game.screen.blit(final_score_text, fs_rect)
                restart_text = game.font.render("Press R to restart", True, _project.BLACK)
                restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
                game.screen.blit(restart_text, restart_rect)
                esc_text = game.font.render("ESC to return to hub", True, _project.BLACK)
                esc_rect = esc_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
                game.screen.blit(esc_text, esc_rect)
                if score > 0:
                    game.save_score(score)
                    happiness_bonus = min(25, score * 2)
                    game.mango_state['happiness'] = min(100, game.mango_state['happiness'] + happiness_bonus)
                    game.save_state()
            except Exception:
                pass

        # Present the logical surface to the actual display every frame
        try:
            game.present()
        except Exception:
            try:
                pygame.display.flip()
            except Exception:
                pass
        try:
            game.clock.tick(FPS)
        except Exception:
            try:
                game.clock.tick(getattr(_project, 'FPS', 60))
            except Exception:
                pass
