"""AudioManager: compact, reliable, and tested-friendly.

This module offers a single AudioManager class with a small, stable API
used by project.py. It uses pygame when available and creates small
placeholder WAV files when real assets are missing so the game can run
in CI or on development machines without shipping audio assets.
"""

import os
import math
import time
try:
    import wave
except Exception:
    # wave may not be available in some WASM/python builds; guard usage below
    wave = None
import struct

try:
    import pygame
except Exception:
    pygame = None


class AudioManager:
    """Compact audio manager.

    Public API used by project.py:
    - ensure_audio_ready() -> bool
    - load_sounds()
    - play_music(key)
    - stop_music()
    - play_sfx(key, maxtime=None)
    - play_debug_tone(freq, duration_ms, volume)
    - start_watchdog(key='forest', interval=1.0)
    - stop_watchdog()
    - watchdog_tick()

    The manager mirrors a few attributes onto `owner` for backwards
    compatibility: `sounds`, `_music_files`, `_music_playing`, `_music_mode`,
    `_music_watchdog`.
    """

    def __init__(self, owner):
        self.owner = owner
        self.sounds = {}
        self._music_files = {}

        # watchdog state
        self._watchdog_enabled = False
        self._watchdog_key = None
        self._watchdog_interval = 1.0
        self._watchdog_last = 0.0

        # mirror expected owner attributes where code expects them
        try:
            setattr(self.owner, 'sounds', self.sounds)
            setattr(self.owner, '_music_files', self._music_files)
            setattr(self.owner, '_music_playing', None)
            setattr(self.owner, '_music_mode', None)
            setattr(self.owner, '_music_watchdog', False)
        except Exception:
            # owner may be a simple object in tests
            pass
        # Reserve a dedicated channel index for fallback music so SFX don't steal it
        # Pick a high channel index to avoid collisions with tests/examples
        self._reserved_music_channel_index = 15
        # Do not initialize the mixer at import time; use ensure_audio to init on first user gesture
        self._mixer_initialized = False

    def ensure_audio(self):
        """Ensure the pygame mixer is initialized and sounds are loaded.

        This is safe to call multiple times and is intended to be invoked
        on the first user gesture in web builds to satisfy browser autoplay
        restrictions.
        """
        if self._mixer_initialized:
            return True
        if not pygame:
            return False
        
        # Detect WASM environment
        try:
            import sys
            is_wasm = sys.platform == 'emscripten' or hasattr(sys, '_emscripten_info')
        except Exception:
            is_wasm = False
            
        try:
            # In WASM, use minimal mixer initialization
            if is_wasm:
                try:
                    # Use simpler parameters for WASM
                    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
                except Exception:
                    try:
                        pygame.mixer.init()
                    except Exception:
                        return False
            else:
                # Desktop: use high-quality parameters
                try:
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                except Exception:
                    try:
                        pygame.mixer.init()
                    except Exception:
                        return False
            try:
                pygame.mixer.set_num_channels(16)  # Reduce channels for WASM
            except Exception:
                pass
            self._mixer_initialized = True
            # Load sounds now that mixer is available
            try:
                self.load_sounds()
            except Exception:
                pass
            return True
        except Exception:
            return False

    # --- WAV placeholder writers ------------------------------------------------
    def write_short_tone(self, path, freq=1500, duration_ms=160, volume=1.0):
        # Some runtimes (pygbag/wasm) don't include the `wave` stdlib module.
        # Prefer to skip placeholder file generation in that case to avoid
        # raising ModuleNotFoundError during import. On desktop, the original
        # behavior is preserved.
        if wave is None:
            return False
        try:
            framerate = 44100
            amplitude = int(32767 * max(0.0, min(1.0, volume)))
            nframes = int(framerate * duration_ms / 1000)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with wave.open(path, 'w') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(framerate)
                for i in range(nframes):
                    t = i / framerate
                    val = int(amplitude * math.sin(2 * math.pi * freq * t))
                    wf.writeframes(struct.pack('<hh', val, val))
            return True
        except Exception:
            return False

    def write_thump(self, path, duration_ms=220, volume=0.9):
        if wave is None:
            return False
        try:
            framerate = 44100
            amplitude = int(32767 * max(0.0, min(1.0, volume)))
            nframes = int(framerate * duration_ms / 1000)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with wave.open(path, 'w') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(framerate)
                for i in range(nframes):
                    t = i / framerate
                    env = (1.0 - (i / float(nframes)))
                    val = int(amplitude * env * math.sin(2 * math.pi * 120 * t))
                    wf.writeframes(struct.pack('<hh', val, val))
            return True
        except Exception:
            return False

    # --- mixer helpers ---------------------------------------------------------
    def ensure_audio_ready(self):
        if not pygame:
            return False
        try:
            if not pygame.mixer.get_init():
                # prefer explicit params but fall back to defaults if they fail
                try:
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                except Exception:
                    try:
                        pygame.mixer.init()
                    except Exception:
                        return False
            try:
                pygame.mixer.set_num_channels(32)
            except Exception:
                pass
            return True
        except Exception:
            return False

    def apply_volume_settings(self):
        if not pygame:
            return
        
        # Detect WASM environment
        try:
            import sys
            is_wasm = sys.platform == 'emscripten' or hasattr(sys, '_emscripten_info')
        except Exception:
            is_wasm = False
            
        try:
            if pygame.mixer.get_init():
                try:
                    # In WASM, avoid pygame.mixer.music (causes crashes)
                    # Only handle music if not in WASM and using music mode
                    if not is_wasm and getattr(self.owner, '_music_mode', None) == 'music':
                        try:
                            pygame.mixer.music.set_volume(self.owner.music_volume * self.owner.master_volume)
                        except Exception:
                            pass
                except Exception:
                    pass
            for s in list(self.sounds.keys()):
                try:
                    if self.sounds.get(s):
                        self.sounds[s].set_volume(self.owner.sfx_volume * self.owner.master_volume)
                except Exception:
                    pass
            # If music was started as a Sound on a channel, update that channel's volume
            try:
                if getattr(self.owner, '_music_mode', None) == 'sound':
                    ch = getattr(self.owner, '_music_channel', None)
                    if ch:
                        try:
                            ch.set_volume(self.owner.music_volume * self.owner.master_volume)
                        except Exception:
                            pass
            except Exception:
                pass
        except Exception:
            pass

    # --- loading and placeholders ----------------------------------------------
    def load_sounds(self):
        base = os.path.join('assets', 'sounds')
        os.makedirs(base, exist_ok=True)
        # Prefer OGG files in web builds (pygbag) for browser-friendly playback.
        def pick_ext(name):
            ogg = os.path.join(base, f"{name}.ogg")
            wav = os.path.join(base, f"{name}.wav")
            if os.path.exists(ogg):
                return ogg
            return wav

        flap = pick_ext('flap')
        thump = pick_ext('thump')

        # create placeholders if missing (safe for CI)
        if not os.path.exists(flap):
            try:
                self.write_short_tone(flap, freq=1200, duration_ms=220, volume=0.9)
            except Exception:
                pass
        if not os.path.exists(thump):
            try:
                self.write_thump(thump, duration_ms=260, volume=0.9)
            except Exception:
                pass

        # Known SFX mapping used by project.py
        # SFX map: prefer .ogg when available; pick_ext will select available file
        sfx_map = {
            'flap': os.path.basename(pick_ext('flap')),
            'thump': os.path.basename(pick_ext('thump')),
            'button': os.path.basename(pick_ext('buttonpressed')),
            'medicine': os.path.basename(pick_ext('medicine')),
            'chirp': os.path.basename(pick_ext('chirp')),
        }

        if pygame and pygame.mixer.get_init():
            try:
                for key, fname in sfx_map.items():
                    p = os.path.join(base, fname)
                    if os.path.exists(p):
                        try:
                            self.sounds[key] = pygame.mixer.Sound(p)
                        except Exception:
                            # keep going if a particular SFX fails to load
                            pass
            except Exception:
                pass

        # Debug: log which SFX keys were loaded (for diagnostics)
        try:
            loaded = sorted([k for k, v in self.sounds.items() if not k.startswith('_') and v])
            msg = f"[audio] load_sounds: loaded keys={loaded}"
            print(msg)
            try:
                with open('audio_debug.log', 'a') as _lf:
                    _lf.write(msg + '\n')
            except Exception:
                pass
        except Exception:
            pass

        # Music: prefer OGG for web builds
        self._music_files = {
            'forest': pick_ext('forest'),
            'home': pick_ext('home')
        }

        for k, p in self._music_files.items():
            if not os.path.exists(p):
                try:
                    # longer placeholder for music
                    self.write_short_tone(p, freq=400, duration_ms=2000, volume=0.6)
                except Exception:
                    pass

        try:
            setattr(self.owner, 'sounds', self.sounds)
            setattr(self.owner, '_music_files', self._music_files)
        except Exception:
            pass

        try:
            self.apply_volume_settings()
        except Exception:
            pass

    # --- channel helpers ----------------------------------------------------
    def _get_sfx_channel(self):
        """Return a free channel for SFX that avoids the reserved music channel.

        This helper will try to find a free channel, and if the found channel
        matches the reserved music channel index it will try to find another
        free channel or pick a safe fallback.
        """
        if not pygame:
            return None
        try:
            ch = pygame.mixer.find_channel()
            if ch:
                # Avoid using the reserved music channel
                if getattr(ch, 'get_id', None):
                    cid = ch.get_id()
                else:
                    # Some pygame versions don't expose get_id on Channel
                    cid = None
                if cid == self._reserved_music_channel_index:
                    # try to get another channel explicitly
                    for i in range(pygame.mixer.get_num_channels()):
                        if i == self._reserved_music_channel_index:
                            continue
                        try:
                            c2 = pygame.mixer.Channel(i)
                            if not c2.get_busy():
                                return c2
                        except Exception:
                            continue
                    # last resort: return the found channel anyway
                    return ch
                return ch
            # If find_channel returned None, try to allocate a non-reserved channel
            try:
                # try a few indices avoiding the reserved one
                total = pygame.mixer.get_num_channels()
                for i in range(total):
                    if i == self._reserved_music_channel_index:
                        continue
                    try:
                        c = pygame.mixer.Channel(i)
                        if not c.get_busy():
                            return c
                    except Exception:
                        continue
            except Exception:
                pass
            # fallback to channel 0 if everything else fails
            try:
                return pygame.mixer.Channel(0)
            except Exception:
                return None
        except Exception:
            return None

    # --- playback -------------------------------------------------------------
    def play_music(self, key):
        try:
            if key not in self._music_files:
                return
            path = self._music_files.get(key)
            if not os.path.exists(path):
                return
            if not pygame:
                return
                
            # Detect WASM environment
            try:
                import sys
                is_wasm = sys.platform == 'emscripten' or hasattr(sys, '_emscripten_info')
            except Exception:
                is_wasm = False
                
            # If already playing this key and the backend reports busy, do nothing
            try:
                cur = getattr(self.owner, '_music_playing', None)
                mode = getattr(self.owner, '_music_mode', None)
                if cur == key:
                    if mode == 'music' and not is_wasm:
                        try:
                            if pygame.mixer.music.get_busy():
                                return
                        except Exception:
                            return
                    if mode == 'sound':
                        try:
                            ch = getattr(self.owner, '_music_channel', None)
                            if ch and ch.get_busy():
                                return
                        except Exception:
                            return
            except Exception:
                pass
                
            # In WASM, skip pygame.mixer.music (causes crashes) and use Sound fallback
            if not is_wasm:
                # Try streaming playback (preferred on desktop)
                try:
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.set_volume(self.owner.music_volume * self.owner.master_volume)
                    pygame.mixer.music.play(-1)
                    try:
                        setattr(self.owner, '_music_playing', key)
                        setattr(self.owner, '_music_mode', 'music')
                    except Exception:
                        pass
                    # debug log
                    try:
                        msg = f"[audio] music.play() started for {key} -> {path} (vol={self.owner.music_volume * self.owner.master_volume:.3f})"
                        print(msg)
                        with open('audio_debug.log', 'a') as _lf:
                            _lf.write(msg + '\n')
                    except Exception:
                        pass
                    return
                except Exception:
                    pass  # Fall through to Sound fallback
                    
            # WASM or streaming failed: fallback to Sound playback on a reserved channel
            try:
                snd = pygame.mixer.Sound(path)
                # find a dedicated channel (prefer the reserved music channel)
                try:
                    ch = pygame.mixer.Channel(self._reserved_music_channel_index)
                except Exception:
                    ch = pygame.mixer.find_channel() or pygame.mixer.Channel(0)
                # play as looping sound
                try:
                    ch.play(snd, loops=-1)
                except Exception:
                    try:
                        ch = snd.play(loops=-1)
                    except Exception:
                        ch = None
                # set volumes
                try:
                    if ch:
                        ch.set_volume(self.owner.music_volume * self.owner.master_volume)
                except Exception:
                    pass
                # keep a reference so the Sound isn't GC'd and mirror state onto owner
                try:
                    self.sounds[f'_music_{key}'] = snd
                except Exception:
                    pass
                # mirror state onto owner
                try:
                    setattr(self.owner, '_music_channel', ch)
                    setattr(self.owner, '_music_playing', key)
                    setattr(self.owner, '_music_mode', 'sound')
                except Exception:
                    pass
                # debug log
                try:
                    msg = f"[audio] fallback Sound.play() started for {key} -> {path} (vol={self.owner.music_volume * self.owner.master_volume:.3f})"
                    print(msg)
                    with open('audio_debug.log', 'a') as _lf:
                        _lf.write(msg + '\n')
                except Exception:
                    pass
                return
            except Exception:
                # final failure
                try:
                    msg = f"[audio] could not play music {key}"
                    print(msg)
                    with open('audio_debug.log', 'a') as _lf:
                        _lf.write(msg + '\n')
                except Exception:
                    pass
                return
        except Exception:
            try:
                msg = f"[audio] could not play music {key} (outer)"
                print(msg)
                with open('audio_debug.log', 'a') as _lf:
                    _lf.write(msg + '\n')
            except Exception:
                pass

    def stop_music(self):
        try:
            # Detect WASM environment
            try:
                import sys
                is_wasm = sys.platform == 'emscripten' or hasattr(sys, '_emscripten_info')
            except Exception:
                is_wasm = False
                
            # stop streaming music if used (skip in WASM)
            try:
                if not is_wasm and getattr(self.owner, '_music_mode', None) == 'music':
                    if pygame:
                        try:
                            pygame.mixer.music.stop()
                        except Exception:
                            pass
            except Exception:
                pass
            # stop fallback sound-based music
            try:
                if getattr(self.owner, '_music_mode', None) == 'sound':
                    ch = getattr(self.owner, '_music_channel', None)
                    if ch:
                        try:
                            ch.stop()
                        except Exception:
                            pass
                    # also remove stored sound object
                    try:
                        key = getattr(self.owner, '_music_playing', None)
                        if key:
                            self.sounds.pop(f'_music_{key}', None)
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass
        try:
            setattr(self.owner, '_music_playing', None)
            setattr(self.owner, '_music_mode', None)
            try:
                setattr(self.owner, '_music_channel', None)
            except Exception:
                pass
        except Exception:
            pass

    def play_sfx(self, key, maxtime=None):
        try:
            # Diagnostic log - announce attempt
            try:
                msg = f"[audio] _play_sfx: attempt to play key='{key}'"
                print(msg)
                try:
                    with open('audio_debug.log', 'a') as _lf:
                        _lf.write(msg + '\n')
                except Exception:
                    pass
            except Exception:
                pass

            if not pygame:
                return
            snd = self.sounds.get(key)
            if not snd:
                try:
                    msg = f"[audio] _play_sfx: missing sound for key='{key}'"
                    print(msg)
                    with open('audio_debug.log', 'a') as _lf:
                        _lf.write(msg + '\n')
                except Exception:
                    pass
                return
            try:
                snd.set_volume(max(0.0, min(1.0, self.owner.sfx_volume * self.owner.master_volume)))
            except Exception:
                pass
            try:
                ch = self._get_sfx_channel() or (pygame.mixer.Channel(0) if pygame else None)
                played = False
                if maxtime is not None:
                    try:
                        ch.play(snd, maxtime=maxtime)
                        played = True
                    except TypeError:
                        ch.play(snd)
                        played = True
                else:
                    ch.play(snd)
                    played = True
                # log success
                try:
                    vol = None
                    try:
                        vol = ch.get_volume()
                    except Exception:
                        vol = None
                    msg = f"[audio] _play_sfx: played '{key}' on channel {ch} (set_vol={self.owner.sfx_volume * self.owner.master_volume:.3f} read_vol={vol})"
                    print(msg)
                    try:
                        with open('audio_debug.log', 'a') as _lf:
                            _lf.write(msg + '\n')
                    except Exception:
                        pass
                except Exception:
                    pass
            except Exception:
                try:
                    snd.play()
                    try:
                        msg = f"[audio] _play_sfx: fallback played '{key}' via Sound.play()"
                        print(msg)
                        with open('audio_debug.log', 'a') as _lf:
                            _lf.write(msg + '\n')
                    except Exception:
                        pass
                except Exception:
                    try:
                        msg = f"[audio] _play_sfx: failed to play '{key}'"
                        print(msg)
                        with open('audio_debug.log', 'a') as _lf:
                            _lf.write(msg + '\n')
                    except Exception:
                        pass
        except Exception:
            pass

    def play_debug_tone(self, freq=800, duration_ms=300, volume=1.0):
        try:
            debug_path = os.path.join('assets', 'sounds', '_debug_tone.wav')
            if not os.path.exists(os.path.dirname(debug_path)):
                os.makedirs(os.path.dirname(debug_path), exist_ok=True)
            if not os.path.exists(debug_path):
                try:
                    self.write_short_tone(debug_path, freq=freq, duration_ms=duration_ms, volume=volume)
                except Exception:
                    pass
            if pygame and os.path.exists(debug_path):
                try:
                    snd = pygame.mixer.Sound(debug_path)
                    ch = pygame.mixer.find_channel() or pygame.mixer.Channel(0)
                    ch.set_volume(1.0)
                    ch.play(snd)
                except Exception:
                    try:
                        snd.play()
                    except Exception:
                        pass
        except Exception:
            pass

    # --- watchdog -------------------------------------------------------------
    def start_watchdog(self, key='forest', interval=1.0):
        try:
            self._watchdog_enabled = True
            self._watchdog_key = key
            try:
                self._watchdog_interval = float(interval)
            except Exception:
                self._watchdog_interval = 1.0
            self._watchdog_last = 0.0
            try:
                setattr(self.owner, '_music_watchdog', True)
            except Exception:
                pass
        except Exception:
            pass

    def stop_watchdog(self):
        try:
            self._watchdog_enabled = False
            self._watchdog_key = None
            try:
                setattr(self.owner, '_music_watchdog', False)
            except Exception:
                pass
        except Exception:
            pass

    def watchdog_tick(self):
        try:
            if not self._watchdog_enabled:
                return
            now = time.time()
            if now - self._watchdog_last < self._watchdog_interval:
                return
            self._watchdog_last = now
            key = self._watchdog_key
            if not key:
                return
            try:
                if getattr(self.owner, '_music_playing', None) != key:
                    return
            except Exception:
                pass
            busy = False
            try:
                if getattr(self.owner, '_music_mode', None) == 'music':
                    busy = bool(pygame.mixer.music.get_busy()) if pygame else False
                elif getattr(self.owner, '_music_mode', None) == 'sound':
                    ch = getattr(self.owner, '_music_channel', None)
                    if ch:
                        try:
                            busy = bool(ch.get_busy())
                        except Exception:
                            busy = True
                    else:
                        busy = False
            except Exception:
                busy = True
            if not busy:
                try:
                    self.play_music(key)
                except Exception:
                    pass
        except Exception:
            pass
