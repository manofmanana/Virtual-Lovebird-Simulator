"""Simple Tickle minigame: click Mango to tickle him and increase happiness.

Exports: play_tickle_minigame(game, tickle_state, exit_state)
"""
import time
import random
try:
    import pygame
except Exception:
    pygame = None
import math
import os

try:
    import project as _project
except Exception:
    _project = None


def play_tickle_minigame(game, tickle_state, exit_state):
    try:
        game.state = tickle_state
    except Exception:
        pass

    SCREEN_WIDTH = getattr(_project, 'SCREEN_WIDTH', game.screen.get_width())
    SCREEN_HEIGHT = getattr(_project, 'SCREEN_HEIGHT', game.screen.get_height())
    FPS = getattr(_project, 'FPS', 60)

    # use floats for smooth movement
    mango_x = float(SCREEN_WIDTH // 2)
    mango_y = float(SCREEN_HEIGHT // 2)
    mango_w = 120
    mango_h = 96

    # movement state
    vx = 0.0
    vy = 0.0
    # increase base speed to make the mini-game more challenging
    speed = 480.0  # px per second approximate (was 220)

    particles = []
    clock = pygame.time.Clock() if pygame else None
    tickles = 0
    target = 12
    running = True
    started = False
    show_instructions = True
    show_end = False
    end_message = ""
    # Try to load easter-egg image 'ericv.png' (optional)
    eric_img = None
    try:
        possible_paths = [
            os.path.join('assets', 'sprites', 'ericv.png'),
            os.path.join('assets', 'ericv.png'),
            'ericv.png'
        ]
        for p in possible_paths:
            try:
                if os.path.exists(p):
                    im = pygame.image.load(p)
                    eric_img = im.convert_alpha()
                    break
            except Exception:
                continue
    except Exception:
        eric_img = None

    # Play cheerful music for tickle (use same minigame music as others: 'forest')
    try:
        if getattr(game, '_music_started', False):
            game._play_music('forest')
        else:
            game._queued_music = 'forest'
    except Exception:
        pass

    last_time = time.time()
    while running and getattr(game, 'state', None) == tickle_state:
        now = time.time()
        dt = now - last_time if now > last_time else 1.0 / FPS
        last_time = now

        if pygame:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                elif event.type == pygame.KEYDOWN:
                    if not started:
                        # space to start
                        if event.key == pygame.K_SPACE:
                            started = True
                            show_instructions = False
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                            break
                    else:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                            break
                        if show_end:
                            if event.key == pygame.K_r:
                                # reset game
                                tickles = 0
                                started = False
                                show_instructions = True
                                show_end = False
                                end_message = ""
                        
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and started and not show_end:
                    mx, my = event.pos
                    rect = pygame.Rect(mango_x - mango_w//2, mango_y - mango_h//2, mango_w, mango_h)
                    if rect.collidepoint(mx, my):
                        tickles += 1
                        # spawn particle on sprite
                        try:
                            if hasattr(game, 'particle_system') and game.particle_system:
                                # spawn directly over sprite
                                game.particle_system.add_button_effect(mx, my, 'tickle')
                                game.particle_system.add_sprite_animation('tickle')
                        except Exception:
                            pass
                        try:
                            game._play_sfx('chirp')
                        except Exception:
                            pass
                        if tickles >= target:
                            try:
                                game.mango_state['happiness'] = min(100, game.mango_state.get('happiness', 0) + 20)
                                if hasattr(game, 'misbehavior_count'):
                                    game.misbehavior_count = max(0, game.misbehavior_count - 2)
                                game.save_state()
                            except Exception:
                                pass
                            # end state
                            show_end = True
                            end_message = "Congrats! Mango had fun!"

        # draw
        try:
            try:
                game.draw_hub_background()
            except Exception:
                game.screen.fill((135,206,250))
            # title
            try:
                t = game.title_font.render('Tickle Mango!', True, (255,255,255))
                game.screen.blit(t, t.get_rect(center=(SCREEN_WIDTH//2, 60)))
            except Exception:
                pass
                # draw mango: movement when started
            sprite_drawn = False
            try:
                if started and not show_end:
                    # move mango randomly across screen - more frequent and faster wandering
                    # choose a new random velocity target more often for erratic motion
                    if random.random() < 0.08:
                        angle = random.uniform(0, 2 * math.pi)
                        mult = random.uniform(0.7, 1.4)
                        vx = math.cos(angle) * speed * mult
                        vy = math.sin(angle) * speed * mult
                    # integrate movement scaled by dt (keep as floats for smoothness)
                    mango_x += vx * dt
                    mango_y += vy * dt
                    # bounds
                    mango_x = max(float(mango_w//2), min(float(SCREEN_WIDTH - mango_w//2), mango_x))
                    mango_y = max(float(mango_h//2), min(float(SCREEN_HEIGHT - mango_h//2), mango_y))
                    # show moving sprite if available (mango_still when flying/moving)
                    try:
                        if hasattr(game, 'mango_sprites') and game.mango_sprites.get('still'):
                            sp = game.mango_sprites.get('still')
                            s = pygame.transform.smoothscale(sp, (mango_w, mango_h))
                            game.screen.blit(s, s.get_rect(center=(int(mango_x), int(mango_y))))
                            sprite_drawn = True
                    except Exception:
                        sprite_drawn = False
                # when not moving (pre-start or paused), show mood-based sprite
                if not sprite_drawn:
                    try:
                        mood = game.get_mango_mood()
                        sprite_name = None
                        if hasattr(game, 'particle_system') and game.particle_system:
                            sprite_name = game.particle_system.get_current_sprite(None)
                        if sprite_name and sprite_name.replace('mango_','') in getattr(game, 'mango_sprites', {}):
                            sp = game.mango_sprites.get(sprite_name.replace('mango_',''))
                        else:
                            sp = game.mango_sprites.get(mood if mood in game.mango_sprites else 'idle')
                        if sp:
                            s = pygame.transform.smoothscale(sp, (mango_w, mango_h))
                            game.screen.blit(s, s.get_rect(center=(int(mango_x), int(mango_y))))
                            sprite_drawn = True
                    except Exception:
                        sprite_drawn = False
                if not sprite_drawn:
                    pygame.draw.ellipse(game.screen, (255,152,0), (int(mango_x) - mango_w//2, int(mango_y) - mango_h//2, mango_w, mango_h))
            except Exception:
                try:
                    pygame.draw.ellipse(game.screen, (255,152,0), (int(mango_x) - mango_w//2, int(mango_y) - mango_h//2, mango_w, mango_h))
                except Exception:
                    pass

            # draw particles from game's particle system if present (on sprite and hub)
            try:
                if hasattr(game, 'particle_system') and game.particle_system:
                    game.particle_system.update(dt)
                    game.particle_system.draw(game.screen)
            except Exception:
                pass

            # progress / instructions / end messages (Flappy-like board styling)
            try:
                panel_w = 460
                panel_h = 220
                panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
                # dark panel background similar to Flappy's board
                panel_surf.fill((24, 24, 24, 230))
                # subtle border
                try:
                    pygame.draw.rect(panel_surf, (255,255,255,30), (0, 0, panel_w, panel_h), 2)
                except Exception:
                    pass
                px = SCREEN_WIDTH // 2 - panel_w // 2
                py = SCREEN_HEIGHT // 2 - panel_h // 2 + 40

                if not started and show_instructions:
                    # draw panel and instructions
                    try:
                        # draw background panel as subtle backdrop
                        game.screen.blit(panel_surf, (px, py))

                        # Position Eric to the right of the panel, even larger
                        eric_w, eric_h = 600, 600
                        # Position Eric so he slightly overlaps the panel (keeps him visible)
                        eric_x = px + panel_w - (eric_w // 3)
                        # lower Eric vertically so he sits more naturally beside the panel
                        eric_y = py + (panel_h // 2) - (eric_h // 2) + 120
                        if eric_img:
                            try:
                                ers = pygame.transform.smoothscale(eric_img, (eric_w, eric_h))
                                game.screen.blit(ers, ers.get_rect(topleft=(eric_x, eric_y)))
                            except Exception:
                                pass

                        # Draw a speech-bubble style instruction box that matches
                        # the overlay area of the grey panel so text stays readable
                        bubble_x = px + 12
                        bubble_y = py + 18
                        bubble_w = panel_w - 36
                        bubble_h = panel_h - 64
                        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_w, bubble_h)
                        try:
                            # light bubble with dark border (no pointer)
                            pygame.draw.rect(game.screen, (255,255,255), bubble_rect, border_radius=14)
                            pygame.draw.rect(game.screen, (30,30,30), bubble_rect, 2, border_radius=14)
                        except Exception:
                            pass

                        title = getattr(game, 'title_font', None)
                        lf = getattr(game, 'large_font', None)
                        sf = getattr(game, 'small_font', None)
                        # Center the title and lines inside the bubble for better readability
                        try:
                            if title:
                                t = title.render('Tickle Mango!', True, (20,20,20))
                                game.screen.blit(t, t.get_rect(center=(bubble_x + bubble_w // 2, bubble_y + 26)))
                            lines = [
                                "Click on Mango to tickle him!",
                                "Mango will fly around once the game starts.",
                                "Controls: Click = Tickle, SPACE = Start, ESC = Back"
                            ]
                            for i, ln in enumerate(lines):
                                if sf:
                                    txt = sf.render(ln, True, (30,30,30))
                                    txt_rect = txt.get_rect(center=(bubble_x + bubble_w // 2, bubble_y + 62 + i * 28))
                                    game.screen.blit(txt, txt_rect)
                        except Exception:
                            pass
                    except Exception:
                        pass
                elif show_end:
                    try:
                        # draw panel and end message
                        game.screen.blit(panel_surf, (px, py))
                        lf = getattr(game, 'large_font', None)
                        sf = getattr(game, 'small_font', None)
                        if lf:
                            msg = lf.render(end_message or 'Well done!', True, (255,255,255))
                            game.screen.blit(msg, msg.get_rect(center=(SCREEN_WIDTH//2, py + 70)))
                        if sf:
                            hint = sf.render('Press R to play again or ESC to return to hub', True, (220,220,220))
                            game.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH//2, py + 120)))
                    except Exception:
                        pass
                else:
                    txt = game.small_font.render(f"Tickles: {tickles}/{target}", True, (255,255,255))
                    game.screen.blit(txt, (20, 20))
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

        if clock:
            clock.tick(FPS)
        else:
            time.sleep(1.0 / FPS)

    # restore hub music
    try:
        game._stop_music()
        if getattr(game, '_music_started', False):
            game._play_music('home')
        else:
            game._queued_music = 'home'
    except Exception:
        pass

    try:
        game.state = exit_state
    except Exception:
        pass
    return True
