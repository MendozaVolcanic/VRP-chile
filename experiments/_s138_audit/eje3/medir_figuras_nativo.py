"""S138 eje 3 - verificacion del instrumento 4 (medir_figuras_apendice.py) sobre la imagen NATIVA.

POR QUE. El instrumento de S137 renderiza la pagina a 400 dpi y lee marcas de graduacion medidas a
mano. Las figuras del Apendice A son PNG embebidos de 1065 x 607 px (fitz extract_image), asi que el
render a 400 dpi INTERPOLA (2x) un raster que ya existe. Aqui se mide sobre el raster nativo, con las
marcas detectadas automaticamente por los rotulos de la barra, y se corren los controles:
  C1 sintetico: campo gaussiano de sigma conocido pintado con la tabla de la barra -> sigma recuperado.
  C2 instrumento muerto: panel uniforme (sigma 0) y ruido RGB (sigma enorme).
  C3 escala invertida: signo cambiado (la mediana no lo delata) y espejada (si lo delata).
  C4 paneles negativos A7 / A9 / A4 (el autor no detecta): sigma de un fondo sin anomalia.
  C5 posicion de la mascara de alerta en A2 y A6 respecto del centro de la grilla (51 celdas).
Escribe solo en experiments/_s138_audit/eje3/out_nativo/.
"""
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
import fitz

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[2]
OUT = HERE / "out_nativo"
OUT.mkdir(exist_ok=True)
PDF = RAIZ / "documentacion" / "sp426.5.pdf"
sys.path.insert(0, str(RAIZ / "experiments" / "_s137"))
import medir_figuras_apendice as M  # noqa: E402  (solo funciones puras)

FIG = {"A2": 140, "A6": 166, "A7": 171, "A9": 184, "A4": 153, "A3": 145}
CAJA_DNTI = (12, 330, 240, 575)
CAJA_DETI = (752, 330, 985, 575)
CAJA_BARRA_DNTI = (240, 330, 340, 575)
LABELS_DNTI = [0.01, 0.005, 0.0, -0.005, -0.01]


def imagen(xref):
    doc = fitz.open(str(PDF))
    info = doc.extract_image(xref)
    return np.array(Image.open(io.BytesIO(info["image"])).convert("RGB"))


def barra_y_marcas(img, caja, labels):
    x0, y0, x1, y1 = caja
    sub = img[y0:y1, x0:x1]
    g = sub.mean(axis=2)
    cols = np.where((g < 245).mean(axis=0) > 0.6)[0]
    grupos = np.split(cols, np.where(np.diff(cols) > 1)[0] + 1)
    barra = max(grupos, key=len)
    bx0, bx1 = int(barra.min()), int(barra.max())
    c = (bx0 + bx1) // 2
    filas = np.where(g[:, c] < 250)[0]
    r_top, r_bot = int(filas.min()) + 3, int(filas.max()) - 3
    lab = g[:, bx1 + 4: bx1 + 60]
    tinta = (lab < 140).any(axis=1)
    filas_t = np.where(tinta)[0]
    grupos_t = np.split(filas_t, np.where(np.diff(filas_t) > 2)[0] + 1)
    centros = [float((gr.min() + gr.max()) / 2) for gr in grupos_t if len(gr) >= 4]
    if len(centros) != len(labels):
        raise RuntimeError(f"rotulos detectados {len(centros)} != {len(labels)}: {centros}")
    a, b = np.polyfit(centros, labels, 1)
    resid = float(np.max(np.abs(a * np.array(centros) + b - labels)))
    rows = np.arange(r_top, r_bot + 1)
    colores = sub[rows, c, :].astype(float)
    vals = a * rows + b
    meta = {"bar_x": (x0 + bx0, x0 + bx1), "bar_rows": (y0 + r_top, y0 + r_bot),
            "centros_rotulos_nativo": [round(y0 + v, 1) for v in centros],
            "pendiente": a, "ordenada": b, "residuo": resid,
            "escala": [round(float(vals.min()), 5), round(float(vals.max()), 5)],
            "n_colores": int(len(rows))}
    return colores, vals, meta


def interior(img, caja):
    x0, y0, x1, y1 = caja
    return M.interior_panel(img[y0:y1, x0:x1])


