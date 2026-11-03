# -*- coding: utf-8 -*-
"""Verificador S173 (ver_ablmodis): relectura propia de s173_cenit_modis.json, sin leer.py.

Pregunta 1 (si estuviera roto, lo veria?): calcula razon por pasada y por brazo desde los campos crudos del JSON,
con cuatro agregados (media con ceros, media sin ceros, mediana, razon de sumas), por tramo de cenit (<30, >=30),
Spearman con scipy, nulo por barajado (200, semilla 173 y 7), jackknife (sacar una pasada), y por separado los ceros.
Pregunta 2 (instrumento muerto?): control positivo = X2/V0 tiene que dar 2,000 en toda pasada con V0 > 0; si no
lo ve, el lector esta roto. Y V0 == V campo a campo.
Denominador: 27 pasadas MODIS de Chillan con alerta de MIROVA, 2026-09-29 a 2026-11-02 (lista del arnes).
"""
import io
import json
import sys
from collections import Counter

import numpy as np
from scipy.stats import spearmanr

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
J = "D:/vrp-trabajo/temporales/s173_aud/ablacion_modis_run/s173-cenit-modis/s173_cenit_modis.json"
d = json.load(open(J, encoding="utf-8"))
P = d["pasadas"]
print("commit del JSON:", d["commit"], "| n pasadas:", len(P))
print("estados:", Counter(e.get("estado") for e in P))
BR = ["V0", "X2", "FA", "FSH", "SC", "FA_SC", "RN", "G5", "NAT", "NAT_AREA"]


def mag(e, b):
    """Magnitud del brazo: vrp_mw del resumen (brazos de grilla y nativos); K y V: vrp_mw del slim."""
    if b in ("K", "V"):
        return float(e[b]["vrp_mw"] or 0.0)
    return float(e["brazos"][b]["vrp_mw"] or 0.0)


def pcmag(e, b):
    if b in ("K", "V"):
        return e[b].get("pc_vrp_mw")
    return e["brazos"][b].get("pc_vrp_mw")


z = np.array([e["z_record"] for e in P])
zi0 = np.array([e["geom_i0"]["sensor_zenith"] for e in P])
m = np.array([e["vrp_mirova_mw"] for e in P])
dts = [e["dt"] for e in P]
sens = [e["sensor"] for e in P]
print("\n== cenit: z_record contra sensor_zenith del pixel i0 (MxD03): max |dif| =", round(float(np.max(np.abs(z - zi0))), 2))
print("== tramos: n(<30) =", int((z < 30).sum()), " n(>=30) =", int((z >= 30).sum()))
print("== MIROVA (MW): min", m.min(), "max", m.max(), "; alertas <= 0,05 MW (regla SN):", int((m <= 0.05).sum()))
print("== dayflag:", Counter(e["dayflag"] for e in P), " sunglint min:", round(min(e["sunglint"] for e in P), 1))
print("== fechas por tramo:")
for lab, sel in (("<30", z < 30), (">=30", z >= 30)):
    print("  ", lab, [dts[i][:10] for i in np.nonzero(sel)[0]])
print("== sensor por tramo:", {lab: dict(Counter(sens[i] for i in np.nonzero(sel)[0])) for lab, sel in (("<30", z < 30), (">=30", z >= 30))})

# ---------------------------------------------------------------- controles
print("\n== CONTROLES")
print("control_produccion_igual:", Counter(e["control_produccion_igual"] for e in P))
print("control_produccion_dif:", Counter(json.dumps(e["control_produccion_dif"]) for e in P))
print("control_produccion_brazo:", Counter(e["control_produccion_brazo"] for e in P))
print("guardado_codigo_sha:", Counter(e["guardado_codigo_sha"] for e in P))
print("control_V0_igual_V:", Counter(e["control_V0_igual_V"] for e in P))
v0v = [(e["dt"], mag(e, "V0"), mag(e, "V"), e["brazos"]["V0"]["npix"], e["V"]["npix"]) for e in P
       if mag(e, "V0") != mag(e, "V") or e["brazos"]["V0"]["npix"] != e["V"]["npix"]]
