import os
import shutil

from package_web import build


def test_simulated_build_creates_output(tmp_path):
    out = str(tmp_path / "pygbag_sim")
    if os.path.exists(out):
        shutil.rmtree(out)
    ok = build(output=out, simulate=True, clean=True)
    assert ok is True
    index = os.path.join(out, "index.html")
    assert os.path.exists(index)
    # index should contain the simulated title
    with open(index, "r", encoding="utf-8") as fh:
        data = fh.read()
    assert "Mango Web Build (simulated)" in data
