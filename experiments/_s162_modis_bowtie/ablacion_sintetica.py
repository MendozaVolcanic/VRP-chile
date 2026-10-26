# -*- coding: utf-8 -*-
"""S162 MOD-E (D28, bow tie de MODIS), paso 2 sin red: ablacion SINTETICA de la eliminacion de duplicados del bow tie
dentro del port del codigo de MIROVA (envoltorio `mirova_port.correr` de S159, deteccion y fondo del oraculo validado
contra Octave), con la geometria de barrido de MODIS.

POR QUE SINTETICA. Las grillas guardadas del lote del port (D:/vrp-trabajo/temporales/s159_portes/run_39712862945) ya
estan remuestreadas a 51 x 51: no traen los pixeles nativos ni su linea y su frame, asi que con ellas no se puede quitar
un duplicado (verificado al abrir los .npz: solo mir, tir, mir_b21, mir_geo5, tir_geo5). Lo que si se puede sin red es
medir el MECANISMO: cuanto cambia lo que mide el codigo de MIROVA si se quitan o no los duplicados, en funcion del angulo
de barrido, con un foco de potencia conocida. Eso dice si D28 puede explicar una diferencia del tamano que se ve en los
datos (paso 1: la razon port/MIROVA sube de 0,96 en el nadir a ~1,1 sobre 40 grados). La medicion real queda para el
lote de MOD-C, que guarda los recortes nativos.

EL FENOMENO. MODIS barre de lado a lado con 10 detectores; cada barrido avanza 10 km sobre el suelo. En el nadir cada
detector ve 1 km y los barridos se tocan sin traslaparse. Hacia el borde la distancia al suelo crece, la huella de cada
detector se estira a lo largo de la traza y los barridos vecinos se pisan: el mismo suelo aparece dos veces, medido por
el detector 9 de un barrido y el 0 del siguiente (bow tie). MIROVA quita esos duplicados antes de remuestrear (D28); el
port remuestrea con todos.

GEOMETRIA (modelo, declarado): Tierra esferica R = 6.371 km, altura 705 km (Terra y Aqua), IFOV = 1/705 rad (1 km en el
nadir). Para el angulo de barrido t: distancia oblicua r(t), cenit z(t) = asin((R + H)/R sen t); huella a lo largo de la
traza a = IFOV r, a lo ancho b = IFOV r / cos z; frames cada IFOV en t. Detector d del barrido s centrado en
y = 10 s + (d - 4,5) a km. Un foco de area A_s a T_s se reparte en los pixeles cuya huella lo contiene (rectangular, sin
PSF), con exceso de radiancia (B(T_s) - B(T_bg)) A_s / (a b) en MIR (3,959 um) y TIR (11,03 um).

BRAZOS: TODOS (los pixeles nativos, como el port) y SIN_DUP (cada barrido conserva solo los detectores cuyo centro cae en
su franja nominal de 10 km, |y - 10 s| < 5 km: es la eliminacion por filas de borde, una de las dos lecturas de D28; la
de Coppola 2010 no esta localizada, SOSPECHA). En el nadir los dos brazos son identicos (control negativo).

Las dos preguntas del instrumento:
1. Si quitar duplicados no hiciera nada, ¿se veria? Si: en el nadir los brazos tienen que dar exactamente lo mismo
   (control negativo exigido); con traslape, el numero de pixeles nativos difiere y se informa.
2. Si el port no viera el foco, ¿se veria? Si: se informa la fraccion de focos detectados por brazo y angulo, y la razon
   medido / verdadero; un foco no detectado no entra a la razon. Control positivo: en el nadir la razon tiene que quedar
   cerca de 1 (la suma del codigo conserva la energia del foco en una grilla de 1 km).

Uso: python -I ablacion_sintetica.py --port DIR_DE_mirova_port.py [--n 40]
"""
import argparse
import io
import json
import math
import statistics as st
import sys
from pathlib import Path

import numpy as np