def medir(nombre, img):
    dentro = interior(img, CAJA_DNTI)
    colores, vals, meta = barra_y_marcas(img, CAJA_BARRA_DNTI, LABELS_DNTI)
    v = M.a_valores(dentro, colores, vals)
    celdas = M.por_celda(v, 51)
    h, w = celdas.shape
    region = celdas[int(h * 0.15):int(h * 0.75), int(w * 0.45):]
    fila = {"panel": nombre, "interior_px": list(dentro.shape[:2]), "barra": meta,
            "pixel": M.estadisticos(v), "celda51": M.estadisticos(celdas),
            "celda50": M.estadisticos(M.por_celda(v, 50)),
            "celda_sin_lago_ni_costa": M.estadisticos(region),
            "max_celda": round(float(celdas.max()), 5)}
    fila["control_mediana_ok"] = abs(fila["celda51"]["mediana"]) <= M.TOL_MEDIANA
    Image.fromarray(dentro).save(OUT / f"{nombre}_interior.png")
    return fila, (dentro, colores, vals)


def pintar(campo, colores, vals):
    idx = np.abs(campo.reshape(-1, 1) - vals.reshape(1, -1)).argmin(axis=1)
    return colores[idx].reshape(campo.shape + (3,)).astype(np.uint8)


def extraer(rgb, colores, vals):
    v = M.a_valores(rgb, colores, vals)
    return M.estadisticos(M.por_celda(v, 51))


def rumbo(dx_e, dy_n):
    return (np.degrees(np.arctan2(dx_e, dy_n)) + 360) % 360


