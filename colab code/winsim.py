import numpy as np
import pandas as pd
from sklearn.neighbors import KDTree
from tqdm import tqdm
import multiprocessing as mp
import argparse
import os

# ============================================================
# COLOR SPACE UTILITIES
# ============================================================

def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def linear_to_srgb(c):
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * (c ** (1/2.4)) - 0.055)

def rgb_to_xyz(rgb):
    rgb = srgb_to_linear(rgb)
    M = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041]
    ])
    return rgb @ M.T

def xyz_to_lab(xyz):
    ref = np.array([0.95047, 1.00000, 1.08883])
    xyz = xyz / ref

    def f(t):
        return np.where(t > 0.008856, np.cbrt(t), 7.787*t + 16/116)

    fx, fy, fz = f(xyz[:,0]), f(xyz[:,1]), f(xyz[:,2])
    L = 116*fy - 16
    a = 500*(fx - fy)
    b = 200*(fy - fz)
    return np.stack([L,a,b], axis=1)

def rgb_to_lab(rgb):
    return xyz_to_lab(rgb_to_xyz(rgb))

def lab_de(a, b):
    return deltaE2000(rgb_to_lab(a[None,:]), rgb_to_lab(b[None,:]))[0]

# ============================================================
# OKLAB
# ============================================================

def linear_to_oklab(rgb):
    rgb = np.clip(rgb, 0, 1)
    r, g, b = rgb

    l = 0.4122214708*r + 0.5363325363*g + 0.0514459929*b
    m = 0.2119034982*r + 0.6806995451*g + 0.1073969566*b
    s = 0.0883024619*r + 0.2817188376*g + 0.6299787005*b

    l_, m_, s_ = np.cbrt([l, m, s])

    L = 0.2104542553*l_ + 0.7936177850*m_ - 0.0040720468*s_
    a = 1.9779984951*l_ - 2.4285922050*m_ + 0.4505937099*s_
    b = 0.0259040371*l_ + 0.7827717662*m_ - 0.8086757660*s_

    return np.array([L, a, b])

# ============================================================
# DELTA E 2000
# ============================================================

def deltaE2000(Lab1, Lab2):
    L1, a1, b1 = Lab1.T
    L2, a2, b2 = Lab2.T
    avg_L = (L1 + L2) / 2
    C1 = np.sqrt(a1**2 + b1**2)
    C2 = np.sqrt(a2**2 + b2**2)
    avg_C = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt((avg_C**7) / (avg_C**7 + 25**7)))
    a1p = (1 + G) * a1
    a2p = (1 + G) * a2
    C1p = np.sqrt(a1p**2 + b1**2)
    C2p = np.sqrt(a2p**2 + b2**2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp = L2 - L1
    dCp = C2p - C1p
    dhp = h2p - h1p
    dhp = np.where(dhp > 180, dhp - 360, dhp)
    dhp = np.where(dhp < -180, dhp + 360, dhp)
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dhp / 2))
    avg_Lp = (L1 + L2) / 2
    avg_Cp = (C1p + C2p) / 2
    hp_sum = h1p + h2p
    avg_hp = np.where(np.abs(h1p - h2p) > 180, hp_sum + 360, hp_sum) / 2
    avg_hp %= 360
    T = (1
         - 0.17 * np.cos(np.radians(avg_hp - 30))
         + 0.24 * np.cos(np.radians(2 * avg_hp))
         + 0.32 * np.cos(np.radians(3 * avg_hp + 6))
         - 0.20 * np.cos(np.radians(4 * avg_hp - 63)))
    Sl = 1 + ((0.015 * (avg_Lp - 50)**2) / np.sqrt(20 + (avg_Lp - 50)**2))
    Sc = 1 + 0.045 * avg_Cp
    Sh = 1 + 0.015 * avg_Cp * T
    Rt = -2 * np.sqrt((avg_Cp**7) / (avg_Cp**7 + 25**7)) * np.sin(np.radians(60 * np.exp(-((avg_hp - 275)/25)**2)))
    return np.sqrt((dLp/Sl)**2 + (dCp/Sc)**2 + (dHp/Sh)**2 + Rt*(dCp/Sc)*(dHp/Sh))

# ============================================================
# CVD MATRICES
# ============================================================

