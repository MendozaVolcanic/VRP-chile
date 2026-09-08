"""S136 - verifica las dos correcciones que trajo la sesion paralela (VRP 136) al probe.

POR QUE. VRP 136 audito el probe y trajo dos correcciones. No se aceptan por venir de un par
(A48: un subagente o una sesion hermana puede inventar una heuristica razonable y equivocada);
se verifican con datos. Este script las verifica por una via INDEPENDIENTE de la suya: ella
comparo contra el brazo control del A/B de S135, este script compara el FONDO.

CORRECCION 1 - el control de validez estaba mal construido. Comparaba el probe (codigo de hoy)
contra `data/mirova_equivalent/`, escrito para junio-julio por el codigo de ENTONCES: regimen
previo a #535, con la mascara de nube encendida. No podia reproducir por construccion. Es el
razonamiento del propio pre-registro ("el regimen lo fija el codigo que procesa, no la fecha del
granule") aplicado al reves en el control.
   Verificacion independiente: si la causa es el regimen, las pasadas que REPRODUCEN deben tener
   el mismo fondo y las que NO, un fondo corrido. El fondo (t_bg_k) es el termometro del cambio
   que introdujo #535.

CORRECCION 2 - el desenlace se calculo sin verificar que hubiera sustrato. El filtro solo actua
si el hotspot final viene del camino Test 1 (process_viirs.py:1779, valor LEGACY), y las 20
pasadas se eligieron por `triggered_test1`, que es otra cosa: disparar no es ganar la seleccion.
   Verificacion: contar en cuantas pasadas ACTUAL y SIN_FILTRO difieren de verdad.

Uso: python experiments/_s136/verificar_control_y_sustrato.py
"""
import io
import json
import statistics as st
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
PROBE = Path(__file__).parent / "out" / "resultado_3brazos.json"
TOL_REPRO = 0.10
MIN_NEVADOS = 4  # el umbral del pre-registro para no caer en el desenlace C


def ts(s):
    s = (s or "").strip()
    if s.isdigit():
        return datetime.fromtimestamp(int(s), tz=timezone.utc)
    try:
        t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def persistido(volcan, pasada_utc, sensor):
    """El record del MISMO sensor y la MISMA pasada (3 min), no el mas cercano en el tiempo."""
    p = RAIZ / "data" / "mirova_equivalent" / "{}.json".format(volcan)
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) else d
    obj = datetime.strptime(pasada_utc, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    for r in recs:
        if r.get("sensor") != sensor:
            continue
        t = ts(r.get("datetime_utc") or r.get("timestamp"))
        if t and abs(t - obj) <= timedelta(minutes=3):
            return r
    return None


def mag(f, brazo):
    return ((f.get("brazos") or {}).get(brazo) or {}).get("magnitud_publicada_mw")


def main():
    filas = json.loads(PROBE.read_text(encoding="utf-8"))

    print("=" * 96)
    print("CORRECCION 1 - ¿la no-reproduccion se explica por el REGIMEN del comparador?")
    print("Si es asi, las que reproducen deben tener el mismo fondo y las que no, uno corrido.")
    print("=" * 96)
    rep, nore = [], []
    for f in filas:
        rec = ((f.get("brazos") or {}).get("ACTUAL") or {}).get("record") or {}
        m = mag(f, "ACTUAL")
        p = persistido(f["volcan"], f["pasada_utc"], f.get("sensor"))
        if p is None or m is None:
            continue
        pv = p.get("f5_core_vrp_mw")
        if pv is None:
            pv = (p.get("primary_cluster") or {}).get("vrp_mw")
        if pv is None:
            continue
        ok = (pv > 0 and abs(m - pv) / pv <= TOL_REPRO) or (pv == 0 and m == 0)
        if rec.get("t_bg_k") is None or p.get("t_bg_k") is None:
            continue
        (rep if ok else nore).append(abs(rec["t_bg_k"] - p["t_bg_k"]))

    if rep and nore:
        mr, mn = st.median(rep), st.median(nore)
        print("  reproducen      n={:2d}   |delta t_bg| mediana = {:.2f} K".format(len(rep), mr))
        print("  NO reproducen   n={:2d}   |delta t_bg| mediana = {:.2f} K".format(len(nore), mn))
        print()
        if mn > 3 * max(mr, 0.01):
            print("  >>> CONFIRMADA. El fondo separa los dos grupos por un factor {:.0f}.".format(
                mn / max(mr, 0.01)))
            print("  >>> La no-reproduccion es del COMPARADOR (regimen distinto), no del probe.")
        else:
            print("  >>> NO confirmada por esta via: el fondo no separa los dos grupos.")

    print()
    print("=" * 96)
    print("CORRECCION 2 - ¿cuantas pasadas tienen SUSTRATO (el filtro cambia algo)?")
    print("=" * 96)
    cambia = {"nevado": 0, "control": 0}
    total = {"nevado": 0, "control": 0}
    for f in filas:
        a, s = mag(f, "ACTUAL"), mag(f, "SIN_FILTRO")
        if a is None or s is None:
            continue
        total[f["clase"]] = total.get(f["clase"], 0) + 1
        if abs(a - s) > 1e-9:
            cambia[f["clase"]] = cambia.get(f["clase"], 0) + 1
    tot = sum(total.values())
    print("  la magnitud publicada cambia en {}/{} pasadas".format(sum(cambia.values()), tot))
    for clase in ("nevado", "control"):
        print("     {:8s} {}/{}".format(clase, cambia[clase], total[clase]))
    print()
    print("  El criterio pre-registrado cae en el desenlace C con menos de {} pasadas utiles"
          .format(MIN_NEVADOS))
    print("  en los nevados. Con sustrato hay {}.".format(cambia["nevado"]))
    if cambia["nevado"] < MIN_NEVADOS:
        print("  >>> CONFIRMADA. Leyendo 'util' como 'con sustrato', el desenlace es C, no A.")
        print("  >>> El pre-registro NO define 'util' operacionalmente: esa lectura hay que")
        print("  >>> ponersela a Nicolas por delante, no resolverla entre sesiones.")

    print()
    print("  Donde SI hay sustrato, la direccion del efecto:")
    for f in filas:
        a, s = mag(f, "ACTUAL"), mag(f, "SIN_FILTRO")
        if a is None or s is None or abs(a - s) <= 1e-9:
            continue
        print("     {:22s} {:17s} {:8s} {:.4f} -> {:.4f}  (x{:.2f})".format(
            f["volcan"], f["pasada_utc"], f["clase"], a, s, s / a if a else float("nan")))


if __name__ == "__main__":
    main()
