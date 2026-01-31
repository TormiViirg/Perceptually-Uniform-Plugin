from google.colab import output 
output.enable_custom_widget_manager()

from PIL import Image
from google.colab import files

import numpy as np
import matplotlib.pyplot as plt
import time
import ipywidgets as widgets
from IPython.display import display, clear_output

last_swatch_img = None

def hsl_to_rgb_vec(h, s, l):
    h = np.asarray(h, dtype = np.float32)
    s = np.asarray(s, dtype = np.float32)
    l = np.asarray(l, dtype = np.float32)

    r = np.empty_like(h, dtype = np.float32)
    g = np.empty_like(h, dtype = np.float32)
    b = np.empty_like(h, dtype = np.float32)

    ach = (s == 0)
    r[ach] = l[ach]
    g[ach] = l[ach]
    b[ach] = l[ach]

    chr_ = ~ach
    if np.any(chr_):
        hh = h[chr_]
        ss = s[chr_]
        ll = l[chr_]

        q = np.where(ll < 0.5, ll * (1.0 + ss), ll + ss - ll * ss)
        p = 2.0 * ll - q

        def hue2rgb(p, q, t):
            t = t % 1.0
            out = np.empty_like(t, dtype=np.float32)
            c1 = t < (1/6)
            c2 = (t >= (1/6)) & (t < 0.5)
            c3 = (t >= 0.5) & (t < (2/3))
            out[c1] = p[c1] + (q[c1] - p[c1]) * 6.0 * t[c1]
            out[c2] = q[c2]
            out[c3] = p[c3] + (q[c3] - p[c3]) * (2/3 - t[c3]) * 6.0
            out[~(c1 | c2 | c3)] = p[~(c1 | c2 | c3)]
            return out

        rt = hh + 1/3
        gt = hh
        bt = hh - 1/3

        r[chr_] = hue2rgb(p, q, rt)
        g[chr_] = hue2rgb(p, q, gt)
        b[chr_] = hue2rgb(p, q, bt)

    return r, g, b

def srgb_to_linear(c):
    c = np.asarray(c, dtype=np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

M_RGB_TO_XYZ = np.array([
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041],
], dtype=np.float32)

WHITE_D65 = np.array([0.95047, 1.0, 1.08883], dtype=np.float32)

def rgb_linear_to_xyz(r, g, b):
    rgb = np.stack([r, g, b], axis=-1)
    xyz = rgb @ M_RGB_TO_XYZ.T
    return xyz[..., 0], xyz[..., 1], xyz[..., 2]

def f_lab(t):
    delta = 6 / 29
    delta3 = delta ** 3
    return np.where(
        t > delta3, 
        np.cbrt(t),
        t / (3 * delta * delta) + 4/29
    )

def xyz_to_lab(x, y, z):
    x = x / WHITE_D65[0]
    y = y / WHITE_D65[1]
    z = z / WHITE_D65[2]

    fx = f_lab(x)
    fy = f_lab(y)
    fz = f_lab(z)

    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    return L.astype(np.float32), a.astype(np.float32), b.astype(np.float32)

def delta_e94(
    lab1, lab2,
    kL = 1.0, 
    kC = 1.0, 
    kH = 1.0, 
    K1 = 0.045, 
    K2 = 0.015
    ):
  
    L1, a1, b1 = lab1[..., 0], lab1[..., 1], lab1[..., 2]
    L2, a2, b2 = lab2[..., 0], lab2[..., 1], lab2[..., 2]

    dL = L1 - L2
    C1 = np.sqrt(a1*a1 + b1*b1)
    C2 = np.sqrt(a2*a2 + b2*b2)
    dC = C1 - C2

    da = a1 - a2
    db = b1 - b2
    dH2 = da*da + db*db - dC*dC
    dH2 = np.maximum(dH2, 0.0)
    dH = np.sqrt(dH2)

    SL = 1.0
    SC = 1.0 + K1 * C1
    SH = 1.0 + K2 * C1

    termL = (dL / (kL * SL)) ** 2
    termC = (dC / (kC * SC)) ** 2
    termH = (dH / (kH * SH)) ** 2
    return np.sqrt(termL + termC + termH).astype(np.float32)

