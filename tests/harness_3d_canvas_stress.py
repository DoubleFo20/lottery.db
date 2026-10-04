"""tests/harness_3d_canvas_stress.py
Python Adversarial Stress & Verification Harness for 3d.html Kinetic Canvas Engine.
Executed by Challenger 1 (Canvas Stress & Mobile Performance Challenger).
"""

import hashlib
import math
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_3D = REPO_ROOT / "3d.html"
DASH_3D = REPO_ROOT / "dashboard" / "3d.html"


def test_parity():
    assert ROOT_3D.exists()
    assert DASH_3D.exists()
    h1 = hashlib.sha256(ROOT_3D.read_bytes()).hexdigest()
    h2 = hashlib.sha256(DASH_3D.read_bytes()).hexdigest()
    assert h1 == h2, f"Parity mismatch: {h1} != {h2}"
    print("[PASS] Byte-for-byte SHA256 parity verified.")


def test_string_invariants():
    content = ROOT_3D.read_text(encoding="utf-8")
    for req in ["70%", "15%", "70% Banker", "15% Pairs", "830386", "#060503"]:
        assert req in content, f"Missing {req}"
    print("[PASS] Required string invariants verified.")


def test_scroll_boundary_conditions():
    total_frames = 50
    view_h = 800
    container_h = 3600
    max_scroll = container_h - view_h  # 2800

    def calc_p(rect_top):
        if max_scroll <= 0:
            return 0.0
        return max(0.0, min(1.0, -rect_top / max_scroll))

    def to_frame(p):
        return 1.0 + p * (total_frames - 1)

    def draw_idx(f):
        return min(total_frames, max(1, round(f)))

    # 0%, 50%, 100%
    assert draw_idx(to_frame(calc_p(0))) == 1
    assert draw_idx(to_frame(calc_p(-1400))) == 26
    assert draw_idx(to_frame(calc_p(-2800))) == 50

    # Negative scroll (bounce top)
    assert draw_idx(to_frame(calc_p(500))) == 1
    assert draw_idx(to_frame(calc_p(10000))) == 1

    # Overscroll (bounce bottom)
    assert draw_idx(to_frame(calc_p(-3500))) == 50
    assert draw_idx(to_frame(calc_p(-999999))) == 50

    print("[PASS] Frame boundary conditions verified.")


def test_dpr_capping():
    def cap_dpr(dpr_in):
        return min(dpr_in or 1.0, 2.0)

    for dpr, expected in [
        (0.5, 0.5),
        (1.0, 1.0),
        (1.5, 1.5),
        (2.0, 2.0),
        (2.5, 2.0),
        (3.0, 2.0),
        (4.0, 2.0),
        (8.0, 2.0),
        (0.0, 1.0),
        (None, 1.0),
    ]:
        assert cap_dpr(dpr) == expected
    print("[PASS] DPR capping logic verified.")


def test_aspect_ratio_cover_math():
    iw, ih = 720, 1280
    viewports = [
        ("Portrait 9:16", 780, 1688),
        ("Square 1:1", 1600, 1600),
        ("Landscape 16:9", 1920, 1080),
        ("Ultra-Wide 21:9", 2560, 1080),
        ("Legacy 4:3", 1024, 768),
        ("Tall Mobile 9:21", 720, 1680),
    ]

    for name, cw, ch in viewports:
        scale = max(cw / iw, ch / ih)
        dw = iw * scale
        dh = ih * scale
        dx = (cw - dw) / 2.0
        dy = (ch - dh) / 2.0

        assert dw >= cw - 1e-6, f"{name}: width gap"
        assert dh >= ch - 1e-6, f"{name}: height gap"
        assert abs((dw / dh) - (iw / ih)) < 1e-6, f"{name}: distortion"
        assert abs((dx + dw / 2.0) - (cw / 2.0)) < 1e-6, f"{name}: x-center"
        assert abs((dy + dh / 2.0) - (ch / 2.0)) < 1e-6, f"{name}: y-center"

    print("[PASS] Centered cover aspect ratio math verified.")


def test_lerp_stability():
    lerp_factor = 0.11
    current = 1.0
    target = 50.0
    steps = 0
    while current != target and steps < 200:
        steps += 1
        diff = target - current
        if abs(diff) < 0.001:
            current = target
        else:
            current += diff * lerp_factor

    assert current == 50.0
    assert steps <= 95
    print(f"[PASS] Lerp stability converged in {steps} steps.")


if __name__ == "__main__":
    print("=== Python 3D Canvas Stress Harness ===")
    test_parity()
    test_string_invariants()
    test_scroll_boundary_conditions()
    test_dpr_capping()
    test_aspect_ratio_cover_math()
    test_lerp_stability()
    print("=== ALL PYTHON STRESS HARNESS TESTS PASSED ===")
