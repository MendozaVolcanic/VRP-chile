"""S159, frente «el código OSF de MIROVA, entero»: dos mediciones de apoyo al INFORME.md de esta carpeta.

Las dos preguntas del instrumento, en el encabezado:

1. Si lo que mido estuviera roto, ¿lo vería?
   A) Cobertura de identificadores: si un paso del `.m` no tuviera NINGÚN rastro en `pipeline/`, el conteo
      de archivos con esa señal daría 0. Un paso portado con otro nombre daría un falso «no existe»: por eso
      cada token se eligió con el nombre del FENÓMENO (glint, 200 K, dilatación, fillmissing) y no del
      identificador de MATLAB, y el resultado sólo se usa como respaldo de una lectura hecha a mano.
   B) Compuertas del `.m` sobre las 791 escenas de O1: si una compuerta nunca disparara en ninguna familia,
      «no tiene sustrato» sería la lectura; si disparara en sintéticas y no en chilenas, la lectura es «no hay
      sustrato en Chile hoy». Se cuentan las dos por separado.
2. Si el instrumento estuviera muerto, ¿se vería distinto?
   A) Control positivo: `polyfit` (sabemos que `pipeline/detection_context.py` lo usa) tiene que dar > 0 archivos.
      Control negativo: un token inventado tiene que dar 0.
   B) Control positivo: Etna tiene que dar 5 alertas y Tot_Lmir_hot 1,965342180 (el número del OSF); y las
      sintéticas traen sun-glint de 5 a 20° y escenas con 30 a 60 % de M15 inválido (O1 §2.1), así que las
      compuertas 1 y 4 TIENEN que disparar ahí. Si no disparan, el instrumento está muerto.

Denominadores: A) todos los `.py` de `pipeline/`; B) 791 escenas de `experiments/_s159/o1/entradas.mat`
(Etna 2023-05-19; 190 chilenas del 2026-03-01 al 2026-10-16; 600 sintéticas de semilla 7).

Uso: PYTHONIOENCODING=utf-8 python pasos_del_m.py  (desde cualquier carpeta; rutas absolutas abajo).
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import scipy.io as sio

RAIZ = Path(r"C:\vrp-trabajo\s159-pruebas")
PIPELINE = RAIZ / "pipeline"
O1 = RAIZ / "experiments" / "_s159" / "o1"
ORACULO = RAIZ / "experiments" / "_s158_oraculo_mirova"
SALIDA = Path(__file__).with_name("pasos_del_m_salida.txt")

sys.path.insert(0, str(ORACULO))
import mirova_v750 as mv  # noqa: E402  (port del .m validado en O1: 791/791 contra Octave)

lineas: list[str] = []


def p(s: str = "") -> None:
    print(s)
    lineas.append(s)


# ----------------------------------------------------------------------------------------------
# A) Cobertura de identificadores en pipeline/
# ----------------------------------------------------------------------------------------------
TOKENS = {
    "paso 1 sun-glint": r"glint",
    "paso 3 píxel frío ≤ 200 K": r"<=\s*200|200\.0?\s*K|200\)",
    "paso 4 escena con ≥ mitad NaN": r"numel|mitad de NaN|50\s*% de NaN|maximumMissing",
    "paso 9 unión sin unique": r"np\.unique|unique\(",
    "V dilatación del hueco": r"dilat|imdilate|binary_dilation",
    "V interpolación 2D del fondo": r"fillmissing|griddata|interp2|LinearNDInterpolator",
    "V VRP NaN sin alerta": r"vrp_mw.{0,20}nan|= np\.nan  # sin alerta",
    "control positivo (polyfit)": r"polyfit",
    "control negativo (token inventado)": r"zzqxv_no_existe_jamas",
}

p("# A) Cobertura de identificadores en pipeline/*.py (archivo:línea de la primera coincidencia)")
archivos = sorted(PIPELINE.glob("*.py"))
p(f"denominador: {len(archivos)} archivos .py en {PIPELINE}")
for nombre, patron in TOKENS.items():
    rx = re.compile(patron)
    hits = []
    for f in archivos:
        for i, ln in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if rx.search(ln):
                hits.append(f"{f.name}:{i}")
                break
    p(f"  {nombre:38s} archivos={len(hits):2d}  {' '.join(hits[:6])}")
p()

# ----------------------------------------------------------------------------------------------
# B) Compuertas del .m sobre las 791 escenas de O1, por familia
# ----------------------------------------------------------------------------------------------
m = sio.loadmat(O1 / "entradas.mat")
M13, M15, BOX = m["M13"], m["M15"], m["BOX"]
DAY, SG = m["DAY"].ravel(), m["SG"].ravel()
et = json.load(open(O1 / "entradas_etiquetas.json", encoding="utf-8"))
assert len(et) == M13.shape[2] == 791, (len(et), M13.shape)


def familia(e: dict) -> str:
    f = e.get("familia", "?")
    return "chilena" if f.startswith("chil") or "variante" in f else f


fams = [familia(e) for e in et]
p("# B) Compuertas del .m sobre las 791 escenas de O1 (oráculo mirova_v750, devolver_diag=True)")
p(f"familias: {dict(Counter(fams))}")

C = defaultdict(Counter)
for k in range(M13.shape[2]):
    fam = fams[k]
    zi13, zi15, box = M13[:, :, k], M15[:, :, k], BOX[:, :, k]
    day, sg = float(DAY[k]), float(SG[k])
    c = C[fam]
    c["escenas"] += 1
    c["dayflag≠0"] += int(day != 0)
    c["sunglint<12 (rechazo paso 1)"] += int((not np.isfinite(sg)) or sg < 12)
    with np.errstate(invalid="ignore", divide="ignore"):
        bt15 = mv.radiance_to_temperature(zi15, 10.763)
    frios = int(np.count_nonzero(bt15 <= 200))
    c["escenas con píxel M15 ≤ 200 K (paso 3)"] += int(frios > 0)
    c["píxeles M15 ≤ 200 K (paso 3)"] += frios
    # paso 4: NaN del NTI tras el filtro frío
    zi15f = np.where(bt15 <= 200, np.nan, zi15)
    with np.errstate(invalid="ignore", divide="ignore"):
        nti = (zi13 - zi15f) / (zi13 + zi15f)
    nan_nti = int(np.count_nonzero(~np.isfinite(nti)))
    c["escena rechazada ≥ mitad NaN (paso 4)"] += int(nan_nti >= (nti.size // 2))
    # paso 6: alertas absolutas dentro de BOX (sin el marco)
    boxd = box.astype(float).copy()
    boxd[:, [0, -1]] = np.nan
    boxd[[0, -1], :] = np.nan
    k1 = -0.7 if day == 0 else -0.5
    nabs = int(np.count_nonzero(np.isfinite(boxd) & (nti > k1)))
    c["escenas con alerta absoluta NTI > K1 (paso 6)"] += int(nabs > 0)
    c["píxeles NTI > K1 (paso 6)"] += nabs
    alert, diag = mv.hotspot_detection(zi13, zi15, box, day, sg, devolver_diag=True)
    alert = np.asarray(alert).ravel()
    if diag.get("rechazo"):
        c[f"rechazo del oráculo: {diag['rechazo']}"] += 1
    c["escenas con alerta"] += int(alert.size > 0)
    c["escenas con índices repetidos (unique≠raw)"] += int(len(np.unique(alert)) != alert.size)
    p1 = diag.get("pase1") or {}
    p2 = diag.get("pase2") or {}
    c["pase 2 sin regresión (<3 puntos)"] += int(alert.size > 0 and not p2)
    if p1:
        c["pase1: umbral dNTI fuera = piso 0,02"] += int(abs(p1["thr_dnti_box0_roi1"] - 0.02) < 1e-12)
        c["pase1: umbral dNTI cumbre = piso 0,003"] += int(abs(p1["thr_dnti_roi2"] - 0.003) < 1e-12)
        c["pase1: umbral dETI fuera = piso 0,01"] += int(abs(p1["thr_deti_box0_roi1"] - 0.01) < 1e-12)
        c["pase1: umbral dETI cumbre = piso 0,003"] += int(abs(p1["thr_deti_roi2"] - 0.003) < 1e-12)
        c["pase1 con estadísticos"] += 1

# control positivo de B: Etna
ke = next(i for i, e in enumerate(et) if e["familia"] == "etna")
al_e = np.asarray(mv.hotspot_detection(M13[:, :, ke], M15[:, :, ke], BOX[:, :, ke], DAY[ke], SG[ke])).ravel()
lhot = float(np.nansum(M13[:, :, ke].ravel(order="F")[al_e]))
p(f"control positivo Etna: {al_e.size} alertas, Tot_Lmir_hot {lhot:.9f} (OSF: 5 y 1,965342180)")
assert al_e.size == 5 and abs(lhot - 1.965342180) < 1e-6, "instrumento muerto: Etna no reproduce el OSF"

claves = sorted({k for c in C.values() for k in c})
p()
p("| compuerta | " + " | ".join(sorted(C)) + " |")
p("|---|" + "---|" * len(C))
for k in claves:
    p(f"| {k} | " + " | ".join(str(C[f].get(k, 0)) for f in sorted(C)) + " |")
p()
p("Lectura: sólo las compuertas que disparan en la familia «chilena» tienen sustrato en Chile dentro de esta batería;")
p("las que disparan sólo en «sintetica» prueban que el instrumento las ve (control positivo) pero no que ocurran aquí.")

SALIDA.write_text("\n".join(lineas) + "\n", encoding="utf-8")
print(f"\nescrito {SALIDA}")