R, H = 6371.0, 705.0
IFOV = 1.0 / H
SIN_GLINT = 180.0                         # de noche no hay reflejo: angulo de sun-glint lejos del umbral de 12 grados
C1, C2 = 1.191042e8, 1.4387752e4          # Planck en W m-2 sr-1 um-1 con lambda en um


def planck(lam, t):
    return C1 / (lam ** 5 * (np.exp(C2 / (lam * t)) - 1.0))


def geom(t):
    """Distancia oblicua, cenit (rad) y distancia sobre el suelo desde el nadir (km) para el angulo de barrido t."""
    z = math.asin((R + H) / R * math.sin(t))
    r = (R + H) * math.cos(t) - math.sqrt(R * R - (R + H) ** 2 * math.sin(t) ** 2)
    return r, z, R * (z - t)


def escena(t_c, x_s, y_s, a_s_km2, ts, rng, t_bg=(265.0, 262.0), ruido=0.3, n_frames=71, n_barridos=8):
    """Pixeles nativos alrededor del volcan (0, 0): x a lo ancho, y a lo largo (km). Devuelve listas por pixel."""
    _, _, s_c = geom(t_c)
    xs, ys, mir, tir, barrido, det = [], [], [], [], [], []
    lam_m, lam_t = 3.959, 11.03
    for j in range(n_frames):
        t = t_c + (j - n_frames // 2) * IFOV
        r, z, s = geom(t)
        a, b = IFOV * r, IFOV * r / math.cos(z)
        x = s - s_c
        for sb in range(-n_barridos // 2, n_barridos // 2):
            for d in range(10):
                y = 10.0 * sb + (d - 4.5) * a
                bt_m = t_bg[0] + rng.normal(0, ruido)
                bt_t = t_bg[1] + rng.normal(0, ruido)
                lm, lt = float(planck(lam_m, bt_m)), float(planck(lam_t, bt_t))
                if abs(x_s - x) <= b / 2 and abs(y_s - y) <= a / 2:
                    lm += float(planck(lam_m, ts) - planck(lam_m, t_bg[0])) * a_s_km2 / (a * b)
                    lt += float(planck(lam_t, ts) - planck(lam_t, t_bg[1])) * a_s_km2 / (a * b)
                xs.append(x); ys.append(y); mir.append(lm); tir.append(lt); barrido.append(sb); det.append(d)
    return {k: np.asarray(v) for k, v in (("x", xs), ("y", ys), ("mir", mir), ("tir", tir), ("barrido", barrido),
                                           ("det", det))}


def grillar(e, sel, g, MP):
    from scipy.interpolate import griddata
    X, Y = MP.centros(g)
    pts = np.column_stack([e["x"][sel] * 1000.0, e["y"][sel] * 1000.0])
    return [griddata(pts, e[k][sel], (X, Y), method="linear") for k in ("mir", "tir")]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", required=True, help="carpeta de mirova_port.py (rama s159-pruebas)")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--vrp", type=float, default=1.0, help="VRP verdadero del foco, MW")
    a = ap.parse_args()
    sys.path.insert(0, a.port)
    import mirova_port as MP
    cfg = MP.SENSORES["MODIS"]
    g = {"ul_x": -25500.0, "ul_y": 25500.0, "n": 51, "celda": 1000.0}
    ts, vrp_obj = 1000.0, a.vrp                  # foco de 1000 K (1 MW es el orden de una alerta de Lascar)
    lam_m = 3.959
    dl_int = vrp_obj * 1e6 / (cfg["coef"] * cfg["area"])          # integral de deltaL MIR que da 1 MW
    a_s = dl_int / float(planck(lam_m, ts) - planck(lam_m, 265.0))  # km2
    print(f"foco: {ts:.0f} K, area {a_s * 1e6:.1f} m2, VRP verdadero {vrp_obj} MW (coef MODIS del port)")
    rng = np.random.default_rng(20261024)
    filas = []
    for deg in (0.0, 20.0, 30.0, 40.0, 45.0, 50.0, 55.0):
        t_c = math.radians(deg)
        r, z, _ = geom(t_c)
        aa = IFOV * r
        pos = rng.uniform(-0.5, 0.5, size=(a.n, 2)) * np.array([2.0, 10.0])   # foco al azar en +-1 km x +-5 km
        for k, (xs_, ys_) in enumerate(pos):
            e = escena(t_c, float(xs_), float(ys_), a_s, ts, np.random.default_rng(1000 + k))
            todos = np.ones(e["x"].size, bool)
            sin_dup = np.abs(e["y"] - 10.0 * e["barrido"]) < 5.0
            fila = {"angulo": deg, "cenit": round(math.degrees(z), 1), "huella_traza_km": round(aa, 3), "k": k,
                    "foco_xy": [round(float(xs_), 3), round(float(ys_), 3)],
                    "n_pix": {"TODOS": int(todos.sum()), "SIN_DUP": int(sin_dup.sum())},
}
            for nombre, sel in (("TODOS", todos), ("SIN_DUP", sin_dup)):
                mir, tir = grillar(e, sel, g, MP)
                o = MP.correr(mir, tir, g, 0.0, 0.0, 0, SIN_GLINT, cfg, modo="fisica", semillas=0)
                fila[nombre] = {"npix": o["npix"], "vrp_mw": o["vrp_mw"], "motivo": o["motivo_vacio"]}
            filas.append(fila)
    print("angulo cenit huella  n_pix(T/S)  detecta T/S   razon_T mediana [n]  razon_S mediana [n]  S/T mediana [n]")
    resumen = {}
    for deg in sorted({f["angulo"] for f in filas}):
        fs = [f for f in filas if f["angulo"] == deg]
        rt = [f["TODOS"]["vrp_mw"] / vrp_obj for f in fs if f["TODOS"]["npix"]]
        rs = [f["SIN_DUP"]["vrp_mw"] / vrp_obj for f in fs if f["SIN_DUP"]["npix"]]
        st_ = [f["SIN_DUP"]["vrp_mw"] / f["TODOS"]["vrp_mw"] for f in fs if f["TODOS"]["npix"] and f["SIN_DUP"]["npix"]]
        dt, ds = sum(1 for f in fs if f["TODOS"]["npix"]), sum(1 for f in fs if f["SIN_DUP"]["npix"])
        med = lambda x: round(st.median(x), 3) if x else None  # noqa: E731
        resumen[deg] = {"cenit": fs[0]["cenit"], "huella": fs[0]["huella_traza_km"], "n": len(fs),
                        "n_pix": [fs[0]["n_pix"]["TODOS"], fs[0]["n_pix"]["SIN_DUP"]], "detecta": [dt, ds],
                        "razon_todos": med(rt), "razon_sin_dup": med(rs), "sin_dup_sobre_todos": med(st_),
                        "sin_dup_sobre_todos_p10_p90": ([round(float(np.percentile(st_, 10)), 3),
                                                         round(float(np.percentile(st_, 90)), 3)] if st_ else None)}
        x = resumen[deg]
        print(f"{deg:6.0f} {x['cenit']:5.1f} {x['huella']:6.3f}  {x['n_pix'][0]}/{x['n_pix'][1]}   {dt:>2}/{ds:<2} de {len(fs)}"
              f"   {x['razon_todos']} [{len(rt)}]   {x['razon_sin_dup']} [{len(rs)}]   {x['sin_dup_sobre_todos']} "
              f"[{len(st_)}] p10-p90 {x['sin_dup_sobre_todos_p10_p90']}")
    nadir = [f for f in filas if f["angulo"] == 0.0]
    ctl = all(f["TODOS"] == f["SIN_DUP"] for f in nadir) and nadir[0]["n_pix"]["TODOS"] == nadir[0]["n_pix"]["SIN_DUP"]
    print("control negativo (nadir, brazos identicos):", "OK" if ctl else "FALLA")
    Path(__file__).with_name("ablacion_sintetica_%gMW.json" % a.vrp).write_text(json.dumps({"resumen": resumen, "filas": filas},
                                                                              indent=1), encoding="utf-8")
    sys.exit(0 if ctl else 2)


if __name__ == "__main__":
    main()
