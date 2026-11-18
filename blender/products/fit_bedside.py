"""
Bedside table: solve the reference camera and the cabinet's width/depth.

The reference (1018 x 835 px) is a two-point perspective: all vertical edges
are vertical, so the camera is level (no pitch/roll) with a vertical lens
shift. Unknowns: camera position, yaw, focal length, principal point, and the
cabinet width and depth. Scale: side panel height fixed to the current model.

    blender -b --factory-startup --python blender/products/fit_bedside.py
"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fit_coffee_table as f

W_IMG, H_IMG = 1018, 835
SIDE_Z0, SIDE_Z1 = 0.04, 0.50       # side panels: plinth top to top of the frame (scale)

# carcass corners measured on the photograph (px)
REF = {
    "L_back_top": (178, 278), "L_back_bot": (178, 662),
    "L_front_top": (500, 330), "L_front_bot": (500, 734),
    "R_front_top": (905, 215), "R_front_bot": (905, 555),
}
NAMES = ["cx", "cy", "cz", "yaw", "fpx", "ppx", "ppy", "W", "D"]


def project(p, P):
    q = dict(zip(NAMES, p))
    cam = np.array([q["cx"], q["cy"], q["cz"]])
    a = math.radians(q["yaw"])
    fwd = np.array([math.sin(a), math.cos(a), 0.0])        # level camera
    right = np.array([math.cos(a), -math.sin(a), 0.0])
    up = np.array([0, 0, 1.0])
    v = np.asarray(P, float) - cam
    z = v @ fwd
    return np.stack([q["ppx"] + q["fpx"] * (v @ right) / z, q["ppy"] - q["fpx"] * (v @ up) / z], -1)


def corners(p):
    q = dict(zip(NAMES, p))
    W, D = q["W"], q["D"]
    pts = {
        "L_back_top": (-W / 2, D / 2, SIDE_Z1), "L_back_bot": (-W / 2, D / 2, SIDE_Z0),
        "L_front_top": (-W / 2, -D / 2, SIDE_Z1), "L_front_bot": (-W / 2, -D / 2, SIDE_Z0),
        "R_front_top": (W / 2, -D / 2, SIDE_Z1), "R_front_bot": (W / 2, -D / 2, SIDE_Z0),
    }
    return {k: project(p, [v])[0] for k, v in pts.items()}


def cost(p):
    q = dict(zip(NAMES, p))
    if q["fpx"] < 100 or q["W"] < 0.1 or q["D"] < 0.1:
        return 1e12
    m = corners(p)
    return sum(((m[k] - np.array(v)) ** 2).sum() for k, v in REF.items())


def main():
    best = None
    for yaw in (20, 30, 40, 50):
        for dist in (1.0, 1.6, 2.4):
            a = math.radians(yaw)
            x0 = [-math.sin(a) * dist, -math.cos(a) * dist, 1.1, yaw, 1100, 509, 100, 0.6, 0.42]
            x = np.array(x0, float)
            for _ in range(3):
                x, v = f.nelder_mead(cost, x, [0.2, 0.2, 0.2, 5, 150, 40, 60, 0.08, 0.08])
            if best is None or v < best[1]:
                best = (x, v)
    x, v = best
    q = dict(zip(NAMES, x))
    m = corners(x)
    print("[FIT] rms %.2f px" % math.sqrt(v / len(REF)))
    for k in REF:
        print("[FIT]  %-12s ref %-11s model (%.0f, %.0f)" % (k, REF[k], *m[k]))
    for k, val in q.items():
        print("[FIT] %-4s = %.4f" % (k, val))
    json.dump(q, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bedside_camera_fit.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