def alerta(img):
    """Mascara de alerta: panel del medio, mismo marco que el dNTI desplazado media distancia al dETI."""
    def abs_box(caja):
        x0, y0, x1, y1 = caja
        g = img[y0:y1, x0:x1].mean(axis=2)
        m = M.recuadro_oscuro(g)
        return (x0 + m[2], y0 + m[0], x0 + m[3], y0 + m[1])
    bd, be = abs_box(CAJA_DNTI), abs_box(CAJA_DETI)
    dx = (be[0] - bd[0]) / 2.0
    gd = img[bd[1]:bd[3] + 1, bd[0]:bd[2] + 1].mean(axis=2)

    def grosor(perfil):
        i = 0
        while i < len(perfil) // 4 and perfil[i] < 60:
            i += 1
        return i + 2
    top, bot = grosor(gd.mean(axis=1)), grosor(gd.mean(axis=1)[::-1])
    izq, der = grosor(gd.mean(axis=0)), grosor(gd.mean(axis=0)[::-1])
    ax0, ay0 = int(round(bd[0] + dx)) + izq, bd[1] + top
    ax1, ay1 = int(round(bd[2] + dx)) + 1 - der, bd[3] + 1 - bot
    panel = img[ay0:ay1, ax0:ax1]
    g = panel.mean(axis=2)
    H, W = g.shape
    ys, xs = np.where(g > 128)
    if len(xs) == 0:
        return {"n_px_blancos": 0, "nota": "sin pixeles blancos en la mascara", "panel_px": [H, W]}
    cx, cy = xs.mean() + 0.5, ys.mean() + 0.5
    ccx, ccy = cx / W * 51, cy / H * 51
    dxe, dyn = ccx - 25.5, 25.5 - ccy
    xr = (xs.min() / W * 51, (xs.max() + 1) / W * 51)
    yr = (ys.min() / H * 51, (ys.max() + 1) / H * 51)
    return {"n_px_blancos": int(len(xs)), "panel_px": [H, W],
            "centroide_celda": [round(ccx, 2), round(ccy, 2)],
            "extension_celdas_x": [round(xr[0], 2), round(xr[1], 2)],
            "extension_celdas_y": [round(yr[0], 2), round(yr[1], 2)],
            "n_celdas_aprox": round(len(xs) / (H * W / 51 / 51), 1),
            "dist_km_desde_centro_25.5": round(float(np.hypot(dxe, dyn)), 2),
            "rumbo_deg": round(float(rumbo(dxe, dyn)), 1),
            "dist_km_si_grilla_50": round(float(np.hypot(dxe, dyn)) * 50 / 51, 2)}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    res = {}
    imgs = {k: imagen(x) for k, x in FIG.items()}
    for nombre in ["A2", "A6", "A7", "A9", "A4", "A3"]:
        try:
            fila, _ = medir(nombre, imgs[nombre])
            res[nombre] = fila
            print(f"{nombre}: interior {fila['interior_px']}  barra escala {fila['barra']['escala']} "
                  f"residuo {fila['barra']['residuo']:.2e} rotulos {fila['barra']['centros_rotulos_nativo']} "
                  f"n_colores {fila['barra']['n_colores']}")
            print(f"     celda51 {fila['celda51']}")
            print(f"     celda50 r3 {fila['celda50']['sigma_recorte3']} | sin lago r3 "
                  f"{fila['celda_sin_lago_ni_costa']['sigma_recorte3']} | max {fila['max_celda']} "
                  f"| mediana ok {fila['control_mediana_ok']}")
        except Exception as e:
            res[nombre] = {"error": repr(e)}
            print(nombre, "ERROR", repr(e))
    fila6, (dentro6, col6, val6) = medir("A6", imgs["A6"])
    H, W = dentro6.shape[:2]
    rng = np.random.default_rng(137)
    print("\nC1 sintetico (51x51 gaussiano pintado con la barra de A6, bilineal al tamano del interior, 1 px saturado al centro):")
    c1 = []
    for st in [0.0004, 0.0008, 0.0016, 0.0030, 0.0076]:
        campo = rng.normal(0, st, (51, 51))
        campo[25, 25] = 0.05
        rgb = pintar(campo, col6, val6)
        grande = np.array(Image.fromarray(rgb).resize((W, H), Image.BILINEAR))
        e = extraer(grande, col6, val6)
        e_nn = extraer(np.array(Image.fromarray(rgb).resize((W, H), Image.NEAREST)), col6, val6)
        verdad = M.estadisticos(np.clip(campo, val6.min(), val6.max()))
        c1.append({"sigma_true": st, "verdad_clipped": verdad, "recuperado_bilineal": e, "recuperado_nearest": e_nn})
        print(f"   sigma_true {st:.4f} (mad del campo recortado a la escala {verdad['sigma_mad']:.5f}) -> "
              f"bilineal mad {e['sigma_mad']:.5f} pct {e['sigma_percentil']:.5f} r3 {e['sigma_recorte3']:.5f} med {e['mediana']:+.5f}"
              f" | nearest r3 {e_nn['sigma_recorte3']:.5f}")
    print("C2 instrumento muerto:")
    uni = np.zeros((H, W, 3), np.uint8)
    uni[:] = col6[np.abs(val6).argmin()]
    e_uni = extraer(uni, col6, val6)
    e_rnd = extraer(rng.integers(0, 256, (H, W, 3), dtype=np.uint8), col6, val6)
    print("   panel uniforme (color del 0):", e_uni)
    print("   ruido RGB puro:", e_rnd)
    print("C3 escala invertida sobre A6 real:")
    e_sign = M.estadisticos(M.por_celda(M.a_valores(dentro6, col6, -val6), 51))
    e_mirr = M.estadisticos(M.por_celda(M.a_valores(dentro6, col6, val6[::-1]), 51))
    print("   signo cambiado:", e_sign, "control mediana ok:", abs(e_sign["mediana"]) <= M.TOL_MEDIANA)
    print("   espejada      :", e_mirr, "control mediana ok:", abs(e_mirr["mediana"]) <= M.TOL_MEDIANA)
    print("C5 posicion de la mascara de alerta (celdas 51, centro 25.5, norte arriba):")
    c5 = {}
    for nombre in ["A2", "A6", "A7", "A9"]:
        try:
            c5[nombre] = alerta(imgs[nombre])
        except Exception as e:
            c5[nombre] = {"error": repr(e)}
        print("  ", nombre, c5[nombre])
    res["controles"] = {"C1": c1, "C2": {"uniforme": e_uni, "ruido": e_rnd},
                        "C3": {"signo": e_sign, "espejo": e_mirr}, "C5": c5}
    (OUT / "figuras_nativo.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
