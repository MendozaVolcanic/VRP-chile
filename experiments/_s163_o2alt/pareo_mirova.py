"""S163 O2 alternativa, parte 3: ¿qué variante del fondo reproduce mejor el VRP que MIROVA PUBLICÓ en sus alertas de
VIIRS 750, y alcanzan los datos para separarlas?

POR QUÉ. pert_contra_matlab.py mostró que la regla de desempate de MATLAB queda identificada (166 de 166 escenas). Falta
la otra mitad del camino de punta a punta: nuestras radiancias regrilladas + el código real de MIROVA, ¿dan el número
que MIROVA publicó? Y antes de leer un ganador, ¿el pareo tiene resolución para distinguir variantes que difieren
en un factor de hasta 1,8 sólo en alertas de un píxel?

Variantes por escena (mismas alertas, las de MATLAB): MATLAB R2026b (resultado_o2.mat, md5 abajo), shim de Octave
(salida_octave_s163.mat, re-corrida hoy), segundo port (R2) y primer port (O1).
Referencia: CSV consolidado del scraper (canal tabla, latest.php) en la raíz del worktree, Sensor == "VIIRS"
(= VIIRS 750), pareo por volcán y minuto exacto de Fecha_Satelite_UTC. Ventana avisada por calidad_referencia_mirova.

Unidad independiente = la PASADA (volcán y hora). Las variantes de grilla e interpolador de una misma pasada no son
independientes: se resumen primero por pasada (mediana) y después entre pasadas.

Pregunta 1 (¿mide lo que dice?): L_hot de cada variante es el de MATLAB (sólo cambia el fondo); el radio de la alerta
se compara con Distancia_km de MIROVA (radio, sin acimut: sólo descarta, A93/A107). Pregunta 2 (¿puede dar distinto
de cero?): control de potencia con verdad sembrada (MIROVA simulada = una variante × ruido del tamaño del piso
medido) sobre las 73 escenas de un píxel de O2: si con verdad sembrada el método no recupera la variante, un «no
separa» no dice nada de los datos.
"""
import csv
import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import scipy.io as sio

AQUI = Path(__file__).resolve().parent
EXP = AQUI.parent
RAIZ = EXP.parent
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(EXP / "_s158_audit_r2" / "oraculo"))
import calidad_referencia_mirova as CAL  # noqa: E402
import mirova_v750_r2 as R2  # noqa: E402

spec = importlib.util.spec_from_file_location("o1p", EXP / "_s158_oraculo_mirova" / "mirova_v750.py")
O1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(O1)

O2 = Path(r"C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\o2_paquete")
assert hashlib.md5((O2 / "resultado_o2.mat").read_bytes()).hexdigest() == "1f7fdc4bed0f8cb6223204bbce42ba43"
R = sio.loadmat(O2 / "resultado_o2.mat"); E = sio.loadmat(O2 / "entradas_o2.mat")
etq = json.loads((O2 / "entradas_o2_etiquetas.json").read_text(encoding="utf-8"))
OCT = sio.loadmat(AQUI / "salida_octave_s163.mat")
octA = OCT["ALERTAS"].ravel().astype(int); octO = OCT["OFFSET"].ravel().astype(int); octN = OCT["NALERT"].ravel().astype(int)
VAR = ("matlab", "shim", "r2", "o1")
RNG = np.random.default_rng(163)

# ---------------- referencia MIROVA ----------------
DESDE, HASTA = "2026-03-01", "2026-10-16"
CAL.avisar(DESDE, HASTA)
NOMBRES = {"Lascar": "Lascar", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "PuyehueCordonCaulle": "PuyehueCordonCaulle",
           "Nevados de Chillan": "NevadosDeChillan", "Villarrica": "Villarrica", "Tupungatito": "Tupungatito",
           "Chaiten": "Chaiten", "Llaima": "Llaima", "Isluga": "Isluga"}
