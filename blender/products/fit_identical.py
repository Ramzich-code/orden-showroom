"""
Coffee table fit with the design rule enforced: the upper (travertine) and
lower (walnut) platforms are IDENTICAL slabs: same width, depth, thickness,
corner radius. Only vertical position and horizontal offset differ.

Camera fixed (solved from the stone top: az 39, el 19, 50 mm).
Free: shared slab thickness T, upper-slab underside height H, the lower
slab's horizontal offset (dx, dy), and the panel's span along the left side.
Corner radius is scanned and chosen by total residual over BOTH slabs.

    blender -b --factory-startup --python blender/products/fit_identical.py
"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fit_coffee_table as f
from fit_stage2 import outline_y_at

CAM = dict(az=39.0, el=19.0, dist=1186.1 / 591.0, ox=0.0, oy=-24.0)
SLAB_W, SLAB_D = 1.10, 1.02
PANEL_T = 0.03

C = [  # typed constraints measured on the photograph (px)
    ("stone_left_x", 27), ("stone_right_x", 828), ("stone_low_y", 850), ("stone_near_top_y", 811),
    ("wal_low_y", 983), ("wal_low_x", 395, 0.4), ("wal_right_x", 823), ("wal_left_x", 27),
    ("wal_bottom_at_700", 857), ("wal_bottom_at_250", 948), ("wal_topedge_at_700", 812),
    ("pan_tl", (100, 711)), ("pan_tr", (186, 764)), ("pan_br", (182, 938)), ("pan_bl", (100, 877)),
    # left end: the walnut band continues to the left of the panel, well above the floor
    ("wal_bottom_at_60", 801),   # (a highlight at x=300 was rejected: inconsistent with any slab pose)
]
NAMES = ["T", "H", "dx", "dy", "yp_b", "yp_f", "Z"]   # Z = underside height of the lower slab


def evaluate(p, r):
    q = dict(zip(NAMES, p))
    top_z = q["H"] + q["T"]
    cam = f.camera(CAM["az"], CAM["el"], CAM["dist"], np.array([0, 0, top_z]))
    proj = lambda P: f.project(np.asarray(P, float), cam, CAM["ox"], CAM["oy"])
    rr = f.rounded_rect(SLAB_W, SLAB_D, r, n=60)          # ONE outline for both slabs
    s_top = proj(np.c_[rr, np.full(len(rr), top_z)])
    s_bot = proj(np.c_[rr, np.full(len(rr), q["H"])])
    w_rr = rr + [q["dx"], q["dy"]]
    w_top = proj(np.c_[w_rr, np.full(len(w_rr), q["Z"] + q["T"])])
    w_bot = proj(np.c_[w_rr, np.full(len(w_rr), q["Z"])])
    s_all, w_all = np.vstack([s_top, s_bot]), np.vstack([w_top, w_bot])
    wl = w_bot[w_bot[:, 1].argmax()]
    v = {
        "stone_left_x": s_all[:, 0].min(), "stone_right_x": s_all[:, 0].max(),
        "stone_low_y": s_bot[:, 1].max(), "stone_near_top_y": s_top[:, 1].max(),
        "wal_low_y": wl[1], "wal_low_x": wl[0],
        "wal_right_x": w_all[:, 0].max(), "wal_left_x": w_all[:, 0].min(),
        "wal_bottom_at_700": outline_y_at(w_bot, 700, "max"),
        "wal_bottom_at_250": outline_y_at(w_bot, 250, "max"),
        "wal_topedge_at_700": outline_y_at(w_top, 700, "max"),
        "wal_bottom_at_60": outline_y_at(w_bot, 60, "max"),

    }
    xp = q["dx"] - SLAB_W / 2 - PANEL_T          # panel outer face, against the walnut's left end
    for name, (y, z) in {"pan_tl": (q["yp_b"], q["H"]), "pan_tr": (q["yp_f"], q["H"]),
                         "pan_br": (q["yp_f"], 0.0), "pan_bl": (q["yp_b"], 0.0)}.items():
        v[name] = proj([[xp, y, z]])[0]
    return v


def cost(p, r):
    q = dict(zip(NAMES, p))
    v = evaluate(p, r)
    e = 0.0
    for c in C:
        k, ref = c[0], c[1]
        w = c[2] if len(c) > 2 else 1.0
        m = v[k]
        if m is None:
            e += 1e4
        elif isinstance(ref, tuple):
            e += w * ((np.array(m) - np.array(ref)) ** 2).sum()
        else:
            e += w * (m - ref) ** 2
    pen = 1e6 * max(0, 0.03 - q["T"]) ** 2
    pen += 1e6 * max(0, q["Z"] + q["T"] - q["H"] + 0.02) ** 2    # open gap of at least 2 cm
    pen += 1e6 * max(0, -q["Z"]) ** 2
    pen += 1e6 * max(0, q["yp_f"] - q["yp_b"] + 0.05) ** 2
    return e + pen


def main():
    results = []
    for r in (0.16, 0.18, 0.20, 0.22):
        best, bv = None, 1e18
        for s in ([0.075, 0.26, 0.0, 0.0, 0.1, -0.15, 0.10], [0.07, 0.30, -0.05, -0.05, 0.13, -0.12, 0.15], [0.08, 0.24, 0.05, 0.05, 0.2, -0.05, 0.05], [0.07, 0.28, 0.0, 0.0, 0.1, -0.15, 0.0]):
            x = np.array(s, float)
            for _ in range(3):
                x, v = f.nelder_mead(lambda p: cost(p, r), x, [0.01, 0.03, 0.05, 0.05, 0.05, 0.05, 0.04])
            if v < bv:
                best, bv = x, v
        rms = math.sqrt(bv / len(C))
        results.append((rms, r, best))
        print("[FIT] corner r=%.2f  rms %.1f px  %s" % (r, rms, np.round(best, 3)))
    rms, r, best = min(results, key=lambda t: t[0])
    q = dict(zip(NAMES, best))
    v = evaluate(best, r)
    print("[FIT] ==== best corner radius %.2f, rms %.1f px" % (r, rms))
    for c in C:
        print("[FIT]   %-20s ref %-12s model %s" % (c[0], c[1], np.round(v[c[0]], 1)))
    for k, val in q.items():
        print("[FIT] %-5s = %.4f" % (k, val))
    out = dict(camera=CAM, slab=dict(w=SLAB_W, d=SLAB_D, t=q["T"], r=r), H=q["H"], lower_z=q["Z"], offset=[q["dx"], q["dy"]],
               panel=dict(t=PANEL_T, y_back=q["yp_b"], y_front=q["yp_f"]), rms_px=rms)
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "coffee_table_identical_fit.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
