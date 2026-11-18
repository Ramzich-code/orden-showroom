"""
Coffee table fit following the client's front-view sketch:
  * two identical slabs, aligned left-right (no lateral offset in front view)
  * one walnut panel OUTSIDE the left ends of both slabs, touching them,
    standing on the floor; its top height is solved
  * the lower slab is carried by the panel (free height), and may be offset
    front/back only
Camera fixed (az 39, el 19, 50 mm). Slab 1.10 x 1.02, thickness 0.07.

    blender -b --factory-startup --python blender/products/fit_outboard.py
"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fit_coffee_table as f
import fit_identical as fi

T, R = 0.07, 0.18
NAMES = ["H", "dy", "yp_b", "yp_f", "Z", "PT"]   # PT = height of the panel's top


def evaluate(p):
    q = dict(zip(NAMES, p))
    full = np.array([T, q["H"], 0.0, q["dy"], q["yp_b"], q["yp_f"], q["Z"]])
    v = fi.evaluate(full, R)                        # slabs + panel bottom/outer face
    top_z = q["H"] + T
    cam = f.camera(fi.CAM["az"], fi.CAM["el"], fi.CAM["dist"], np.array([0, 0, top_z]))
    proj = lambda P: f.project(np.asarray(P, float), cam, fi.CAM["ox"], fi.CAM["oy"])
    xp = -fi.SLAB_W / 2 - fi.PANEL_T                # outer face, panel touching the slab ends
    v["pan_tl"] = proj([[xp, q["yp_b"], q["PT"]]])[0]
    v["pan_tr"] = proj([[xp, q["yp_f"], q["PT"]]])[0]
    return v


def cost(p):
    q = dict(zip(NAMES, p))
    v = evaluate(p)
    e = 0.0
    for c in fi.C:
        k, ref = c[0], c[1]
        w = c[2] if len(c) > 2 else 1.0
        m = v[k]
        if m is None:
            e += 1e4
        elif isinstance(ref, tuple):
            e += w * ((np.array(m) - np.array(ref)) ** 2).sum()
        else:
            e += w * (m - ref) ** 2
    pen = 1e6 * max(0, q["Z"] + T - q["H"] + 0.02) ** 2 + 1e6 * max(0, -q["Z"]) ** 2
    pen += 1e6 * max(0, q["yp_f"] - q["yp_b"] + 0.05) ** 2
    pen += 1e6 * max(0, q["H"] - q["PT"]) ** 2          # panel reaches at least the upper slab
    pen += 1e6 * max(0, q["PT"] - q["H"] - T) ** 2      # and not above its top surface
    return e + pen


def main():
    best = None
    for s in ([0.26, 0.0, 0.1, -0.15, 0.05, 0.30], [0.25, 0.05, 0.2, -0.05, 0.08, 0.29], [0.27, -0.05, 0.0, -0.25, 0.03, 0.32]):
        x = np.array(s, float)
        for _ in range(4):
            x, val = f.nelder_mead(cost, x, [0.03, 0.05, 0.05, 0.05, 0.03, 0.02])
        if best is None or val < best[1]:
            best = (x, val)
    x, val = best
    q = dict(zip(NAMES, x))
    v = evaluate(x)
    print("[FIT] rms %.1f px" % math.sqrt(val / len(fi.C)))
    for c in fi.C:
        print("[FIT]   %-20s ref %-12s model %s" % (c[0], c[1], np.round(v[c[0]], 1)))
    for k, val in q.items():
        print("[FIT] %-4s = %.4f" % (k, val))
    json.dump(q, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "coffee_table_outboard_fit.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
