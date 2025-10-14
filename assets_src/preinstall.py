import sys
import os
import traceback

def main():
    try:
        print('PREINSTALL: starting')
        # Prefer a dependency-free approach: unzip any .whl files directly into
        # the mounted assets directory (loaderhome). This makes package files
        # available on sys.path without needing pip/aio.pep0723.
        wheel_dir = os.path.join(os.path.dirname(__file__), 'site-packages')
        assets_dir = os.path.dirname(__file__)
        if os.path.isdir(wheel_dir):
            for fn in sorted(os.listdir(wheel_dir)):
                if fn.endswith('.whl'):
                    path = os.path.join(wheel_dir, fn)
                    try:
                        print('PREINSTALL: extracting', path, '->', assets_dir)
                        import zipfile
                        with zipfile.ZipFile(path, 'r') as z:
                            z.extractall(assets_dir)
                        print('PREINSTALL: extracted', path)
                    except Exception:
                        print('PREINSTALL: extract failed for', path)
                        traceback.print_exc()
        else:
            print('PREINSTALL: no wheel dir', wheel_dir)

        # run check_pygame if present
        check = os.path.join(os.path.dirname(__file__), 'check_pygame.py')
        if os.path.isfile(check):
            print('PREINSTALL: running check_pygame')
            try:
                with open(check, 'r') as f:
                    code = f.read()
                exec(compile(code, check, 'exec'), {})
            except Exception:
                print('PREINSTALL: check_pygame failed')
                traceback.print_exc()
        else:
            print('PREINSTALL: check_pygame not found')

    except Exception:
        print('PREINSTALL: unexpected error')
        traceback.print_exc()

if __name__ == '__main__':
    main()
