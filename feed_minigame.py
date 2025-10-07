"""Feed Mini-game: catch falling seeds to feed Mango.

This module provides play_feed_minigame(game, feed_state, exit_state).
Player moves Mango left/right to catch seeds; 20 seeds caught ends the game
and restores Mango's hunger to full.
"""
import time
import random
import math
try:
    import pygame
except Exception:
    pygame = None

try:
    import project as _project
except Exception:
    _project = None


def play_feed_minigame(game, feed_state, exit_state):
    try:
        game.state = feed_state
    except Exception:
        pass

    SCREEN_WIDTH = getattr(_project, 'SCREEN_WIDTH', game.screen.get_width())
    SCREEN_HEIGHT = getattr(_project, 'SCREEN_HEIGHT', game.screen.get_height())
    FPS = getattr(_project, 'FPS', 60)

    # Player mango horizontal movement
    mango_x = SCREEN_WIDTH // 2
    mango_y = SCREEN_HEIGHT - 120
    mango_speed = 6
    # make mango larger (user requested bigger mango)
    mango_w = 110
    mango_h = 88

    seeds = []
    spawn_timer = 0
    # less frequent spawns to reduce clutter
    spawn_interval = 90  # frames

    caught = 0
    target = 20
    running = True
    started = False
    show_instructions = True
    show_end = False
    end_message = ""

    # Play forest music during the mini-game (fallbacks handled by AudioManager)
    try:
            if getattr(game, '_music_started', False):
                game._play_music('forest')
            else:
                game._queued_music = 'forest'
    except Exception:
        try:
            game._play_music('home')
        except Exception:
            pass

    # Module-level caches for resources (do not reload every frame)
    global _feed_bg_surface, _feed_mango_still_surf, _feed_mango_moving_surf, _feed_seed_surf, _feed_ground_surf
    try:
        _feed_bg_surface
    except NameError:
        _feed_bg_surface = None
    try:
        _feed_mango_still_surf
    except NameError:
        _feed_mango_still_surf = None
    try:
        _feed_mango_moving_surf
    except NameError:
        _feed_mango_moving_surf = None
    try:
        _feed_seed_surf
    except NameError:
        _feed_seed_surf = None

    # Load background image if available
    if pygame and _feed_bg_surface is None:
        try:
            bg_path = 'assets/backgrounds/feed_bg.png'
            img = pygame.image.load(bg_path)
            try:
                img = img.convert_alpha()
            except Exception:
                img = img.convert()
            # scale background to fill the entire screen
            _feed_bg_surface = pygame.transform.smoothscale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            _feed_bg_surface = None

    # prepare a dark-brown ground texture at the bottom of the mini-game
    try:
        _feed_ground_surf
    except NameError:
        _feed_ground_surf = None
    ground_h = max(28, mango_h // 2)
    ground_y = SCREEN_HEIGHT - ground_h
    if pygame and _feed_ground_surf is None:
        try:
            # create a small tiled pixel texture for the ground
            gs = pygame.Surface((8, 8))
            gs.fill((101, 67, 33))  # base dark brown
            # add some lighter/darker pixels for a simple pixel texture
            gs.set_at((1, 1), (90, 50, 30))
            gs.set_at((2, 3), (120, 80, 50))
            gs.set_at((5, 2), (110, 70, 40))
            # tile to full width
            surf = pygame.Surface((SCREEN_WIDTH, ground_h))
            for x in range(0, SCREEN_WIDTH, 8):
                for y in range(0, ground_h, 8):
                    try:
                        surf.blit(gs, (x, y))
                    except Exception:
                        pass
            _feed_ground_surf = surf.convert()
        except Exception:
            _feed_ground_surf = None

    # Load mango and seed sprites (prefer explicit files; fall back to game.mango_sprites)
    if pygame:
        if _feed_mango_still_surf is None:
            try:
                p = 'assets/sprites/mango_still.png'
                img = pygame.image.load(p)
                _feed_mango_still_surf = img.convert_alpha() if hasattr(img, 'convert_alpha') else img.convert()
            except Exception:
                _feed_mango_still_surf = None
                try:
                    _feed_mango_still_surf = game.mango_sprites.get('still')
                except Exception:
                    _feed_mango_still_surf = None

        # prepare scaled version for the current mango size
        try:
            _feed_mango_still_scaled
        except NameError:
            _feed_mango_still_scaled = None
        if pygame and _feed_mango_still_surf and _feed_mango_still_scaled is None:
                try:
                    _feed_mango_still_scaled = pygame.transform.smoothscale(_feed_mango_still_surf, (mango_w, mango_h))
                except Exception:
                    _feed_mango_still_scaled = _feed_mango_still_surf

        if _feed_mango_moving_surf is None:
            try:
                p = 'assets/sprites/mango_moving.png'
                img = pygame.image.load(p)
                _feed_mango_moving_surf = img.convert_alpha() if hasattr(img, 'convert_alpha') else img.convert()
            except Exception:
                _feed_mango_moving_surf = None
                try:
                    _feed_mango_moving_surf = game.mango_sprites.get('moving')
                except Exception:
                    _feed_mango_moving_surf = None

        try:
            _feed_mango_moving_scaled
        except NameError:
            _feed_mango_moving_scaled = None
        if pygame and _feed_mango_moving_surf and _feed_mango_moving_scaled is None:
                try:
                    _feed_mango_moving_scaled = pygame.transform.smoothscale(_feed_mango_moving_surf, (mango_w, mango_h))
                except Exception:
                    _feed_mango_moving_scaled = _feed_mango_moving_surf

        if _feed_seed_surf is None:
            try:
                p = 'assets/sprites/seed.png'
                img = pygame.image.load(p)
                seed_img = img.convert_alpha() if hasattr(img, 'convert_alpha') else img.convert()
                # scale seed to a larger size for better visibility
                try:
                    _feed_seed_surf = pygame.transform.smoothscale(seed_img, (28, 28))
                except Exception:
                    _feed_seed_surf = seed_img
            except Exception:
                _feed_seed_surf = None

    last_time = time.time()
    clock = pygame.time.Clock() if pygame else None
    # track previous x to compute velocity-based movement
    prev_mango_x = mango_x
    movement_threshold_px_per_s = 20.0  # consider moving if velocity exceeds this

    while running and getattr(game, 'state', None) == feed_state:
        # handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Ensure hub music is restored when exiting the mini-game
                try:
                    game._stop_music()
                    if getattr(game, '_music_started', False):
                        game._play_music('home')
                    else:
                        game._queued_music = 'home'
                except Exception:
                    pass
                game.state = exit_state
                running = False
                break
            elif event.type == pygame.KEYDOWN:
                if not started:
                    if event.key == pygame.K_SPACE:
                        started = True
                        show_instructions = False
                    elif event.key == pygame.K_ESCAPE:
                        try:
                            game._play_sfx('button')
                        except Exception:
                            pass
                        try:
                            game._stop_music()
                            if getattr(game, '_music_started', False):
                                game._play_music('home')
                            else:
                                game._queued_music = 'home'
                        except Exception:
                            pass
                        game.state = exit_state
                        running = False
                        break
                else:
                    if event.key == pygame.K_ESCAPE:
                        try:
                            game._play_sfx('button')
                        except Exception:
                            pass
                        try:
                            game._stop_music()
                            if getattr(game, '_music_started', False):
                                game._play_music('home')
                            else:
                                game._queued_music = 'home'
                        except Exception:
                            pass
                        game.state = exit_state
                        running = False
                        break
                    if show_end and event.key == pygame.K_r:
                        # restart the minigame
                        caught = 0
                        started = False
                        show_instructions = True
                        show_end = False
                        end_message = ""
                        try:
                            seeds.clear()
                        except Exception:
                            seeds = []
                        spawn_timer = 0
                        prev_mango_x = mango_x

        # keyboard state
        keys = pygame.key.get_pressed() if pygame else []
        if keys:
            if keys[pygame.K_LEFT]:
                mango_x -= mango_speed
            if keys[pygame.K_RIGHT]:
                mango_x += mango_speed

        # compute velocity and movement detection
        try:
            now = time.time()
            dt = now - last_time if now > last_time else 1.0 / FPS
            last_time = now
            vx = (mango_x - prev_mango_x) / (dt if dt > 0 else 1.0)
            keys_moving = bool(keys and (keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]))
            moved = keys_moving or abs(vx) > movement_threshold_px_per_s
            prev_mango_x = mango_x
        except Exception:
            # fallback to simple threshold check
            try:
                moved = abs(mango_x - prev_mango_x) > 1
                prev_mango_x = mango_x
            except Exception:
                moved = False

        # keep in bounds
        mango_x = max(mango_w//2, min(SCREEN_WIDTH - mango_w//2, mango_x))

        # spawn seeds
        spawn_timer += 1
        if spawn_timer >= spawn_interval:
            spawn_timer = 0
            seeds.append({
                'x': random.randint(20, SCREEN_WIDTH - 20),
                'y': -10,
                'vy': random.uniform(1.0, 2.2)
            })

        # update seeds only when the minigame has started and is not in end state
        mango_rect = pygame.Rect(int(mango_x - mango_w//2), int(mango_y - mango_h//2), mango_w, mango_h)
        if started and not show_end:
            for s in seeds[:]:
                # make seeds fall a bit slower for easier catches
                s['y'] += s['vy'] * 0.85

                # build seed rect based on sprite size if available
                if _feed_seed_surf:
                    sw, sh = _feed_seed_surf.get_size()
                    seed_rect = pygame.Rect(int(s['x'] - sw//2), int(s['y'] - sh//2), sw, sh)
                else:
                    seed_rect = pygame.Rect(int(s['x'] - 6), int(s['y'] - 6), 12, 12)

                # collision with mango
                try:
                    if seed_rect.colliderect(mango_rect):
                        caught += 1
                        try:
                            game._play_sfx('chirp')
                        except Exception:
                            pass
                        try:
                            seeds.remove(s)
                        except Exception:
                            pass
                        continue
                except Exception:
                    pass

                # if seed touches the ground, penalize and remove
                try:
                    if s['y'] >= ground_y:
                        # subtract a point but never go below 0
                        caught = max(0, caught - 1)
                        try:
                            seeds.remove(s)
                        except Exception:
                            pass
                        continue
                except Exception:
                    pass

                # remove seeds that fall off bottom as fallback
                if s['y'] > SCREEN_HEIGHT + 50:
                    try:
                        seeds.remove(s)
                    except Exception:
                        pass

        # draw
        try:
            # draw dedicated feed background if available, else fallback
            if pygame and _feed_bg_surface:
                try:
                    game.screen.blit(_feed_bg_surface, (0, 0))
                except Exception:
                    try:
                        game.draw_gradient_background()
                    except Exception:
                        # last-resort: clear screen
                        game.screen.fill((0, 0, 0))
            else:
                try:
                    game.draw_gradient_background()
                except Exception:
                    game.screen.fill((0, 0, 0))
        except Exception:
            pass

            # draw seeds and mango
        try:
            for s in seeds:
                if _feed_seed_surf:
                    try:
                        rect = _feed_seed_surf.get_rect(center=(int(s['x']), int(s['y'])))
                        game.screen.blit(_feed_seed_surf, rect)
                    except Exception:
                        pygame.draw.circle(game.screen, (210, 180, 140), (int(s['x']), int(s['y'])), 12)
                else:
                    pygame.draw.circle(game.screen, (210, 180, 140), (int(s['x']), int(s['y'])), 12)
            # draw mango: when moving use mango_still, when still use mango_moving
            using_sprite = False
            try:
                # moved variable is computed earlier using velocity/keys
                # prefer scaled surfaces if available
                if moved and _feed_mango_still_scaled:
                    rect = _feed_mango_still_scaled.get_rect(center=(int(mango_x), int(mango_y)))
                    game.screen.blit(_feed_mango_still_scaled, rect)
                    using_sprite = True
                elif (not moved) and _feed_mango_moving_scaled:
                    rect = _feed_mango_moving_scaled.get_rect(center=(int(mango_x), int(mango_y)))
                    game.screen.blit(_feed_mango_moving_scaled, rect)
                    using_sprite = True
            except Exception:
                using_sprite = False

            # fallback to game sprite or ellipse when no sprite drawn
            if not using_sprite:
                try:
                    if hasattr(game, 'mango_sprites') and game.mango_sprites.get('idle'):
                        sp = game.mango_sprites.get('idle')
                        game.screen.blit(sp, sp.get_rect(center=(int(mango_x), int(mango_y))))
                    else:
                        pygame.draw.ellipse(game.screen, (255,152,0), (mango_x - mango_w//2, mango_y - mango_h//2, mango_w, mango_h))
                except Exception:
                    pygame.draw.ellipse(game.screen, (255,152,0), (mango_x - mango_w//2, mango_y - mango_h//2, mango_w, mango_h))

            # HUD: progress bar + caught count
            try:
                # progress bar dimensions
                bar_w = 220
                bar_h = 14
                bar_x = SCREEN_WIDTH // 2 - bar_w // 2
                bar_y = 16
                # background
                pygame.draw.rect(game.screen, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h))
                # filled portion
                pct = min(1.0, caught / float(target) if target else 0.0)
                fill_w = int(bar_w * pct)
                if fill_w > 0:
                    pygame.draw.rect(game.screen, (100, 200, 100), (bar_x + 1, bar_y + 1, fill_w - 2 if fill_w > 2 else fill_w, bar_h - 2))
                # border
                pygame.draw.rect(game.screen, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 1)
                # textual count
                # use black text for better readability on the progress bar
                txt = game.font.render(f"Seeds: {caught}/{target}", True, (0,0,0))
                game.screen.blit(txt, (bar_x + bar_w + 8, bar_y - 1))
            except Exception:
                try:
                    txt = game.font.render(f"Seeds caught: {caught}/{target}", True, (255,255,255))
                    game.screen.blit(txt, (20, 20))
                except Exception:
                    pass

            # draw overlays: instructions before start, and end screen when finished
            try:
                if show_instructions and not show_end:
                    # Flappy-like white board panel for instructions (dark text on light panel)
                    panel_w = 460
                    panel_h = 180
                    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
                    # white-ish board with slight alpha to blend
                    panel.fill((245, 245, 245, 255))
                    # subtle border
                    try:
                        pygame.draw.rect(panel, (200,200,200), (0, 0, panel_w, panel_h), 2, border_radius=8)
                    except Exception:
                        pass
                    px = SCREEN_WIDTH // 2 - panel_w // 2
                    py = SCREEN_HEIGHT // 2 - panel_h // 2
                    try:
                        game.screen.blit(panel, (px, py))
                        lf = getattr(game, 'large_font', None) or getattr(game, 'title_font', None)
                        sf = getattr(game, 'small_font', None) or getattr(game, 'font', None)
                        if lf:
                            t = lf.render('Feed Mini-Game', True, (20, 20, 20))
                            game.screen.blit(t, t.get_rect(center=(SCREEN_WIDTH//2, py + 36)))
                        lines = [
                            'Move Mango left/right to catch seeds',
                            'Use LEFT and RIGHT arrows to move',
                            'SPACE to start, ESC to return to hub'
                        ]
                        for i, ln in enumerate(lines):
                            if sf:
                                txt = sf.render(ln, True, (40,40,40))
                                game.screen.blit(txt, txt.get_rect(center=(SCREEN_WIDTH//2, py + 80 + i*28)))
                    except Exception:
                        pass

                if show_end:
                    # Flappy-like white board panel for end message
                    panel_w = 460
                    panel_h = 180
                    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
                    panel.fill((245, 245, 245, 255))
                    try:
                        pygame.draw.rect(panel, (200,200,200), (0, 0, panel_w, panel_h), 2, border_radius=8)
                    except Exception:
                        pass
                    px = SCREEN_WIDTH // 2 - panel_w // 2
                    py = SCREEN_HEIGHT // 2 - panel_h // 2
                    try:
                        game.screen.blit(panel, (px, py))
                        lf = getattr(game, 'large_font', None) or getattr(game, 'title_font', None)
                        sf = getattr(game, 'small_font', None) or getattr(game, 'font', None)
                        if lf:
                            msg = lf.render(end_message or 'Well done!', True, (20,20,20))
                            game.screen.blit(msg, msg.get_rect(center=(SCREEN_WIDTH//2, py + 56)))
                        if sf:
                            hint = sf.render('Press R to play again or ESC to return to hub', True, (40,40,40))
                            game.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH//2, py + 112)))
                    except Exception:
                        pass

                try:
                    game.present()
                except Exception:
                    try:
                        pygame.display.flip()
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

        # finish condition: show end screen to avoid flicker and let user choose R or ESC
        if started and not show_end and caught >= target:
            try:
                game.mango_state['hunger'] = 100
                try:
                    game.save_state()
                except Exception:
                    pass
                try:
                    game.hud_messages.append(("Mango is full!", time.time() + 2.0))
                except Exception:
                    pass
            except Exception:
                pass
            # small feedback sound
            try:
                game._play_sfx('thump')
            except Exception:
                pass
            # show end overlay instead of immediately returning
            show_end = True
            end_message = "Congrats! Mango had fun!"

        # tick
        if clock:
            clock.tick(FPS)
        else:
            # avoid busy loop
            time.sleep(1.0 / FPS)

    # ensure state set to exit and restore hub music as a final safety net
    try:
        try:
            game._stop_music()
            if getattr(game, '_music_started', False):
                game._play_music('home')
            else:
                game._queued_music = 'home'
        except Exception:
            pass
    except Exception:
        pass
    try:
        game.state = exit_state
    except Exception:
        pass
