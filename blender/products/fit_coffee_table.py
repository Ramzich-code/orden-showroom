"""
Least-squares fit of the coffee-table proportions and the camera to points
measured on the reference photograph (854 x 1280 px).

Pure numpy; run with Blender's Python or any Python with numpy:
    blender -b --factory-startup --python blender/products/fit_coffee_table.py

Scale is fixed by assuming the stone top is 1.10 m wide (the photo contains
no absolute dimension). Everything else is solved.
"""
import json
import math
import os

import numpy as np

W_IMG, H_IMG = 854, 1280
LENS, SENSOR = 50.0, 36.0
F_PX = LENS / SENSOR * W_IMG

# --- Points measured on the photograph (pixels). See docs/coffee-table-fit.md
REF = {
    "stone_left": (27, 652),        # leftmost point of the stone slab
    "stone_right": (828, 663),      # rightmost point of the stone slab
    "stone_low": (380, 850),        # lowest point of the slab's lower edge
    "stone_top": (720, 517),        # highest point of the top surface
    "stone_near_top": (365, 811),   # lowest point of the top surface outline
    "wal_low": (395, 983),          # lowest point of the walnut platform
    "wal_right": (823, 800),        # rightmost point of the walnut
    "wal_left": (27, 745),          # leftmost point (rounded back-left end)
    "pan_tl": (100, 711),           # vertical panel, outer face corners
    "pan_tr": (186, 764),
    "pan_br": (182, 938),
    "pan_bl": (100, 877),
}

STONE_W = 1.10
R_CORNER = 0.18


def rounded_rect(w, d, r, n=24):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return np.array(pts)


