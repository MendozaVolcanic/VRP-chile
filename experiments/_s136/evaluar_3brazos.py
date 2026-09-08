"""S136 - aplica el criterio PRE-REGISTRADO al resultado del probe de 3 brazos.

El criterio esta en `docs/PREREGISTRO_PROBE_S136_TEST1_CONTEXTUAL.md` y se fijo antes de correr.
Este script no lo reinterpreta: lo ejecuta.

ORDEN DELIBERADO. Primero el CONTROL DE VALIDEZ (si el brazo ACTUAL no reproduce la produccion,
ningun otro numero es interpretable) y la PARIDAD DE COBERTURA entre brazos (leccion de S135: un
brazo con menos pasadas produce "perdidas" que son dias que nunca miro). Recien despues, los
ratios. Todo numero con su n (A90).

Uso: python experiments/_s136/evaluar_3brazos.py [--dir <carpeta con resultado_3brazos.json>]
"""
import argparse
import io
import json
import statistics as st
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]

BRAZOS = ("ACTUAL", "SIN_KEEP", "SIN_FILTRO")
BANDA = (0.5, 2.0)          # banda de paridad del proyecto
FACTOR = 1.5                # cuanto puede alejarse SIN_FILTRO de ACTUAL sin ser "peor"
MIN_NEVADOS = 4             # bajo esto, el desenlace es C (indeterminado)
TOL_REPRO = 0.10            # el brazo ACTUAL debe reproducir la produccion dentro del 10 %


def ts(s):
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
    s = (s or "").strip()
    if not s:
        return None
    if s.isdigit():
        return datetime.fromtimestamp(int(s), tz=timezone.utc)
    try:
        t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def magnitud_persistida(volcan, pasada_utc):
    """La magnitud que hoy tiene el JSON operacional para esa pasada (control de validez)."""
    p = RAIZ / "data" / "mirova_equivalent" / "{}.json".format(volcan)
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) else d
    objetivo = ts(pasada_utc)
    mejor, dmin = None, timedelta(minutes=20)
    for r in recs:
        t = ts(r.get("datetime_utc") or r.get("timestamp"))
        if t is None:
            continue
        if abs(t - objetivo) <= dmin:
            dmin = abs(t - objetivo)
            mejor = r
    if mejor is None:
        return None
    v = mejor.get("f5_core_vrp_mw")
    if v is None:
        v = (mejor.get("primary_cluster") or {}).get("vrp_mw")
    return v


def mag(fila, brazo):
    b = (fila.get("brazos") or {}).get(brazo) or {}
    return b.get("magnitud_publicada_mw")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(Path(__file__).parent / "out"))
    args = ap.parse_args()
    ruta = Path(args.dir)
    if ruta.is_dir():
        ruta = ruta / "resultado_3brazos.json"
    filas = json.loads(ruta.read_text(encoding="utf-8"))

    print("=" * 100)
    print("CONTROL DE VALIDEZ - ¿el brazo ACTUAL reproduce la produccion persistida?")
    print("Si no reproduce, ningun otro numero de este run es interpretable.")
    print("=" * 100)
    repro_ok, repro_no, sin_ref = 0, [], 0
    for f in filas:
        m = mag(f, "ACTUAL")
        p = magnitud_persistida(f["volcan"], f["pasada_utc"])
        if m is None or p is None:
            sin_ref += 1
            continue
        if p == 0:
            (repro_ok := repro_ok + 1) if m == 0 else repro_no.append((f, m, p))
            continue
        if abs(m - p) / p <= TOL_REPRO:
            repro_ok += 1
        else:
            repro_no.append((f, m, p))
    total_comp = repro_ok + len(repro_no)
    print("reproducen: {}/{}   sin referencia persistida: {}".format(
        repro_ok, total_comp, sin_ref))
    for f, m, p in repro_no:
        print("  NO reproduce  {:22s} {}  probe={:.4f}  persistido={:.4f}".format(
            f["volcan"], f["pasada_utc"], m, p))
    if total_comp and repro_ok / total_comp < 0.8:
        print("\n>>> El probe NO reproduce la produccion en la mayoria de las pasadas.")
        print(">>> Eso es el hallazgo; los ratios de abajo NO sostienen ningun veredicto.")

    print()
    print("=" * 100)
    print("PARIDAD DE COBERTURA entre brazos (leccion S135)")
    print("=" * 100)
    utiles = []
    for f in filas:
        faltan = [b for b in BRAZOS if mag(f, b) is None]
        if faltan:
            print("  descartada {:22s} {}  sin resultado en: {}".format(
                f["volcan"], f["pasada_utc"], ", ".join(faltan)))
        else:
            utiles.append(f)
    print("pasadas con los 3 brazos: {}/{}".format(len(utiles), len(filas)))

    print()
    print("=" * 100)
    print("RATIOS nuestro/MIROVA por brazo y clase (pareado sobre las mismas pasadas)")
    print("=" * 100)
    resumen = {}
    for clase in ("nevado", "control"):
        sub = [f for f in utiles if f["clase"] == clase]
        if not sub:
            print("{:8s} sin pasadas".format(clase))
            continue
        print("{:8s} n={}".format(clase, len(sub)))
        for b in BRAZOS:
            ratios = [mag(f, b) / f["mirova_vrp_mw"] for f in sub if f.get("mirova_vrp_mw")]
            if not ratios:
                continue
            resumen[(clase, b)] = st.median(ratios)
            s = sorted(ratios)
            print("   {:11s} mediana={:6.2f}  min={:6.2f}  max={:6.2f}".format(
                b, st.median(s), s[0], s[-1]))
        print()

    print("=" * 100)
    print("DESENLACE segun el criterio pre-registrado")
    print("=" * 100)
    n_nev = sum(1 for f in utiles if f["clase"] == "nevado")
    r_sin = resumen.get(("nevado", "SIN_FILTRO"))
    r_act = resumen.get(("nevado", "ACTUAL"))
    if n_nev < MIN_NEVADOS or r_sin is None or r_act is None:
        print("C - INDETERMINADO: {} pasadas utiles en nevados (minimo {})".format(
            n_nev, MIN_NEVADOS))
        return
    # el control tambien se movio tanto como los nevados => efecto universal, no del glaciar
    c_sin, c_act = resumen.get(("control", "SIN_FILTRO")), resumen.get(("control", "ACTUAL"))
    if c_sin and c_act and r_act:
        mov_nev = r_sin / r_act
        mov_ctl = c_sin / c_act
        print("movimiento SIN_FILTRO/ACTUAL:  nevados x{:.2f}   control x{:.2f}".format(
            mov_nev, mov_ctl))
        if mov_ctl > 1.2 and abs(mov_nev - mov_ctl) / mov_nev < 0.25:
            print("C - INDETERMINADO: el control se mueve como los nevados "
                  "(efecto universal, no del glaciar)")
            return
    en_banda = BANDA[0] <= r_sin <= BANDA[1]
    cerca = r_sin <= r_act * FACTOR
    print("R_sin={:.2f}  R_act={:.2f}  en banda {}  dentro de x{} de ACTUAL: {}".format(
        r_sin, r_act, en_banda, FACTOR, cerca))
    if en_banda and cerca:
        print("\nA - EL FILTRO QUEDO SIN FUNCION. Retirarlo es volver al literal (P1 del gate);")
        print("    corresponde proponer el A/B de adopcion con reproceso completo.")
    else:
        print("\nB - EL FILTRO SIGUE CURANDO. No se retira solo. El problema pasa a ser que")
        print("    mecanismo documentado falta (primer candidato: el maximo diario, Laiolo 2026).")


if __name__ == "__main__":
    main()
