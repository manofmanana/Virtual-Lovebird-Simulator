# Repository-level pythonrc.py - used to configure startup for web builds.
# Add any site-wide initialization you want executed before main.py.
# Keep this small and safe: avoid blocking operations.

# Example: enable the debug console for pygbag builds when the page URL has #debug
try:
    import sys
    if hasattr(sys, 'argv'):
        # simple flag you can check in your code if needed
        __PYRC__ = True
except Exception:
    pass

# You can add site-wide imports or small helper functions here.