print("V0 != V (mi comparacion vrp_mw y npix):", v0v)
pcv = [(e["dt"], pcmag(e, "V0"), pcmag(e, "V")) for e in P if pcmag(e, "V0") != pcmag(e, "V")]
print("V0.pc_vrp != V.pc_vrp:", pcv)
# K contra el guardado (slim): mis campos
kg = [(e["dt"], e["K"]["vrp_mw"], e["guardado"]["vrp_mw"], e["K"]["npix"], e["guardado"]["npix"]) for e in P
      if e["control_produccion_brazo"] == "K" and (e["K"]["vrp_mw"] != e["guardado"]["vrp_mw"] or e["K"]["npix"] != e["guardado"]["npix"] or e["K"]["pc_vrp_mw"] != e["guardado"]["pc_vrp_mw"])]
print("K != guardado (vrp/npix/pc, slim):", kg)
vg = [(e["dt"], e["V"]["vrp_mw"], e["guardado"]["vrp_mw"]) for e in P if e["control_produccion_brazo"] == "V" and (e["V"]["vrp_mw"] != e["guardado"]["vrp_mw"] or e["V"]["npix"] != e["guardado"]["npix"])]
print("V != guardado en las de control V:", vg, "| n control V:", sum(e["control_produccion_brazo"] == "V" for e in P))
# K contra la lista del arnes (disp_mw = lo que publico produccion segun la lista)
# control positivo X2
x2 = [(e["dt"], round(mag(e, "X2") / mag(e, "V0"), 4)) for e in P if mag(e, "V0") > 0]
print("X2/V0 por pasada (control positivo del lector):", sorted(set(r for _, r in x2)), "n", len(x2))
print("X2 celdas == V0 celdas:", all(e["brazos"]["X2"]["celdas"] == e["brazos"]["V0"]["celdas"] for e in P))
# publica
for b in ["K", "V"]:
    print(f"{b}_publica:", Counter(e[f"{b}_publica"] for e in P))
for b in BR:
    print(f"publica {b}:", Counter(e["brazos"][b].get("publica") for e in P))
print("pasadas con V_publica=1 y X2 publica=0:", [(e["dt"], e["V"]["vrp_mw"], e["brazos"]["X2"]["vrp_mw"], e["brazos"]["X2"]["distance_class"]) for e in P if e["V_publica"] == 1 and e["brazos"]["X2"]["publica"] == 0])
print("pasadas con V_publica=0 y V vrp>0:", [(e["dt"], e["V"]["vrp_mw"], e["V"]["distance_class"]) for e in P if e["V_publica"] == 0 and mag(e, "V") > 0])

# brazos que no cambian nada respecto a V0
print("\n== brazos contra V0 (n pasadas en que vrp_mw difiere de V0 / en que celdas difieren)")
for b in BR:
    nd = sum(mag(e, b) != mag(e, "V0") for e in P)
    nc = sum(e["brazos"][b].get("celdas") != e["brazos"]["V0"]["celdas"] for e in P) if "celdas" in P[0]["brazos"][b] else "s/celdas"
    print(f"  {b:9s} vrp difiere en {nd:2d} | celdas difieren en {nc}")

# ---------------------------------------------------------------- razones
rng0 = np.random.default_rng(173)


def nulo(r, zz, nperm=200, seed=173):
    rng = np.random.default_rng(seed)
    obs = spearmanr(r, zz).correlation
    perm = np.array([spearmanr(r, rng.permutation(zz)).correlation for _ in range(nperm)])
    p = float((np.abs(perm) >= abs(obs)).mean())
    return obs, float(np.percentile(perm, 2.5)), float(np.percentile(perm, 97.5)), p


def jack(r, zz):
    out = []
    for i in range(len(r)):
        k = np.ones(len(r), bool); k[i] = False
        out.append(spearmanr(r[k], zz[k]).correlation)
    return float(min(out)), float(max(out))


print("\n== RAZONES brazo/MIROVA por tramo (denominador: 27 pasadas, 2026-09-29 a 2026-11-02)")
print("brazo     | <30: media_c0 media_s0 mediana r_sumas n0 | >=30: media_c0 media_s0 mediana r_sumas n0 | rho(27) nulo95[173] p | rho sin ceros | jackknife min..max")
tabla = {}
for b in ["K", "V"] + BR:
    r = np.array([mag(e, b) / e["vrp_mirova_mw"] for e in P])
    tabla[b] = r
    fila = f"{b:9s} |"
    for sel in (z < 30, z >= 30):
        rr = r[sel]
        nz = rr[rr > 0]
        fila += f" {rr.mean():.3f} {nz.mean() if len(nz) else float('nan'):.3f} {np.median(rr):.3f} {np.array([mag(e,b) for e in P])[sel].sum()/m[sel].sum():.3f} {int((rr==0).sum())} |"
    obs, lo, hi, p = nulo(r, z)
    nzs = r > 0
    rho_nz = spearmanr(r[nzs], z[nzs]).correlation if nzs.sum() > 3 else float("nan")
    jmin, jmax = jack(r, z)
    fila += f" {obs:+.3f} [{lo:+.2f},{hi:+.2f}] p={p:.3f} | {rho_nz:+.3f} (n {int(nzs.sum())}) | {jmin:+.3f}..{jmax:+.3f}"
    print(fila)