MATRICES = {
    "Protanopia": np.array([
        [0.152286, 1.052583, -0.204868],
        [0.114503, 0.786281, 0.099216],
        [-0.003882, -0.048116, 1.051998]
    ]),
    "Deuteranopia": np.array([
        [0.367322, 0.860646, -0.227968],
        [0.280085, 0.672501, 0.047413],
        [-0.011820, 0.042940, 0.968881]
    ]),
    "Tritanopia": np.array([
        [1.255528, -0.076749, -0.178779],
        [-0.078411, 0.930809, 0.147602],
        [0.004733, 0.691367, 0.303900]
    ])
}

identity = np.eye(3)

def simulate_cvd(rgb_linear, matrix):
    return np.clip(rgb_linear @ matrix.T, 0, 1)

def simulate_view(srgb, matrix):
    lin = srgb_to_linear(srgb)
    sim = simulate_cvd(lin, matrix)
    return np.clip(linear_to_srgb(sim), 0, 1)

# ============================================================
# RECONSTRUCTION
# ============================================================

def reconstruct_with_analysis(observed_srgb, matrix, iterations=800, top_k=60):
    if np.linalg.norm(observed_srgb) < 0.02:
        return np.array([0,0,0]), np.zeros((1,3)), ["Black detected"], 100

    observed_lin = srgb_to_linear(observed_srgb)
    observed_lab = linear_to_oklab(observed_lin)

    candidates = []

    for _ in range(iterations):
        lin = np.random.rand(3)
        sim = simulate_cvd(lin, matrix)

        sim_lab = linear_to_oklab(sim)
        lab = linear_to_oklab(lin)

        if abs(lab[0] - observed_lab[0]) > 0.05:
            continue

        error = np.linalg.norm(sim_lab - observed_lab)
        candidates.append((error, lin, lab))

    if len(candidates) < 10:
        for _ in range(iterations):
            lin = np.random.rand(3)
            sim = simulate_cvd(lin, matrix)
            sim_lab = linear_to_oklab(sim)
            lab = linear_to_oklab(lin)
            error = np.linalg.norm(sim_lab - observed_lab)
            candidates.append((error, lin, lab))

    candidates.sort(key=lambda x: x[0])
    best_set = candidates[:top_k]

    best_lin = best_set[0][1]
    best_error = best_set[0][0]
    labs = np.array([c[2] for c in best_set])

    spread = np.mean(np.linalg.norm(labs - labs.mean(axis=0), axis=1))
    confidence = int(np.clip(1 / (1 + 15 * (best_error + spread)), 0, 1) * 100)

    return linear_to_srgb(best_lin), labs, [], confidence

# ============================================================
# PARALLEL TEST (WINDOWS SAFE)
# ============================================================

def process_chunk(chunk):
    np.random.seed()  # ensure different per process
    rows = []

    for rgb in chunk:
        for name, M in MATRICES.items():
            sim = simulate_view(rgb, M)
            rec, labs, warnings, conf = reconstruct_with_analysis(sim, M)

            de_orig_rec = lab_de(rgb, rec)
            spread = np.mean(np.linalg.norm(labs - labs.mean(axis=0), axis=1))

            if de_orig_rec > 3.0 or spread > 0.07:
                rows.append([*rgb, name, *rec, conf, de_orig_rec, spread])

    return rows

def run_parallel_test(reps, chunk_size=256):
    cpu = mp.cpu_count()
    chunks = [reps[i:i+chunk_size] for i in range(0, len(reps), chunk_size)]

    columns = ["r","g","b","cvd","rec_r","rec_g","rec_b","conf","de","spread"]

    with mp.Pool(cpu) as pool, open("anomalies.csv", "w") as f:
        f.write(",".join(columns) + "\n")
        for result in tqdm(pool.imap_unordered(process_chunk, chunks), total=len(chunks)):
            if result:
                pd.DataFrame(result, columns=columns).to_csv(f, header=False, index=False)

# ============================================================
# MAIN
# ============================================================

def load_reps():
    if not os.path.exists("perceptual_reps.npy"):
        raise RuntimeError("Run with --build-reps first")
    return np.load("perceptual_reps.npy")

if __name__ == "__main__":
    mp.freeze_support()

    parser = argparse.ArgumentParser()
    parser.add_argument("--run-test", action="store_true")
    args = parser.parse_args()

    if args.run_test:
        reps = load_reps()
        run_parallel_test(reps)