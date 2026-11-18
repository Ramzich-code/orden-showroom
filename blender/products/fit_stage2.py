"""
Stage 2 fit: camera and stone fixed (verified visually against the photo:
az 39, el 19, 50 mm, stone 1.10 x 1.02 x 0.07). Solves the walnut platform,
the panel and the height of the stone above the floor from typed constraints
measured on the reference photograph.
"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fit_coffee_table as f

CAM = dict(az=39.0, el=19.0, dist=1186.1 / 591.0, ox=0.0, oy=-24.0, Ds=1.02, Ts=0.07)

# typed constraints on the photograph (px)
C = [
    ("wal_bottom_lowest_y", 983, 1.0),     # lowest point of walnut bottom outline
    ("wal_bottom_lowest_x", 395, 0.4),     # (x of that point, weak: rounded corner)
    ("wal_right_x", 823, 1.0),             # rightmost x of walnut
    ("wal_left_x", 27, 1.0),               # leftmost x of walnut (rounded back-left end)
    ("wal_bottom_at_700", 857, 1.0),       # walnut bottom edge y at x=700 (front face)
    ("wal_bottom_at_250", 948, 1.0),       # walnut bottom edge y at x=250 (left face)
    ("wal_topedge_at_700", 812, 1.0),      # walnut top front arris (light line) y at x=700
    ("pan_tl", (100, 711), 1.0), ("pan_tr", (186, 764), 1.0),
    ("pan_br", (182, 938), 1.0), ("pan_bl", (100, 877), 1.0),
]
NAMES = ["H", "Ww", "Dw", "cxw", "cyw", "zwb", "Tw", "xp", "yp_b", "yp_f"]


def proj_setup(H):
    top_z = H + CAM["Ts"]
    cam = f.camera(CAM["az"], CAM["el"], CAM["dist"], np.array([0, 0, top_z]))
    return lambda P: f.project(np.asarray(P, float), cam, CAM["ox"], CAM["oy"])


def outline_y_at(pts, x, mode):
    """y where the closed projected outline crosses the vertical line at x."""
    a, b = pts, np.roll(pts, -1, 0)
    lo, hi = np.minimum(a[:, 0], b[:, 0]), np.maximum(a[:, 0], b[:, 0])
    m = (lo <= x) & (hi >= x) & (hi > lo)
    if not m.any():
        return None
    t = (x - a[m, 0]) / (b[m, 0] - a[m, 0])
    ys = a[m, 1] + t * (b[m, 1] - a[m, 1])
    return ys.max() if mode == "max" else ys.min()


def evaluate(p):
    q = dict(zip(NAMES, p))
    proj = proj_setup(q["H"])
    rr = f.rounded_rect(q["Ww"], q["Dw"], float(os.environ.get("WAL_R", f.R_CORNER)), n=60) + [q["cxw"], q["cyw"]]
    bot = proj(np.c_[rr, np.full(len(rr), q["zwb"])])
    top = proj(np.c_[rr, np.full(len(rr), q["zwb"] + q["Tw"])])
    allp = np.vstack([bot, top])
    low = bot[bot[:, 1].argmax()]
    v = {
        "wal_bottom_lowest_y": low[1], "wal_bottom_lowest_x": low[0],
        "wal_right_x": allp[:, 0].max(), "wal_left_x": allp[:, 0].min(),
        "wal_bottom_at_700": outline_y_at(bot, 700, "max"),
        "wal_bottom_at_250": outline_y_at(bot, 250, "max"),
        "wal_topedge_at_700": outline_y_at(top, 700, "max"),
    }
    for name, (y, z) in {"pan_tl": (q["yp_b"], q["H"]), "pan_tr": (q["yp_f"], q["H"]),
                         "pan_br": (q["yp_f"], 0.0), "pan_bl": (q["yp_b"], 0.0)}.items():
        v[name] = proj([[q["xp"], y, z]])[0]
    return v


VARIANT = os.environ.get("FIT_VARIANT", "free")


def cost(p):
    q = dict(zip(NAMES, p))
    if VARIANT == "floor":
        p = np.array(p, float); p[NAMES.index("zwb")] = 0.0; q["zwb"] = 0.0
    v = evaluate(p)
    e = 0.0
    for k, ref, w in C:
        if VARIANT == "floor" and k == "wal_topedge_at_700" and not os.environ.get("KEEP_TOPEDGE"):
            continue
        m = v[k]
        if m is None:
            e += 1e4
        elif isinstance(ref, tuple):
            e += w * ((np.array(m) - np.array(ref)) ** 2).sum()
        else:
            e += w * (m - ref) ** 2
    pen = 0.0
    for k in ("H", "Ww", "Dw", "Tw"):
        pen += 1e6 * max(0, 0.03 - q[k]) ** 2
    pen += 1e6 * max(0, -q["zwb"]) ** 2
    pen += 1e6 * max(0, q["zwb"] + q["Tw"] - q["H"] + 0.02) ** 2
    pen += 1e6 * max(0, q["yp_f"] - q["yp_b"] + 0.05) ** 2
    if os.environ.get("FIT_TIE_PANEL"):
        # panel (30 mm thick) is fixed against the walnut's left face
        pen += 1e6 * (q["xp"] + 0.03 - (q["cxw"] - q["Ww"] / 2)) ** 2
    return e + pen


def main():
    best, bv = None, 1e18
    starts = [[0.215, 1.10, 1.02, 0, 0, 0.0, 0.095, -0.56, 0.2, -0.05],
              [0.30, 1.05, 1.10, 0.03, 0.08, 0.05, 0.09, -0.53, 0.15, -0.1],
              [0.28, 0.95, 1.15, 0.07, 0.12, 0.0, 0.12, -0.50, 0.0, -0.25],
              [0.25, 1.1, 0.95, -0.02, -0.05, 0.08, 0.08, -0.56, 0.3, 0.05]]
    for s in starts:
        x = np.array(s, float)
        for _ in range(4):
            x, v = f.nelder_mead(cost, x, [0.04, 0.06, 0.06, 0.04, 0.04, 0.03, 0.02, 0.04, 0.06, 0.06])
        print("[FIT] start ->", round(v, 1))
        if v < bv:
            best, bv = x, v
    if VARIANT == "floor":
        best[NAMES.index("zwb")] = 0.0
    q = dict(zip(NAMES, best))
    v = evaluate(best)
    print("[FIT] variant:", VARIANT, " cost:", round(bv, 1))
    print("[FIT] residuals:")
    for k, ref, w in C:
        m = v[k]
        print("[FIT]   %-22s ref %-12s model %s" % (k, ref, np.round(m, 1)))
    for k, val in q.items():
        print("[FIT] %-4s = %.4f" % (k, val))
    json.dump({"camera": CAM, "params": q, "variant": VARIANT}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"coffee_table_fit_{VARIANT}.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