def greedy_palette_deltae94(
    threshold = 2.0,
    L_fixed = 0.5,
    order = "sat_desc",
    shuffle_seed = None,
    h_steps = 256,
    s_steps = 256,
    sat_min = 0.0
):
    H = np.arange(h_steps, dtype=np.float32) / float(h_steps)
    S = np.linspace(sat_min, 1.0, s_steps, dtype=np.float32)
    HH, SS = np.meshgrid(H, S, indexing="xy")
    LL = np.full_like(HH, L_fixed, dtype=np.float32)

    r, g, b = hsl_to_rgb_vec(HH.ravel(), SS.ravel(), LL.ravel())
    rgb_srgb = np.stack([r, g, b], axis=1).astype(np.float32)

    rl, gl, bl = srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b)
    x, y, z = rgb_linear_to_xyz(rl, gl, bl)
    L_val, a_val, b_val = xyz_to_lab(x, y, z)
    labs = np.stack([L_val, a_val, b_val], axis=1).astype(np.float32)

    n = labs.shape[0]
    idx = np.arange(n, dtype=np.int32)

    if order == "random":
        rng = np.random.default_rng(0 if shuffle_seed is None else int(shuffle_seed))
        rng.shuffle(idx)
    elif order == "sat_desc":
        sat = SS.ravel()
        idx = np.argsort(-sat, kind="stable").astype(np.int32)
    elif order == "hue_then_sat":
        hue = HH.ravel()
        sat = SS.ravel()
        idx = np.lexsort((sat, hue)).astype(np.int32)

    bin_size = float(threshold)
    kept_labs = []
    kept_rgb = []
    bins = {}

    neighbor_offsets = [(dx, dy, dz)
                        for dx in (-1, 0, 1)
                        for dy in (-1, 0, 1)
                        for dz in (-1, 0, 1)]

    def bin_key(lab):
        return (int(np.floor(lab[0] / bin_size)),
                int(np.floor(lab[1] / bin_size)),
                int(np.floor(lab[2] / bin_size)))

    for i in idx:
        lab = labs[i]
        bk = bin_key(lab)

        cand_ids = []
        for dx, dy, dz in neighbor_offsets:
            key = (bk[0] + dx, bk[1] + dy, bk[2] + dz)
            if key in bins:
                cand_ids.extend(bins[key])

        if cand_ids:
            cand = np.array([kept_labs[j] for j in cand_ids], dtype=np.float32)
            d = delta_e94(cand, lab[None, :])
            if np.any(d < threshold):
                continue

        new_id = len(kept_labs)
        kept_labs.append(lab)
        kept_rgb.append(rgb_srgb[i])
        bins.setdefault(bk, []).append(new_id)

    return np.array(kept_rgb, dtype = np.float32), np.array(kept_labs, dtype = np.float32)

def palette_to_swatch_image(
    rgb, 
    labs = None, 
    cols = 64, 
    cell = 8, 
    sort_for_display = True
    ):
  
    rgb = np.clip(rgb, 0, 1)

    if sort_for_display and labs is not None and len(labs) > 0:
        a = labs[:, 1]; b = labs[:, 2]
        hue_angle = np.arctan2(b, a)  
        chroma = np.sqrt(a*a + b*b)
        order = np.lexsort((chroma, hue_angle))
        rgb = rgb[order]

    n = rgb.shape[0]
    rows = int(np.ceil(n / cols))
    img = np.ones((rows * cols, 3), dtype = np.float32)
    img[:n] = rgb
    img = img.reshape(rows, cols, 3)

    if cell > 1:
        img = np.kron(img, np.ones((cell, cell, 1), dtype = np.float32))
    return img

threshold_slider = widgets.FloatSlider(
    value = 2.0, 
    min = 0.5, 
    max = 10.0, 
    step = 0.1, 
    description = 'threshold ΔE94', 
    continuous_update = False
)

L_slider         = widgets.FloatSlider(
    value = 0.5, 
    min = 0.0, 
    max = 1.0, 
    step = 0.01, 
    description = 'L_fixed (HSL)', 
    continuous_update = False
)

sat_min_slider   = widgets.FloatSlider(
    value = 0.0, 
    min = 0.0, 
    max = 1.0, 
    step = 0.01, 
    description = 'min saturation', 
    continuous_update = False
)

h_steps_slider   = widgets.IntSlider(
    value = 256, 
    min = 32, 
    max = 256, 
    step = 16, 
    description = 'H steps', 
    continuous_update = False
)

