"""S139: cobertura de datos y latencia, antes y despues del 2026-08-27.

Lo que se mide, por volcan y por sensor:
  - records/dia escritos en data/mirova_equivalent/<Volcan>.json
  - pasadas distintas por dia (datetime_utc unico) - un record por pasada
  - latencia = processed_utc - datetime_utc  (cuanto tarda una pasada del
    satelite en aparecer publicada)

PREGUNTAS DEL INSTRUMENTO
 1. Si se hubieran perdido pasadas, esta medicion lo veria: cuenta pasadas
    distintas por dia, no corridas del cron. Si un dia tuviera 0 pasadas de un
    sensor, aparece como 0 y se distingue de "el volcan no tiene ese sensor"
    porque la tabla lista los sensores presentes en cada tramo.
 2. Si el instrumento estuviera muerto (archivo vacio, parseo roto), el total de
    records se imprime y seria 0 => SIN DATO, no OK.
 Control positivo: la latencia del tramo ANTES debe ser netamente menor. Si
 saliera igual, la medicion no estaria viendo el fenomeno que dice medir.

Ventana: 2026-08-01 .. 2026-09-13 (el 14 esta en curso y se excluye).
Denominador: dias con al menos un record en el tramo, por volcan.
"""
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
DATA = RAIZ / "data" / "mirova_equivalent"
CORTE = "2026-08-27"
D0, D1 = "2026-08-01", "2026-09-14"


def pdt(s):
    if not s:
        return None
    s = s.strip().replace("Z", "+00:00")
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        try:
            d = datetime.strptime(s, "%Y-%m-%d %H:%M")
        except ValueError:
            return None
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d


def main():
    tot = 0
    por_tramo = {"ANTES": defaultdict(Counter), "DESDE": defaultdict(Counter)}
    lat = {"ANTES": defaultdict(list), "DESDE": defaultdict(list)}
    dias = {"ANTES": set(), "DESDE": set()}
    por_vol_dia = {"ANTES": defaultdict(lambda: defaultdict(set)),
                   "DESDE": defaultdict(lambda: defaultdict(set))}
    archivos = sorted(DATA.glob("*.json"))
    print(f"archivos leidos: {len(archivos)}  ({DATA})")
    for f in archivos:
        d = json.loads(f.read_text(encoding="utf-8"))
        vol = d.get("volcano", f.stem)
        for r in d.get("records", []):
            dt = r.get("datetime_utc")
            if not dt:
                continue
            dia = dt[:10]
            if not (D0 <= dia < D1):
                continue
            tot += 1
            tramo = "ANTES" if dia < CORTE else "DESDE"
            sensor = r.get("sensor", "?")
            por_tramo[tramo][vol][sensor] += 1
            dias[tramo].add(dia)
            por_vol_dia[tramo][vol][dia].add((sensor, dt))
            a, b = pdt(dt), pdt(r.get("processed_utc"))
            if a and b:
                lat[tramo][vol].append((b - a).total_seconds() / 3600)
    if tot == 0:
        print("SIN DATO: 0 records en la ventana")
        return
    print(f"records en ventana [{D0}..{D1}): {tot}\n")

    print("=" * 92)
    print("A) pasadas distintas por dia y por volcan (denominador: dias del tramo)")
    print("=" * 92)
    nA, nD = len(dias["ANTES"]), len(dias["DESDE"])
    print(f"   dias con dato: ANTES={nA}  DESDE={nD}")
    print(f"{'volcan':22s} {'ANTES/dia':>10s} {'DESDE/dia':>10s} {'delta %':>9s}")
    vols = sorted(set(por_tramo['ANTES']) | set(por_tramo['DESDE']))
    for v in vols:
        a = sum(len(s) for s in por_vol_dia["ANTES"][v].values()) / nA if nA else float("nan")
        b = sum(len(s) for s in por_vol_dia["DESDE"][v].values()) / nD if nD else float("nan")
        dl = 100 * (b - a) / a if a else float("nan")
        print(f"{v:22s} {a:10.2f} {b:10.2f} {dl:+8.1f}%")
    ta = sum(sum(len(s) for s in por_vol_dia["ANTES"][v].values()) for v in vols) / nA
    tb = sum(sum(len(s) for s in por_vol_dia["DESDE"][v].values()) for v in vols) / nD
    print(f"{'TOTAL':22s} {ta:10.2f} {tb:10.2f} {100*(tb-ta)/ta:+8.1f}%")

    print()
    print("=" * 92)
    print("B) dias SIN ningun record, por volcan (deteccion de agujeros)")
    print("=" * 92)
    import datetime as _dt
    def rango(d0, d1):
        a = _dt.date.fromisoformat(d0); b = _dt.date.fromisoformat(d1)
        while a < b:
            yield a.isoformat(); a += _dt.timedelta(days=1)
    for v in vols:
        hA = [d for d in rango(D0, CORTE) if d not in por_vol_dia["ANTES"][v]]
        hD = [d for d in rango(CORTE, "2026-09-13") if d not in por_vol_dia["DESDE"][v]]
        print(f"{v:22s} ANTES vacios={len(hA):2d}  DESDE vacios={len(hD):2d}"
              + (f"   -> {hD}" if hD else ""))

    print()
    print("=" * 92)
    print("C) latencia pasada -> publicacion (horas), por volcan")
    print("=" * 92)
    print(f"{'volcan':22s} {'n_A':>5s} {'medA':>7s} {'p90A':>7s} | {'n_D':>5s} {'medD':>7s} {'p90D':>7s}")
    def q(xs, f):
        xs = sorted(xs); return xs[int(f * (len(xs) - 1))] if xs else float("nan")
    todos = {"ANTES": [], "DESDE": []}
    for v in vols:
        A, B = lat["ANTES"][v], lat["DESDE"][v]
        todos["ANTES"] += A; todos["DESDE"] += B
        print(f"{v:22s} {len(A):5d} {q(A,.5):7.2f} {q(A,.9):7.2f} | {len(B):5d} {q(B,.5):7.2f} {q(B,.9):7.2f}")
    A, B = todos["ANTES"], todos["DESDE"]
    print(f"{'GLOBAL':22s} {len(A):5d} {q(A,.5):7.2f} {q(A,.9):7.2f} | {len(B):5d} {q(B,.5):7.2f} {q(B,.9):7.2f}")

    print()
    print("=" * 92)
    print("D) por sensor (records totales del tramo, normalizado a por-dia)")
    print("=" * 92)
    sA, sB = Counter(), Counter()
    for v in vols:
        sA.update(por_tramo["ANTES"][v]); sB.update(por_tramo["DESDE"][v])
    print(f"{'sensor':22s} {'ANTES/dia':>10s} {'DESDE/dia':>10s}")
    for s in sorted(set(sA) | set(sB)):
        print(f"{s:22s} {sA[s]/nA:10.2f} {sB[s]/nD:10.2f}")


if __name__ == "__main__":
    main()