print("\n== nulo con otra semilla (7) y 2000 barajados, K / FA / NAT / G5 / V:")
for b in ["K", "V", "FA", "NAT", "G5", "NAT_AREA"]:
    obs, lo, hi, p = nulo(tabla[b], z, nperm=2000, seed=7)
    print(f"  {b:9s} rho {obs:+.3f} nulo95 [{lo:+.2f},{hi:+.2f}] p={p:.4f}")

print("\n== Spearman de la razon contra la FECHA (confusor temporal) y cenit contra fecha:")
idx = np.arange(len(P))  # la lista viene ordenada por dt
for b in ["K", "V", "NAT", "G5"]:
    print(f"  {b:9s} rho(razon, orden de fecha) = {spearmanr(tabla[b], idx).correlation:+.3f}")
print(f"  rho(cenit, orden de fecha) = {spearmanr(z, idx).correlation:+.3f}")

print("\n== razones por pasada (dt, sensor, z, MIROVA, K, V, FA, NAT, G5, NAT_AREA, NAT npix, V0 npix, K npix, NAT dist_min_cumulo_km):")
for i, e in enumerate(P):
    print(f"  {e['dt']} {e['sensor'][6:11]} z={z[i]:5.2f} M={m[i]:6.2f} | K {tabla['K'][i]:.3f} V {tabla['V'][i]:.3f} FA {tabla['FA'][i]:.3f} NAT {tabla['NAT'][i]:.3f} G5 {tabla['G5'][i]:.3f} NATA {tabla['NAT_AREA'][i]:.3f} | npix NAT {e['brazos']['NAT']['npix']:2d} V0 {e['brazos']['V0']['npix']:2d} K {e['K']['npix']:2d} G5 {e['brazos']['G5']['npix']:2d} | NAT dcum {e['brazos']['NAT']['dist_min_cumulo_km']} motivo {e['brazos']['NAT']['motivo']}")

print("\n== NAT contra G5 pasada a pasada: Spearman de las razones y pares (NAT=0, G5=0):")
print("  rho(NAT, G5) =", round(spearmanr(tabla["NAT"], tabla["G5"]).correlation, 3),
      "| ceros NAT:", [dts[i] for i in np.nonzero(tabla["NAT"] == 0)[0]],
      "| ceros G5:", [dts[i] for i in np.nonzero(tabla["G5"] == 0)[0]],
      "| ceros K:", [dts[i] for i in np.nonzero(tabla["K"] == 0)[0]],
      "| ceros FA:", [dts[i] for i in np.nonzero(tabla["FA"] == 0)[0]])
print("  NAT/V por pasada bajo 30:", [(dts[i], round(tabla["NAT"][i] / tabla["V"][i], 3)) for i in np.nonzero(z < 30)[0] if tabla["V"][i] > 0])
print("  NAT/V por pasada >=30:", [(dts[i], round(tabla["NAT"][i] / tabla["V"][i], 3)) for i in np.nonzero(z >= 30)[0] if tabla["V"][i] > 0])
print("  NAT_AREA/NAT por pasada (y 1/cos^3 z):", [(dts[i], round(tabla["NAT_AREA"][i] / tabla["NAT"][i], 2), round(1 / np.cos(np.radians(z[i])) ** 3, 2)) for i in range(len(P)) if tabla["NAT"][i] > 0])
print("  FA/V por pasada:", [(dts[i], round(z[i], 1), round(tabla["FA"][i] / tabla["V"][i], 3)) for i in range(len(P)) if tabla["V"][i] > 0])
print("  K/V por pasada:", [(dts[i], round(z[i], 1), round(tabla["K"][i] / tabla["V"][i], 3)) for i in range(len(P)) if tabla["V"][i] > 0])
