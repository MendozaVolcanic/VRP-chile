# -*- coding: utf-8 -*-
"""s03: clases de coincidencia antes y después de conservar la mancha, y el nulo al lado, con el MISMO código (lib177.clase).

Fenómeno: el volcán no mueve su foco de una pasada a otra más que unas celdas; nuestro punto (final_hotspot) y la mancha de MIROVA
caen ambos cerca del cráter siempre. Una clase «i» (la mancha a <= tolerancia de nuestro punto) puede decir «es el mismo foco de
esta noche» o sólo «ambos están en la misma zona». Lo que las separa es qué pasa cuando se pone en lugar de nuestro punto el de OTRA
pasada del mismo volcán y sensor: si sigue saliendo «i», la clase no identifica nada de la pasada, sólo la zona.

Pre-registro (escrito antes de correr):
  Variantes (todas con la función lib177.clase):
    F5b_recalc : mancha A (F5b), control con el centroide, clase por centroide. Debe reproducir las clases guardadas de F5b (305/305).
    C1         : mancha C1 (máscara de sin dato corregida), control con el centroide, clase por centroide.
    C2p (PRIMARIA): mancha C2 (C1 + empates), control «alguna celda de la mancha reproduce la Distancia_km de la tabla» (BLANDO: no es
                 «el píxel»), clase por distancia de nuestro punto al centroide de la componente principal <= tolerancia de F5b
                 (0,75 / 1,5 / 3,0 km).
    C2_cc      : C2 con control por centroide.
    C2_min     : C2p pero la clase por distancia a la celda más cercana de la mancha (BLANDO: «cae sobre o junto a la mancha»).
    C2_nc      : C2 sin control de distancia (sólo posición), centroide.
  Nulo N1: nuestro punto reemplazado por el de cada OTRA pasada del mismo volcán y sensor (todos los pares, exactos, sin sorteo).
  Nulo N2: igual, pero sólo pasadas a <= 3 días (el foco deriva lento: es el nulo más duro). N2b: <= 1 día.
  Estadísticos: tasa de «i» observada contra N1/N2; diferencia con IC95 por bootstrap sobre pasadas (2000, semilla 177); AUC = P(d propia <
  d de otra pasada) con empates 1/2 (0,5 = la lámina no distingue pasadas); p de permutación de la distancia media (20000 permutaciones).
  Lectura: «separa» si el IC95 de (observado - N1) no incluye 0 Y el AUC tiene IC95 sobre 0,5; «identifica el foco de esa noche» sólo si
  además la diferencia es grande frente a (1 - N1), es decir, si el nulo deja espacio.
Pregunta 1: ¿habría salido distinto si lo que dijimos fuera falso? Sí: si la lámina no tuviera información de pasada, observado = N1.
Pregunta 2: ¿puede el instrumento dar un resultado distinto? Se prueba con (a) reproducción de las clases de F5b, (b) el desplazamiento
  de nuestro punto en 8 direcciones, que debe sacar la clase «i» a medida que crece (s04), y (c) el nulo uniforme dentro del inner.
Universo: los 305 aciertos de F5b (alerta de MIROVA pareada a +-120 s con una pasada nuestra publicada, 2026-09-22 a 2026-11-06), 303 con
lámina, 2 sin lámina (cuentan como iv). Todo Chillán se mide por sensor; el resto de los volcanes sólo dentro de su propio volcán y sensor.
Salida: salidas/s03_clases_y_nulo.out.txt, salidas/s03_clases.csv
"""
import csv, datetime as dt, json, os, sys, collections
import numpy as np
import yaml
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib177 as M
L = M.L
sys.stdout.reconfigure(encoding="utf-8")
rng = np.random.default_rng(177)
V = {v["name"]: v for v in yaml.safe_load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\main\volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
S2 = json.load(open(os.path.join(HERE, "salidas", "s02_manchas.json"), encoding="utf-8"))
P8 = [x for x in json.load(open(os.path.join(HERE, "orig", "p8_clases.json"), encoding="utf-8")) if x.get("vol") != "_CONTROL_"]
CH = "NevadosDeChillan"


class FakeG(dict):
    pass


# --- reconstruir las Mancha de cada record y variante (hace falta la grilla de lat/lon: se recarga igual que en s02)
import rasterio
ARCH = {CH: "ChillanNevadosde"}
refs = json.load(open(os.path.join(HERE, "orig", "p6_tif_referencia_out.json"), encoding="utf-8"))
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
gr = {}


def grilla(vol, b):
    if (vol, b) not in gr:
        ref = refs[f"{ARCH.get(vol, vol)}|{b}"]["ref_sep"]
        g = L.grilla(os.path.join(TMP, "tif_ref", ARCH.get(vol, vol) + "_" + os.path.basename(ref["path"])))
        g["mc"] = (V[vol]["mirova_center_lat"], V[vol]["mirova_center_lon"])
        gr[(vol, b)] = g
    return gr[(vol, b)]


for o in S2:
    g = grilla(o["vol"], o["b"])
    for k in ("A", "C1", "C2"):
        o["M" + k] = M.Mancha(o[k], g, g["mc"])
    o["t"] = dt.datetime.strptime(o["dt"], "%Y-%m-%d %H:%M")
    o["pt"] = (o["our_lat"], o["our_lon"])
    o["dist"] = float(o["dist_tabla"]) if o["dist_tabla"] not in (None, "") else None
    o["estrato"] = (o["vol"], o["b"])
sin_lam = [x for x in P8 if not x.get("png")]

VAR = {
    "F5b_recalc": dict(m="MA", control="cent", metrica="cent", sin_control=False),
    "C1": dict(m="MC1", control="cent", metrica="cent", sin_control=False),
    "C2p": dict(m="MC2", control="any", metrica="cent", sin_control=False),
    "C2_cc": dict(m="MC2", control="cent", metrica="cent", sin_control=False),
    "C2_min": dict(m="MC2", control="any", metrica="min", sin_control=False),
    "C2_nc": dict(m="MC2", control="any", metrica="cent", sin_control=True),
}


def cl(o, v, punto=None):
    a = VAR[v]
    return M.clase(o[a["m"]], punto or o["pt"], o["dist"], o["b"], o["celda_km"], a["control"], a["metrica"], a["sin_control"])


# ---------------------------------------------------------------------------------------------------------------- 1. reproducción
print("== 1. Control: la función de clase con la mancha A reproduce las clases guardadas de F5b ==")
rep = sum(1 for o in S2 if cl(o, "F5b_recalc") == o["claseF5b"].rstrip("?"))
print(f"clase recalculada (mancha A, control por centroide) igual a la de p8_clases.json: {rep} de {len(S2)} con lámina (los {len(sin_lam)} sin lámina son iv por construcción)")
mal = [(o["vol"], o["sensor"], o["dt"], o["claseF5b"], cl(o, "F5b_recalc")) for o in S2 if cl(o, "F5b_recalc") != o["claseF5b"].rstrip("?")]
for m_ in mal[:10]:
    print("   difiere:", m_)

# ---------------------------------------------------------------------------------------------------------------- 2. antes y después
def tabla(filtro, titulo):
    print(f"\n--- {titulo} ---")
    print(f"{'universo':34s} {'n':>4s}  " + "  ".join(f"{v:>16s}" for v in ["F5b guardada"] + list(VAR)[1:]))
    return


def contar(sub, extra_iv=0, variante=None):
    c = collections.Counter()
    for o in sub:
        c[o["claseF5b"].rstrip("?") if variante is None else cl(o, variante)] += 1
    c["iv"] += extra_iv
    return c


print("\n== 2. Antes y después, mismo universo (305 aciertos; i / iii / iv) ==")
grupos = [
    ("TODOS (305)", lambda o: True, 2),
    ("Chillán VIIRS 375", lambda o: o["vol"] == CH and o["b"] == "VIIRS375", 0),
    ("Chillán VIIRS 750", lambda o: o["vol"] == CH and o["b"] == "VIIRS750", 0),
    ("Chillán MODIS (sin validar)", lambda o: o["vol"] == CH and o["b"] == "MODIS", 1),
    ("Chillán protegidas VIIRS 375", lambda o: o["vol"] == CH and o["b"] == "VIIRS375" and o["prot"] == "True", 0),
    ("Chillán protegidas VIIRS 750", lambda o: o["vol"] == CH and o["b"] == "VIIRS750" and o["prot"] == "True", 0),
    ("Chillán protegidas MODIS", lambda o: o["vol"] == CH and o["b"] == "MODIS" and o["prot"] == "True", 1),
    ("Resto VIIRS 375 (sin Chillán)", lambda o: o["vol"] != CH and o["b"] == "VIIRS375", 0),
    ("Resto VIIRS 750 (sin Chillán)", lambda o: o["vol"] != CH and o["b"] == "VIIRS750", 0),
    ("Resto MODIS (sin Chillán)", lambda o: o["vol"] != CH and o["b"] == "MODIS", 1),
]
nombres = ["F5b guardada"] + list(VAR)
print(f"{'universo':32s} {'n':>4s} | " + " | ".join(f"{v:>14s}" for v in nombres))
cuerpo_csv = []
for nom, f, extra in grupos:
    sub = [o for o in S2 if f(o)]
    celdas = []
    for v in [None] + list(VAR):
        c = contar(sub, extra, v)
        celdas.append(f"{c['i']:3d}/{c['iii']:3d}/{c['iv']:3d}")
        cuerpo_csv.append((nom, v or "F5b guardada", c["i"], c["iii"], c["iv"]))
    print(f"{nom:32s} {len(sub) + extra:4d} | " + " | ".join(f"{c:>14s}" for c in celdas))
with open(os.path.join(HERE, "salidas", "s03_clases.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["universo", "variante", "i", "iii", "iv"])
    w.writerows(cuerpo_csv)

print("\n--- Cambios de clase de F5b a C2p (mismo universo) ---")
trans = collections.Counter()
for o in S2:
    trans[(o["claseF5b"].rstrip("?"), cl(o, "C2p"))] += 1
print(dict(sorted(trans.items())))
print("Las 4 protegidas VIIRS de Chillán que F5b llamó (iii) (hallazgo 351):")
for o in S2:
    if o["vol"] == CH and o["claseF5b"].startswith("iii") and o["b"] != "MODIS":
        MC = o["MC2"]
        print(f"  {o['sensor']:14s} {o['dt']} {float(o['vrp']):6.2f} MW prot={o['prot']:5s} | F5b iii | C2p {cl(o, 'C2p'):3s} d_cent {MC.d_cent(*o['pt']):.2f} km (tol {L.TOL[o['b']]}), "
              f"d_min {MC.d_min(*o['pt']):.2f}, mancha {MC.n_celdas} celdas, componentes {MC.n_comps}, control-any {MC.ctrl_any(o['dist'], max(L.TOL[o['b']], o['celda_km']))}")
print("Los 6 MODIS (iii) de F5b en Chillán:")
for o in S2:
    if o["vol"] == CH and o["claseF5b"].startswith("iii") and o["b"] == "MODIS":
        MC = o["MC2"]
        print(f"  {o['sensor']:14s} {o['dt']} {float(o['vrp']):6.2f} MW | C2p {cl(o, 'C2p'):3s} d_cent {MC.d_cent(*o['pt']):.2f} km (tol 3), d_min {MC.d_min(*o['pt']):.2f}, mancha {MC.n_celdas} celdas")

# ---------------------------------------------------------------------------------------------------------------- 3. nulo
def matriz(sub, v, metrica_d):
    """D[i, j] = distancia (km) de la mancha de la pasada i al punto nuestro de la pasada j. clase_ij con lib177.clase (mismo código)."""
    n = len(sub)
    D = np.zeros((n, n))
    C = np.empty((n, n), dtype=object)
    for i, oi in enumerate(sub):
        for j, oj in enumerate(sub):
            C[i, j] = cl(oi, v, oj["pt"])
            a = VAR[v]
            D[i, j] = oi[a["m"]].d_cent(*oj["pt"]) if metrica_d == "cent" else oi[a["m"]].d_min(*oj["pt"])
    return D, C


def nulo(estratos, v, ventana_dias=None, etiqueta="", ctrl_ok_solo=True):
    """Observado y nulo en un conjunto de estratos (cada estrato (vol, sensor); los pares sólo dentro del estrato)."""
    obs, nul, auc, pesos, dpropia, dotras = [], [], [], [], [], []
    ps = []
    nperm_T = []
    for est in estratos:
        sub = [o for o in S2 if o["estrato"] == est]
        a = VAR[v]
        D, C = matriz(sub, v, a["metrica"])
        T = np.array([o["t"] for o in sub])
        for i, oi in enumerate(sub):
            otros = [j for j in range(len(sub)) if j != i and (ventana_dias is None or abs((T[j] - T[i]).total_seconds()) <= ventana_dias * 86400)]
            ci = C[i, i]
            if ci == "iv" and ctrl_ok_solo:
                continue
            if not otros:
                continue
            obs.append(1.0 if ci == "i" else 0.0)
            nul.append(float(np.mean([C[i, j] == "i" for j in otros])))
            dp = D[i, i]
            do = D[i, otros]
            auc.append(float(np.mean((do > dp + 1e-6) + 0.5 * (np.abs(do - dp) <= 1e-6))))
            dpropia.append(dp)
            dotras.append(float(np.mean(do)))
    obs, nul, auc = np.array(obs), np.array(nul), np.array(auc)
    n = len(obs)
    if n == 0:
        return None
    # bootstrap sobre pasadas
    idx = rng.integers(0, n, size=(2000, n))
    dif_b = (obs[idx].mean(axis=1) - nul[idx].mean(axis=1))
    auc_b = auc[idx].mean(axis=1)
    return dict(n=n, obs=obs.mean(), nul=nul.mean(), dif=obs.mean() - nul.mean(), dif_lo=np.percentile(dif_b, 2.5), dif_hi=np.percentile(dif_b, 97.5),
                auc=auc.mean(), auc_lo=np.percentile(auc_b, 2.5), auc_hi=np.percentile(auc_b, 97.5), dprop=float(np.mean(dpropia)), dotras=float(np.mean(dotras)))


def perm_p(estratos, v, nperm=20000):
    """p de permutación: media de d(mancha_i, nuestro_pi(i)) con pi aleatoria dentro del estrato, contra la media observada. Sólo pasadas con control ok."""
    a = VAR[v]
    Tobs, Tn = 0.0, None
    tot = 0
    for est in estratos:
        sub = [o for o in S2 if o["estrato"] == est and cl(o, v) != "iv"]
        if len(sub) < 3:
            continue
        D = np.array([[o[a["m"]].d_cent(*oj["pt"]) if a["metrica"] == "cent" else o[a["m"]].d_min(*oj["pt"]) for oj in sub] for o in sub])
        n = len(sub)
        Tobs += np.trace(D)
        perms = np.array([rng.permutation(n) for _ in range(nperm)])
        t = D[np.arange(n)[None, :], perms].sum(axis=1)
        Tn = t if Tn is None else Tn + t
        tot += n
    if tot == 0:
        return None
    return Tobs / tot, float(Tn.mean() / tot), float((1 + (Tn <= Tobs - 1e-9).sum()) / (1 + nperm))


estr = collections.Counter(o["estrato"] for o in S2)
chillan = {"Chillán VIIRS 375": [(CH, "VIIRS375")], "Chillán VIIRS 750": [(CH, "VIIRS750")], "Chillán MODIS (sin validar)": [(CH, "MODIS")]}
resto = {
    "Resto VIIRS 375 (por volcán)": [e for e in estr if e[1] == "VIIRS375" and e[0] != CH],
    "Resto VIIRS 750 (por volcán)": [e for e in estr if e[1] == "VIIRS750" and e[0] != CH],
}
grupos_n = {**chillan, **resto}


def linea(nom, r):
    if r is None:
        return f"{nom:30s} sin datos"
    return (f"{nom:30s} n={r['n']:3d} obs {r['obs']:.3f} | nulo {r['nul']:.3f} | dif {r['dif']:+.3f} [{r['dif_lo']:+.3f}, {r['dif_hi']:+.3f}] | "
            f"AUC {r['auc']:.3f} [{r['auc_lo']:.3f}, {r['auc_hi']:.3f}] | d media propia {r['dprop']:.2f} km, otras {r['dotras']:.2f} km")


print("\n== 3. Línea base roja: reproducir el nulo de V5B (m4) con la mancha A y las pasadas con control ok ==")
print("(V5B m4 con 30 sorteos por pasada: V375 todos los volcanes obs 0,948 nulo 0,730; V750 obs 0,940 nulo 0,769; mi nulo es exacto, sin sorteo)")
for nom, ests in (("V375 todos los volcanes (A)", [e for e in estr if e[1] == "VIIRS375"]), ("V750 todos los volcanes (A)", [e for e in estr if e[1] == "VIIRS750"])):
    print(linea(nom, nulo(ests, "F5b_recalc", None)))

RES = {}
for v in ("C1", "C2p", "C2_cc", "C2_min", "C2_nc"):
    print(f"\n== 4. Observado contra nulo, variante {v} (control: {VAR[v]['control'] if not VAR[v]['sin_control'] else 'ninguno'}; clase por {VAR[v]['metrica']}) ==")
    for nom, ests in grupos_n.items():
        for etiqueta, vent in (("N1 todas las otras pasadas", None), ("N2 a <= 3 días", 3), ("N2b a <= 1 día", 1)):
            r = nulo(ests, v, vent, etiqueta)
            RES[(v, nom, etiqueta)] = r
            print(linea(f"{nom} | {etiqueta.split(" ")[0]}", r))
        pp = perm_p(ests, v)
        if pp:
            print(f"{'':30s} permutación (distancia media, pasadas con control ok): propia {pp[0]:.3f} km, bajo permutación {pp[1]:.3f} km, p = {pp[2]:.4f}")

# ---------------------------------------------------------------------------------------------------------------- 5. nulo del control
print("\n== 5. ¿Cuánto filtra el control? Tasa en que la mancha de OTRA pasada también reproduce la Distancia_km de ESTA pasada (C2p: alguna celda) ==")
for nom, ests in grupos_n.items():
    ob, nu = [], []
    for est in ests:
        sub = [o for o in S2 if o["estrato"] == est and o["dist"] is not None]
        for i, oi in enumerate(sub):
            tolc = max(L.TOL[oi["b"]], oi["celda_km"])
            ob.append(oi["MC2"].ctrl_any(oi["dist"], tolc))
            nu.append(np.mean([oj["MC2"].ctrl_any(oi["dist"], tolc) for j, oj in enumerate(sub) if j != i]) if len(sub) > 1 else np.nan)
    print(f"{nom:30s} n={len(ob):3d} control propio ok {np.mean(ob):.3f} | la mancha de otra pasada lo pasa con {np.nanmean(nu):.3f}")

# ---------------------------------------------------------------------------------------------------------------- 6. tolerancias
print("\n== 6. Barrido de umbral (C2, sin control, centroide): fracción de pasadas con la mancha a <= k celdas de nuestro punto, propia contra otras pasadas (N1) ==")
for nom, ests in chillan.items():
    sub = [o for o in S2 if o["estrato"] == ests[0]]
    D = np.array([[oi["MC2"].d_cent(*oj["pt"]) for oj in sub] for oi in sub])
    celda = sub[0]["celda_km"]
    n = len(sub)
    fila = []
    for k in (0.5, 1, 1.5, 2, 3, 4, 6):
        thr = k * celda
        prop = np.mean(np.diag(D) <= thr)
        otras = np.mean([(D[i][np.arange(n) != i] <= thr).mean() for i in range(n)])
        fila.append(f"{k}c: {prop:.2f}/{otras:.2f}")
    print(f"{nom:30s} (celda {celda:.3f} km, tolerancia F5b {L.TOL[sub[0]['b']]} km = {L.TOL[sub[0]['b']] / celda:.1f} celdas) propia/otras: " + "  ".join(fila))

# ---------------------------------------------------------------------------------------------------------------- 7. dispersión
print("\n== 7. Cuánto se mueve el foco entre pasadas (Chillán, dispersión de nuestro punto y del centroide de la mancha, km) ==")
for nom, ests in chillan.items():
    sub = [o for o in S2 if o["estrato"] == ests[0]]
    la0, lo0 = np.median([o["our_lat"] for o in sub]), np.median([o["our_lon"] for o in sub])
    def en(la, lo):
        return ((lo - lo0) * 111.32 * np.cos(np.radians(la0)), (la - la0) * 110.57)
    ne = np.array([en(o["our_lat"], o["our_lon"]) for o in sub])
    me = np.array([en(o["MC2"].lat, o["MC2"].lon) for o in sub])
    print(f"{nom:30s} n={len(sub)}  desv. estándar nuestro (E,N) = ({ne[:, 0].std():.2f}, {ne[:, 1].std():.2f}) km; de la mancha = ({me[:, 0].std():.2f}, {me[:, 1].std():.2f}) km; "
          f"puntos nuestros distintos: {len({(round(o['our_lat'], 5), round(o['our_lon'], 5)) for o in sub})}; centroides de mancha distintos: {len({(round(o['MC2'].lat, 5), round(o['MC2'].lon, 5)) for o in sub})}; celda {sub[0]['celda_km']:.2f} km")
    # correlación pasada a pasada y su permutación
    rE, rN = np.corrcoef(ne[:, 0], me[:, 0])[0, 1], np.corrcoef(ne[:, 1], me[:, 1])[0, 1]
    pe = np.array([np.corrcoef(ne[:, 0], me[rng.permutation(len(sub)), 0])[0, 1] for _ in range(5000)])
    pn = np.array([np.corrcoef(ne[:, 1], me[rng.permutation(len(sub)), 1])[0, 1] for _ in range(5000)])
    print(f"{'':30s} correlación entre pasadas nuestro vs mancha: este r={rE:+.2f} (p perm {(1 + (pe >= rE).sum()) / 5001:.4f}), norte r={rN:+.2f} (p perm {(1 + (pn >= rN).sum()) / 5001:.4f})")
