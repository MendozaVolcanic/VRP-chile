"""O1 (S159): compara, escena a escena, la lista de alertas que da el .m ORIGINAL de MIROVA corrido en GNU Octave 11.3
contra los dos ports en Python (primer oráculo `_s158_oraculo_mirova/mirova_v750.py`, segundo
`_s158_audit_r2/oraculo/mirova_v750_r2.py`).

Pregunta 1: si un port tradujera mal un paso, ¿se vería? Sí en las escenas que lo ejercen: se compara el CONJUNTO de
píxeles y además la SECUENCIA exacta (orden de concatenación del .m). Los controles positivos son cuatro copias mutadas
del .m; cada una se compara contra la misma mutación aplicada al segundo port, y se cuenta en cuántas escenas la
mutación cambia la salida de Octave (si fuera 0 en todas, el instrumento no ve).
Pregunta 2: si Octave estuviera muerto o leyera mal las entradas, Etna no daría los 5 píxeles conocidos ni el
Tot_Lmir_hot del OSF (se exige) y el conteo de escenas con alerta caería a 0 (se informa por familia).
Denominador: 791 escenas (1 Etna, 40 chilenas guardadas, 150 variantes chilenas, 600 sintéticas). Ventana: las 10
pasadas chilenas van del 2026-03-01 al 2026-10-16 (run 39641637298); Etna es 2023-05-19 00:54 UTC.
"""
import importlib.util
import json
import sys
import types
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import scipy.io as sio

AQUI = Path(__file__).resolve().parent
EXP = AQUI.parents[1]
sys.path.insert(0, str(EXP / "_s158_audit_r2" / "oraculo"))
import mirova_v750_r2 as R2  # noqa: E402

spec = importlib.util.spec_from_file_location("o1port", EXP / "_s158_oraculo_mirova" / "mirova_v750.py")
O1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(O1)

E = sio.loadmat(AQUI / "entradas.mat")
etq = json.loads((AQUI / "entradas_etiquetas.json").read_text(encoding="utf-8"))
K = E["M13"].shape[2]
assert K == len(etq)


def leer_oct(nombre):
    s = sio.loadmat(AQUI / nombre)
    A = s["ALERTAS"].ravel().astype(int); off = s["OFFSET"].ravel().astype(int); n = s["NALERT"].ravel().astype(int)
    return [A[off[k]:off[k] + n[k]].tolist() for k in range(K)]


def r2_mutante(viejo, nuevo):
    src = Path(R2.__file__).read_text(encoding="utf-8")
    assert src.count(viejo) == 1, viejo
    mod = types.ModuleType("r2m"); exec(compile(src.replace(viejo, nuevo), "r2m", "exec"), mod.__dict__)
    return mod.detectar


NOCHE = "u_abs, s1, s2, n1, n2, e1, e2 = -0.7, 10, 5, 0.02, 0.003, 0.01, 0.003"
MUT = {
    "min2": r2_mutante(NOCHE, NOCHE.replace("0.02, 0.003, 0.01", "0.02, 0.03, 0.01")),
    "k1": r2_mutante(NOCHE, NOCHE.replace("-0.7,", "-0.8,")),
    "sigma": r2_mutante(NOCHE, NOCHE.replace("10, 5,", "5, 10,")),
    "sinp2": r2_mutante("p2 = _pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, absol | ctx1,",
                        "p2 = _pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, absol | ctx1 | True,"),
}

def esc(k):
    return E["M13"][:, :, k], E["M15"][:, :, k], E["BOX"][:, :, k], E["DAY"].ravel()[k], E["SG"].ravel()[k]


oc = leer_oct("salida_original.mat")
# Etna como control del instrumento
m13e = esc(0)[0]
lhot = float(np.sum(m13e.ravel(order="F")[np.array(oc[0]) - 1]))
assert len(oc[0]) == 5 and abs(lhot - 1.965342180) < 5e-10, (oc[0], lhot)
print(f"Etna Octave: {oc[0]} Tot_Lmir_hot={lhot:.9f} (OSF 1.965342180)")

# base de índices del primer port
al_e = np.asarray(O1.hotspot_detection(*esc(0)), int).ravel()
BASE = 1 if sorted(al_e.tolist()) == sorted(oc[0]) else (0 if sorted((al_e + 1).tolist()) == sorted(oc[0]) else None)
assert BASE is not None
print("base de índices del primer port:", BASE)

fam_tot, fam_alerta = Counter(), Counter()
dif = {"r2_conj": defaultdict(list), "r2_sec": defaultdict(list), "o1_conj": defaultdict(list), "o1_sec": defaultdict(list)}
for k in range(K):
    f = etq[k]["familia"]; fam_tot[f] += 1
    if oc[k]: fam_alerta[f] += 1
    _, l2 = R2.detectar(*esc(k))
    l1 = (np.asarray(O1.hotspot_detection(*esc(k)), int).ravel() + (1 - BASE)).tolist()
    if sorted(l2) != sorted(oc[k]): dif["r2_conj"][f].append(k)
    if list(l2) != oc[k]: dif["r2_sec"][f].append(k)
    if sorted(l1) != sorted(oc[k]): dif["o1_conj"][f].append(k)
    if l1 != oc[k]: dif["o1_sec"][f].append(k)

print("\n== Original: escenas por familia (con alerta en Octave)")
for f in fam_tot: print(f"   {f}: {fam_tot[f]} ({fam_alerta[f]} con alerta)")
print("== Discrepancias Octave vs ports (escenas distintas por familia)")
for nom, d in dif.items():
    print(f"   {nom}: total {sum(len(v) for v in d.values())} | " + ", ".join(f"{f}={len(d.get(f, []))}" for f in fam_tot))
    for f, v in d.items():
        for k in v[:5]:
            print(f"      ej {etq[k]} oct={oc[k]}")

# pasadas chilenas guardadas: tabla
print("\n== Pasadas chilenas (matrices guardadas por el run): alertas Octave")
for k in range(K):
    e = etq[k]
    if e["familia"] == "chile_guardada":
        print(f"   {e['id']:38s} {e['metodo']:7s} {e['caja']:15s} oct={oc[k]}")
print("== Variantes chilenas con alerta en Octave")
for k in range(K):
    e = etq[k]
    if e["familia"] == "chile_variante" and oc[k]:
        print(f"   {e['id']:38s} {e['metodo']:7s} dx={e['dx']:5d} dy={e['dy']:5d} oct={oc[k]}")

print("\n== Controles positivos: copias mutadas del .m en Octave")
for nom, det in MUT.items():
    om = leer_oct(f"salida_mut_{nom}.mat")
    cambia = Counter(etq[k]["familia"] for k in range(K) if sorted(om[k]) != sorted(oc[k]))
    no_coincide = [k for k in range(K) if sorted(om[k]) != sorted(det(*esc(k))[1])]
    cambia_r2 = Counter(etq[k]["familia"] for k in range(K) if sorted(det(*esc(k))[1]) != sorted(R2.detectar(*esc(k))[1]))
    print(f"   {nom}: Octave mutado != Octave original en {sum(cambia.values())} escenas {dict(cambia)} | "
          f"R2 mutado != R2 original en {sum(cambia_r2.values())} {dict(cambia_r2)} | Octave mutado != R2 mutado: {len(no_coincide)}")
    for k in no_coincide[:5]:
        print(f"      ej {etq[k]} oct_mut={om[k]}")
    if nom == "k1":
        for k in range(K):
            if sorted(om[k]) != sorted(oc[k]):
                print(f"      k1 cambia: {etq[k]} oct={oc[k]} oct_mut={om[k]}")