def camera(az, el, dist, target):
    a, e = math.radians(az), math.radians(el)
    d = np.array([-math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)])
    pos = target + d * dist
    fwd = -d
    right = np.cross(fwd, [0, 0, 1.0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return pos, right, up, fwd


def project(P, cam, ox, oy):
    pos, right, up, fwd = cam
    v = P - pos
    z = v @ fwd
    x = (v @ right) / z * F_PX + W_IMG / 2 + ox
    y = -(v @ up) / z * F_PX + H_IMG / 2 + oy
    return np.stack([x, y], -1)


NAMES = ["az", "el", "dist", "ox", "oy", "Ds", "Ts", "H", "Ww", "Dw", "cxw", "cyw", "zwb", "Tw", "xp", "yp_b", "yp_f"]


def model_points(p):
    q = dict(zip(NAMES, p))
    top_z = q["H"] + q["Ts"]
    cam = camera(q["az"], q["el"], q["dist"], np.array([0, 0, top_z]))
    proj = lambda P: project(np.asarray(P, float), cam, q["ox"], q["oy"])
    out = {}
    s_rr = rounded_rect(STONE_W, q["Ds"], R_CORNER)
    s_top = proj(np.c_[s_rr, np.full(len(s_rr), top_z)])
    s_bot = proj(np.c_[s_rr, np.full(len(s_rr), q["H"])])
    s_all = np.vstack([s_top, s_bot])
    out["stone_left"] = s_all[s_all[:, 0].argmin()]
    out["stone_right"] = s_all[s_all[:, 0].argmax()]
    out["stone_low"] = s_bot[s_bot[:, 1].argmax()]
    out["stone_top"] = s_top[s_top[:, 1].argmin()]
    out["stone_near_top"] = s_top[s_top[:, 1].argmax()]
    w_rr = rounded_rect(q["Ww"], q["Dw"], R_CORNER) + [q["cxw"], q["cyw"]]
    w_top = proj(np.c_[w_rr, np.full(len(w_rr), q["zwb"] + q["Tw"])])
    w_bot = proj(np.c_[w_rr, np.full(len(w_rr), q["zwb"])])
    w_all = np.vstack([w_top, w_bot])
    out["wal_low"] = w_bot[w_bot[:, 1].argmax()]
    out["wal_right"] = w_all[w_all[:, 0].argmax()]
    out["wal_left"] = w_all[w_all[:, 0].argmin()]
    for name, (y, z) in {"pan_tl": (q["yp_b"], q["H"]), "pan_tr": (q["yp_f"], q["H"]),
                         "pan_br": (q["yp_f"], 0.0), "pan_bl": (q["yp_b"], 0.0)}.items():
        out[name] = proj([[q["xp"], y, z]])[0]
    return out


def cost(p):
    q = dict(zip(NAMES, p))
    pen = 0.0
    # physical sanity: positive sizes, walnut above floor, panel thin & behind stone edge
    for k in ("Ds", "Ts", "H", "Ww", "Dw", "Tw"):
        pen += 1e4 * max(0, 0.02 - q[k]) ** 2
    pen += 1e5 * max(0, -q["zwb"]) ** 2
    pen += 1e5 * max(0, q["zwb"] + q["Tw"] - q["H"] + 0.02) ** 2      # an open gap must exist
    pen += 1e5 * max(0, q["yp_f"] - q["yp_b"] + 0.05) ** 2           # panel width > 5 cm
    m = model_points(p)
    err = sum(((m[k] - np.array(v)) ** 2).sum() for k, v in REF.items())
    return err + pen


def nelder_mead(f, x0, step, iters=4000, tol=1e-10):
    n = len(x0)
    pts = [np.array(x0, float)]
    for i in range(n):
        x = np.array(x0, float); x[i] += step[i]; pts.append(x)
    vals = [f(x) for x in pts]
    for it in range(iters):
        order = np.argsort(vals); pts = [pts[i] for i in order]; vals = [vals[i] for i in order]
        if abs(vals[-1] - vals[0]) < tol * (abs(vals[0]) + 1e-12) + 1e-6 and it > 300:
            break
        c = np.mean(pts[:-1], 0)
        xr = c + (c - pts[-1]); fr = f(xr)
        if fr < vals[0]:
            xe = c + 2 * (c - pts[-1]); fe = f(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = c + 0.5 * (pts[-1] - c); fc = f(xc)
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
            else:
                pts = [pts[0] + 0.5 * (x - pts[0]) for x in pts]; vals = [f(x) for x in pts]
    i = int(np.argmin(vals))
    return pts[i], vals[i]


STONE_KEYS = ["stone_left", "stone_right", "stone_low", "stone_top", "stone_near_top"]
REST_KEYS = [k for k in REF if k not in STONE_KEYS]


def err_for(p, keys):
    m = model_points(p)
    return sum(((m[k] - np.array(REF[k])) ** 2).sum() for k in keys)


def penalties(q):
    pen = 0.0
    for k in ("Ds", "Ts", "H", "Ww", "Dw", "Tw"):
        pen += 1e5 * max(0, 0.02 - q[k]) ** 2
    pen += 1e6 * max(0, -q["zwb"]) ** 2
    pen += 1e6 * max(0, q["zwb"] + q["Tw"] - q["H"] + 0.02) ** 2
    pen += 1e6 * max(0, q["yp_f"] - q["yp_b"] + 0.05) ** 2
    return pen


def report(best, label):
    m = model_points(best)
    rms = math.sqrt(sum(((m[k] - np.array(v)) ** 2).sum() for k, v in REF.items()) / len(REF))
    print("[FIT] ---- %s   rms over all points: %.1f px" % (label, rms))
    for k in REF:
        d = np.linalg.norm(m[k] - np.array(REF[k]))
        print("[FIT]  %-15s ref %-12s model (%4.0f, %4.0f)  err %4.1f px" % (k, REF[k], m[k][0], m[k][1], d))
    for k, v in zip(NAMES, best):
        print("[FIT] %-5s = %.4f" % (k, v))
    return rms


def main():
    x = np.array([39, 19, 2.0, 0, -24, 1.02, 0.07, 0.25, 1.10, 1.02, 0.0, 0.0, 0.0, 0.09, -0.56, 0.2, -0.05], float)
    # stage 1: camera + stone only
    cam_idx = [0, 1, 2, 3, 4, 5, 6]
    def f1(sub):
        y = x.copy(); y[cam_idx] = sub
        return err_for(y, STONE_KEYS)
    sub = x[cam_idx]
    for _ in range(3):
        sub, v1 = nelder_mead(f1, sub, [3, 3, 0.3, 20, 20, 0.08, 0.02])
    x[cam_idx] = sub
    print("[FIT] stage 1 stone rms: %.1f px" % math.sqrt(v1 / len(STONE_KEYS)))
    # stage 2: walnut, panel, height of the stone above the floor (camera fixed)
    rest_idx = list(range(7, len(NAMES)))
    def f2(sub):
        y = x.copy(); y[rest_idx] = sub
        return err_for(y, REST_KEYS) + penalties(dict(zip(NAMES, y)))
    sub = x[rest_idx]
    best_v = 1e18
    for start in ([0.25, 1.1, 1.02, 0, 0, 0.0, 0.09, -0.56, 0.2, -0.05],
                  [0.30, 1.0, 1.1, 0.05, 0.1, 0.02, 0.09, -0.53, 0.25, 0.0],
                  [0.28, 1.1, 1.0, 0.0, -0.05, 0.05, 0.1, -0.56, 0.1, -0.15]):
        s2 = np.array(start, float)
        for _ in range(3):
            s2, v2 = nelder_mead(f2, s2, [0.05, 0.08, 0.08, 0.05, 0.05, 0.03, 0.02, 0.05, 0.08, 0.08])
        if v2 < best_v:
            best_v, sub = v2, s2
    x[rest_idx] = sub
    rms = report(x, "final")
    q = dict(zip(NAMES, x))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coffee_table_fit.json")
    with open(out, "w") as fh:
        json.dump({"params": q, "rms_px": rms, "stone_w": STONE_W, "corner_r": R_CORNER, "lens": LENS}, fh, indent=1)
    print("[FIT] saved", out)


if __name__ == "__main__":
    main()