pasadas = sorted({e["id"] for e in etq if e["familia"].startswith("chile")})
ref = defaultdict(list)
with open(RAIZ / "latest_consolidado.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["Sensor"] != "VIIRS":
            continue
        v = NOMBRES.get(r["Volcan"])
        if v is None:
            continue
        clave = f"{v}_{r['Fecha_Satelite_UTC'][:16].replace(' ', '_').replace(':', '')}"
        if clave in pasadas:
            ref[clave].append(r)
print("\nREFERENCIA (tabla, Sensor VIIRS = 750):")
mir = {}
for p in pasadas:
    filas = ref.get(p, [])
    al = [r for r in filas if r["Tipo_Registro"].startswith("ALERTA")]
    txt = "; ".join(f"{r['Tipo_Registro']} VRP {r['VRP_MW']} dist {r['Distancia_km']}" for r in filas) or "sin fila"
    print(f"  {p:38s} {txt}")
    if len(al) == 1 and float(al[0]["VRP_MW"]) > 0:
        mir[p] = (float(al[0]["VRP_MW"]), float(al[0]["Distancia_km"]), al[0]["Tipo_Registro"])
print(f"pasadas con alerta de MIROVA y VRP > 0: {len(mir)} de {len(pasadas)}")

# ---------------- VRP por variante en cada escena chilena ----------------
esc = []
for k, e in enumerate(etq):
    if not e["familia"].startswith("chile"):
        continue
    a = np.asarray(R["ALERTAS"][k, 0]).ravel().astype(int)
    if a.size == 0:
        continue
    io = e["idx_o1"]
    ao = octA[octO[io]:octO[io] + octN[io]]
    assert np.array_equal(np.sort(ao), np.sort(a)), "Octave y MATLAB detectan distinto"
    m13 = E["M13"][:, :, k].astype(float)
    mk = np.zeros(m13.shape, bool); mk[np.unravel_index(a - 1, m13.shape, order="F")] = True
    v = {"matlab": float(R["VRP"][k, 0]), "shim": float(OCT["VRP"].ravel()[io]),
         "r2": R2.vrp(m13, mk)["VRP_MW"], "o1": O1.vrp(m13, a - 1)[0]}
    rr, cc = np.unravel_index(a - 1, m13.shape, order="F")
    # radio desde el centro de la grilla (= centro MIROVA del volcán), con el corrimiento dx, dy de la variante
    xs = (cc - 33) * 750.0 + e["dx"]; ys = -(rr - 33) * 750.0 + e["dy"]
    radio = float(np.min(np.hypot(xs, ys)) / 1000)
    esc.append({"k": k, "pasada": e["id"], "familia": e["familia"], "metodo": e["metodo"], "caja": e["caja"],
                "dx": e["dx"], "dy": e["dy"], "npix": int(a.size), "radio_km": radio, **v})
print(f"\nescenas chilenas con alerta (MATLAB): {len(esc)}; detección Octave = MATLAB en todas (assert)")


def clase(n):
    return "1" if n == 1 else ("2-4" if n <= 4 else "5+")


def resumen(lista, etiqueta):
    """lista de escenas pareadas; devuelve por variante (n pasadas, n escenas, mediana |log|, sesgo mediano)."""
    porp = defaultdict(list)
    for s in lista:
        porp[s["pasada"]].append(s)
    out = {}
    print(f"\n  {etiqueta}: {len(porp)} pasadas, {len(lista)} escenas -> {sorted(porp)}")
    for vn in VAR:
        lp = [np.median([math.log(s[vn] / mir[p][0]) for s in ss]) for p, ss in porp.items()]
        lp = np.array(lp)
        out[vn] = (len(lp), np.median(np.abs(lp)) if lp.size else np.nan, np.median(lp) if lp.size else np.nan)
        print(f"    {vn:7s} n_pasadas {len(lp):2d} | mediana |log(VRP/MIROVA)| {out[vn][1]:.4f} | sesgo mediano "
              f"{out[vn][2]:+.4f} (x{math.exp(out[vn][2]) if lp.size else float('nan'):.3f}) | por pasada "
              + " ".join(f"{p.split('_')[0][:6]}{p.split('_')[1][5:]}:{x:+.3f}" for p, x in zip(porp, lp)))
    # prueba de signos por pasada: ¿MATLAB queda más cerca de MIROVA que cada modelo?
    for vn in ("shim", "r2", "o1"):
        g = e = q = 0
        for p, ss in porp.items():
            am = abs(np.median([math.log(s["matlab"] / mir[p][0]) for s in ss]))
            av = abs(np.median([math.log(s[vn] / mir[p][0]) for s in ss]))
            if abs(am - av) < 1e-9: e += 1
            elif am < av: g += 1
            else: q += 1
        print(f"    signos MATLAB contra {vn}: MATLAB mas cerca en {g}, mas lejos en {q}, empate en {e} pasadas")
    return out, porp


pares = [s for s in esc if s["pasada"] in mir and all(s[v] > 0 for v in VAR)]
lejos = [s for s in pares if abs(s["radio_km"] - mir[s["pasada"]][1]) > 1.5]
print(f"\nescenas pareadas: {len(pares)}; con radio propio a > 1,5 km del de MIROVA (probable otro objeto): {len(lejos)}"
      f" -> {sorted({s['pasada'] for s in lejos})}")
for s in sorted(pares, key=lambda s: (s["pasada"], s["npix"])):
    if s["familia"] == "chile_guardada":
        print(f"  {s['pasada']:38s} {s['metodo']:7s} {s['caja']:15s} np={s['npix']} r={s['radio_km']:.2f} km "
              f"(MIROVA {mir[s['pasada']][1]:.2f}) MIROVA {mir[s['pasada']][0]:.2f} | MATLAB {s['matlab']:.4f} "
              f"shim {s['shim']:.4f} R2 {s['r2']:.4f} O1 {s['o1']:.4f}")

print("\n=== TABLA (resumen por pasada) ===")
T = {}
for etiqueta, filtro in (("1 px, todas las variantes de grilla", lambda s: s["npix"] == 1),
                         ("1 px, radio compatible (<=1,5 km)", lambda s: s["npix"] == 1 and s not in lejos),
                         ("2-4 px (control), todas", lambda s: 2 <= s["npix"] <= 4),
                         ("2-4 px (control), radio compatible", lambda s: 2 <= s["npix"] <= 4 and s not in lejos),
                         ("5+ px", lambda s: s["npix"] >= 5),
                         ("escena por defecto (guardada, lineal, caja_def), cualquier npix",
                          lambda s: s["familia"] == "chile_guardada" and s["metodo"] == "linear" and s["caja"] == "caja_def")):
    T[etiqueta] = resumen([s for s in pares if filtro(s)], etiqueta)

# ---------------- cuánto difieren las variantes entre sí en estas escenas ----------------
uno = [s for s in pares if s["npix"] == 1]
dif = {vn: sum(abs(s[vn] / s["matlab"] - 1) > 1e-9 for s in uno) for vn in VAR}
print(f"\nen las {len(uno)} escenas pareadas de 1 px, variantes distintas de MATLAB (>1e-9): {dif}")
print("pasadas de 1 px donde alguna variante difiere de MATLAB: "
      f"{sorted({s['pasada'] for s in uno if any(abs(s[v]/s['matlab']-1) > 1e-9 for v in VAR)})}")

# ---------------- piso de ruido del pareo ----------------
# (a) dentro de una pasada, para una MISMA variante (MATLAB), cuánto se mueve el VRP con la grilla y el interpolador
#     de regrillado: eso es ruido NUESTRO (no viene del fondo de fillmissing2).
disp = []
for p, ss in defaultdict(list, {p: [s for s in esc if s["pasada"] == p and s["matlab"] > 0] for p in pasadas}).items():
    if len(ss) >= 3:
        l = np.log([s["matlab"] for s in ss]); disp.append((p, len(ss), float(np.median(np.abs(l - np.median(l))))))
print("\nPISO (a) dispersión de log(VRP MATLAB) entre variantes de grilla de una misma pasada (MAD):")
for p, n, d in disp:
    print(f"  {p:38s} n={n:2d} MAD {d:.3f}")
pisoA = float(np.median([d for _, _, d in disp]))
# (b) fondo de MATLAB contra los otros modelos en las MISMAS escenas: separación que habría que detectar
sep = np.array([abs(math.log(s[v] / s["matlab"])) for s in esc if s["npix"] == 1 and s["matlab"] > 0
                for v in ("shim", "r2", "o1") if s[v] > 0])
print(f"PISO (a) mediana de la MAD por pasada: {pisoA:.3f} (en log natural)")
print(f"SEÑAL (b) |log(variante/MATLAB)| en escenas chilenas de 1 px: mediana {np.median(sep):.4f}, "
      f"fracción > 0: {(sep > 1e-9).mean():.3f}, mediana de las > 0: {np.median(sep[sep > 1e-9]):.3f}")

# ---------------- nulos medidos ----------------
def mediana_abs(lista, vn, m):
    porp = defaultdict(list)
    for s in lista:
        porp[s["pasada"]].append(math.log(s[vn] / m[s["pasada"]]))
    return float(np.median([abs(np.median(x)) for x in porp.values()])) if porp else np.nan


def margen(lista, m):
    v = sorted((mediana_abs(lista, vn, m), vn) for vn in VAR)
    return v[1][0] - v[0][0], v[0][1]


print("\n=== NULOS ===")
for etiqueta, lista in (("1 px, todas", uno), ("1 px, radio compatible", [s for s in uno if s not in lejos])):
    if not lista:
        continue
    m0 = {p: mir[p][0] for p in mir}
    obs, gan = margen(lista, m0)
    ps = sorted({s["pasada"] for s in lista})
    # nulo 1: barajar el VRP de MIROVA dentro de cada volcán (entre las pasadas pareadas de 1 px)
    porv = defaultdict(list)
    for p in ps:
        porv[p.split("_")[0]].append(p)
    perm_posibles = int(np.prod([math.factorial(len(x)) for x in porv.values()]))
    nul1, gan1 = [], defaultdict(int)
    for _ in range(2000):
        m = {}
        for v, pp in porv.items():
            vals = [mir[p][0] for p in pp]; RNG.shuffle(vals); m.update(dict(zip(pp, vals)))
        d, g = margen(lista, m); nul1.append(d); gan1[g] += 1
    # nulo 2: barajar entre todas las pasadas
    nul2, gan2 = [], defaultdict(int)
    for _ in range(2000):
        vals = [mir[p][0] for p in ps]; RNG.shuffle(vals); m = dict(zip(ps, vals))
        d, g = margen(lista, m); nul2.append(d); gan2[g] += 1
    # bootstrap por pasada de la diferencia mejor - segunda (con el ganador observado fijo)
    seg = sorted((mediana_abs(lista, vn, m0), vn) for vn in VAR)[1][1]
    boots = []
    for _ in range(2000):
        bs = RNG.choice(ps, size=len(ps), replace=True)
        lb = []
        for i, p in enumerate(bs):
            lb += [dict(s, pasada=f"{p}#{i}") for s in lista if s["pasada"] == p]
        mb = {f"{p}#{i}": mir[p][0] for i, p in enumerate(bs)}
        boots.append(mediana_abs(lb, seg, mb) - mediana_abs(lb, gan, mb))
    boots = np.array(boots)
    # bootstrap por pasada de (mejor de los tres modelos - MATLAB): > 0 querría decir que MATLAB calza mejor
    bm = []
    for _ in range(2000):
        bs = RNG.choice(ps, size=len(ps), replace=True)
        lb = []
        for i, p in enumerate(bs):
            lb += [dict(s, pasada=f"{p}#{i}") for s in lista if s["pasada"] == p]
        mb = {f"{p}#{i}": mir[p][0] for i, p in enumerate(bs)}
        bm.append(min(mediana_abs(lb, v, mb) for v in ("shim", "r2", "o1")) - mediana_abs(lb, "matlab", mb))
    bm = np.array(bm)
    print(f"  {etiqueta}: {len(ps)} pasadas | ganador observado {gan}, segunda {seg}, margen {obs:.4f}")
    print(f"    nulo barajado dentro de volcán ({perm_posibles} permutaciones distintas posibles): p(margen>=obs) "
          f"{np.mean(np.array(nul1) >= obs - 1e-12):.3f}; ganadores {dict(gan1)}")
    print(f"    nulo barajado global: p(margen>=obs) {np.mean(np.array(nul2) >= obs - 1e-12):.3f}; "
          f"mediana del margen nulo {np.median(nul2):.4f}; ganadores {dict(gan2)}")
    print(f"    bootstrap por pasada de (segunda - ganador): mediana {np.median(boots):+.4f}, IC 95 % "
          f"[{np.percentile(boots, 2.5):+.4f}, {np.percentile(boots, 97.5):+.4f}], fracción <= 0: {np.mean(boots <= 0):.3f}")
    d0 = min(mediana_abs(lista, v, m0) for v in ("shim", "r2", "o1")) - mediana_abs(lista, "matlab", m0)
    print(f"    (mejor modelo - MATLAB) observado {d0:+.4f}; bootstrap por pasada mediana {np.median(bm):+.4f}, IC 95 % "
          f"[{np.percentile(bm, 2.5):+.4f}, {np.percentile(bm, 97.5):+.4f}], fracción > 0 (MATLAB mejor): {np.mean(bm > 0):.3f}")

# ---------------- control de potencia con verdad sembrada ----------------
# Población: las 73 escenas de 1 px de O2 (Etna excluida no aplica: Etna es 5 px), con las 4 variantes.
pop = []
for k, e in enumerate(etq):
    a = np.asarray(R["ALERTAS"][k, 0]).ravel().astype(int)
    if a.size != 1:
        continue
    m13 = E["M13"][:, :, k].astype(float); io = e["idx_o1"]
    mk = np.zeros(m13.shape, bool); mk[np.unravel_index(a - 1, m13.shape, order="F")] = True
    v = [float(R["VRP"][k, 0]), float(OCT["VRP"].ravel()[io]), R2.vrp(m13, mk)["VRP_MW"], O1.vrp(m13, a - 1)[0]]
    if min(v) > 0:
        pop.append(v)
pop = np.log(np.array(pop))
print(f"\n=== POTENCIA (verdad sembrada = MATLAB) sobre {len(pop)} escenas de 1 px de O2 con VRP > 0 en las 4 ===")
# sigma del ruido de pareo: del control de 2-4 px (mediana |log| = 0,674 sigma si es normal) y, aparte, el piso (a)
c24 = T["2-4 px (control), todas"][0]["matlab"][1]
sigmas = {"control 2-4 px": c24 / 0.6745 if np.isfinite(c24) else np.nan, "piso (a) grilla": pisoA / 0.6745,
          "1 px observado (MATLAB)": T["1 px, todas las variantes de grilla"][0]["matlab"][1] / 0.6745, "chico 0,05": 0.05}
for nom, sg in sigmas.items():
    if not np.isfinite(sg):
        print(f"  sigma {nom}: SIN DATO"); continue
    linea = []
    for n in (6, 20, 50, 100, 300, 1000):
        win = 0
        for _ in range(400):
            idx = RNG.integers(0, len(pop), n)
            obs = pop[idx, 0] + RNG.normal(0, sg, n)
            err = np.median(np.abs(pop[idx] - obs[:, None]), axis=0)
            win += int(np.argmin(err) == 0 and err[0] < np.partition(err, 1)[1])
        linea.append(f"n={n}: {win/400:.2f}")
    print(f"  sigma {nom} = {sg:.3f}: P(MATLAB gana estricto) " + " | ".join(linea))
print("  (azar entre 4 variantes = 0,25; con empates muchas escenas no separan nada porque las variantes coinciden)")
(AQUI / "pareo_mirova.json").write_text(json.dumps({"escenas": esc, "mirova": mir}, ensure_ascii=False, indent=0),
                                        encoding="utf-8")
