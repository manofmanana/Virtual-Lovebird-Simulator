import sys
import importlib

def run_check():
    try:
        import pygame
        ver = getattr(pygame, '__version__', 'unknown')
        fn = getattr(pygame, '__file__', None)
        print(f"CHECK_PYGAME: OK version={ver} file={fn}")
    except Exception as e:
        print(f"CHECK_PYGAME: IMPORT FAILED: {e!r}")

if __name__ == '__main__':
    run_check()
import sys
import importlib

def run_check():
    try:
        import pygame
        ver = getattr(pygame, '__version__', 'unknown')
        fn = getattr(pygame, '__file__', None)
        print(f"CHECK_PYGAME: OK version={ver} file={fn}")
    except Exception as e:
        print(f"CHECK_PYGAME: IMPORT FAILED: {e!r}")

if __name__ == '__main__':
    run_check()
