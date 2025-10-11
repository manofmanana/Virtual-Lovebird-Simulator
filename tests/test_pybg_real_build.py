import os
import shutil
import sys
import subprocess
import pytest


def test_real_pybg_build_if_available(tmp_path):
    """If pygbag is installed in the environment, run a real build and
    assert expected artifacts exist. Otherwise skip the test.
    """
    try:
        import pygbag  # type: ignore
    except Exception:
        pytest.skip("pygbag not installed in this environment")

    out = str(tmp_path / "pygbag_real")
    if os.path.exists(out):
        shutil.rmtree(out)

    # Try the more modern invocation first (--build --package), then
    # fallback to older/alternate flag (--output) if needed.
    cmds = [
        [sys.executable, "-m", "pygbag", "--build", "--package", out, "main.py"],
        [sys.executable, "-m", "pygbag", "--output", out, "main.py"],
    ]
    last_err = None
    ok = False
    for cmd in cmds:
        try:
            cp = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ok = True
            break
        except subprocess.CalledProcessError as e:
            # save last error for debugging if both fail
            last_err = e
            continue

    if not ok:
        msg = f"pygbag build failed; last stdout:\n{last_err.output.decode(errors='replace') if last_err else ''}\nlast stderr:\n{last_err.stderr.decode(errors='replace') if last_err else ''}"
        pytest.fail(msg)

    # Determine where pygbag actually wrote files. Newer pygbag writes into
    # build/web by default, older invocations may write into the provided out dir.
    candidates = [out, os.path.join(os.getcwd(), 'build', 'web')]
    found = None
    for c in candidates:
        idx = os.path.join(c, "index.html")
        if os.path.exists(idx):
            found = c
            break

    assert found is not None, f"No index.html found in candidates: {candidates}"

    # wasm or js runtime might live under different names; check presence of any .wasm or .js
    entries = [os.path.join(found, f) for f in os.listdir(found)]
    has_wasm = any(p.endswith('.wasm') for p in entries)
    has_js = any(p.endswith('.js') for p in entries)
    has_apk = any(p.endswith('.apk') for p in entries)
    has_zip = any(p.endswith('.zip') for p in entries)
    # Some pygbag builds produce APKs or zipped bundles instead of JS/WASM files
    assert has_wasm or has_js or has_apk or has_zip, (
        f"No .wasm, .js, .apk or .zip files found in build at {found}; entries={entries}"
    )