s_steps_slider   = widgets.IntSlider(
    value = 256, 
    min = 32,
    max = 256,
    step = 16,
    description = 'S steps',
    continuous_update = False
)

order_dropdown   = widgets.Dropdown( options = [
    ('sat_desc', 'sat_desc'), 
    ('hue_then_sat', 'hue_then_sat'), 
    ('random', 'random')
], value='sat_desc', description='order')

seed_toggle = widgets.Checkbox( 
    value = False, 
    description = 'use seed (random order)'
)

seed_input = widgets.IntText(
    value = 0, 
    description = 'seed', 
    disabled = True
)

def _toggle_seed(change):
    seed_input.disabled = not change['new']
seed_toggle.observe(_toggle_seed, names='value')

cols_slider = widgets.IntSlider(
    value = 64, 
    min = 16, 
    max = 128, 
    step = 8, 
    description = 'swatch cols', 
    continuous_update = False
)

cell_slider = widgets.IntSlider(
    value = 8,
    min = 2, 
    max = 16, 
    step = 1, 
    description = 'cell size', 
    continuous_update = False
)

sort_checkbox = widgets.Checkbox(
    value = True, 
    description = 'sort palette for display'
)

show_checkbox = widgets.Checkbox(
    value = True, 
    description = 'show swatch image'
)

run_button = widgets.Button(
    description = 'Recalculate', 
    button_style = 'primary', 
    icon = 'refresh'
)

out = widgets.Output()

def recompute( _ = None ):
  
    with out:
        clear_output(wait=True)
        t0 = time.time()

        threshold = float(threshold_slider.value)
        L_fixed   = float(L_slider.value)
        sat_min   = float(sat_min_slider.value)
        h_steps   = int(h_steps_slider.value)
        allowing_s0 = (sat_min <= 0.0)

        order     = order_dropdown.value
        seed      = int(seed_input.value) if (seed_toggle.value and order == "random") else None
        s_steps   = int(s_steps_slider.value)

        rgb, labs = greedy_palette_deltae94(
            threshold=threshold,
            L_fixed=L_fixed,
            order=order,
            shuffle_seed=seed,
            h_steps=h_steps,
            s_steps=s_steps,
            sat_min=sat_min
        )

        dt = time.time() - t0

        print(f"Kept colors: {rgb.shape[0]}")
        print(f"Params: threshold={threshold}, L_fixed={L_fixed}, order={order}, seed={seed}, H={h_steps}, S={s_steps}, sat_min={sat_min}")

        if allowing_s0:
            print("Note: sat_min=0 allows true grays (S=0) at L_fixed (e.g., ~#808080 when L_fixed=0.5).")

        print(f"Compute time: {dt:.2f}s")

        if show_checkbox.value:
            img = palette_to_swatch_image(
                rgb, labs = labs,
                cols = int(cols_slider.value),
                cell = int(cell_slider.value),
                sort_for_display = bool(sort_checkbox.value)
            )

            global last_swatch_img
            last_swatch_img = img

            plt.figure(
                figsize = (12, 6)
            )

            plt.imshow(
                img, 
                interpolation = "nearest"
            )

            plt.axis("off")
            plt.title("Kept colors (sRGB swatches)")
            plt.show()

run_button.on_click(recompute)

save_button = widgets.Button(
    description='Save BMP', 
    button_style='success', 
    icon='save'
)

def save_bmp( _ = None, filename = "palette.bmp"):
    with out:
        if last_swatch_img is None:
            print("Nothing to save yet — click Recalculate first.")
            return

        img8 = (np.clip(last_swatch_img, 0, 1) * 255).astype(np.uint8)
        Image.fromarray(img8, mode="RGB").save(filename)  
        print(f"Saved: {filename}")
        files.download(filename)

save_button.on_click(save_bmp)


ui_left = widgets.VBox([
    threshold_slider,
    L_slider,
    sat_min_slider,
    order_dropdown,
    widgets.HBox([seed_toggle, seed_input]),
])

ui_right = widgets.VBox([
    h_steps_slider,
    s_steps_slider,
    cols_slider,
    cell_slider,
    sort_checkbox,
    show_checkbox,
    widgets.HBox([run_button, save_button])
])


ui = widgets.HBox([ui_left, ui_right])
display(ui, out)

recompute()