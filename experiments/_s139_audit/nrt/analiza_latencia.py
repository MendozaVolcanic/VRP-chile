"""S139: descomposicion de la latencia pasada -> publicacion.

LIMITE DEL INSTRUMENTO, declarado antes del numero: `processed_utc` lo escribe
pipeline/store.py:491 y entro al repo con el commit d3b55ac4c (S132, 2026-09-02).
Por lo tanto NO existe comparacion antes/despues del 2026-08-27: para el tramo
ANTES el dato es SIN DATO, no cero.

PREGUNTAS DEL INSTRUMENTO
 1. Si la latencia fuera enorme (dias), la medicion lo veria: es una resta de dos
    marcas de tiempo absolutas, sin tope.
 2. Si el instrumento estuviera muerto (campo ausente), n=0 y se imprime SIN DATO.
 Control positivo: la latencia debe ser estrictamente positiva y mayor que la
 latencia conocida de publicacion de LANCE NRT (~3 h). Si diera ~0 estaria rota.

Ventana: records con datetime_utc >= 2026-09-02 (desde que existe el campo).
Denominador declarado en cada fila.
"""
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
DATA = RAIZ / "data" / "mirova_equivalent"
DESDE = "2026-09-02"
HASTA = "2026-09-14"


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


def q(xs, f):
    xs = sorted(xs)
    return xs[int(f * (len(xs) - 1))] if xs else float("nan")


def main():
    lat_sensor = defaultdict(list)
    lat_hora = defaultdict(list)
    todas = []
    sin_campo = 0
    for f in sorted(DATA.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for r in d.get("records", []):
            dt = r.get("datetime_utc", "")
            if not (DESDE <= dt[:10] < HASTA):
                continue
            a, b = pdt(dt), pdt(r.get("processed_utc"))
            if not b:
                sin_campo += 1
                continue
            h = (b - a).total_seconds() / 3600
            todas.append(h)
            lat_sensor[r.get("sensor", "?")].append(h)
            lat_hora[int(dt[11:13])].append(h)
    if not todas:
        print("SIN DATO")
        return
    print(f"ventana: {DESDE} .. {HASTA}   records con processed_utc: {len(todas)}"
          f"   sin el campo (anteriores a S132): {sin_campo}")
    print(f"GLOBAL  mediana={q(todas,.5):.2f} h   p75={q(todas,.75):.2f}   "
          f"p90={q(todas,.9):.2f}   p99={q(todas,.99):.2f}   max={max(todas):.2f} h")
    print(f"        fraccion > 24 h: {100*sum(1 for x in todas if x>24)/len(todas):.1f}%"
          f"   > 48 h: {100*sum(1 for x in todas if x>48)/len(todas):.1f}%")
    print()
    print(f"{'sensor':22s} {'n':>5s} {'mediana':>8s} {'p90':>7s} {'max':>7s}")
    for s in sorted(lat_sensor):
        v = lat_sensor[s]
        print(f"{s:22s} {len(v):5d} {q(v,.5):8.2f} {q(v,.9):7.2f} {max(v):7.2f}")
    print()
    print("latencia por hora UTC de la pasada (una pasada nocturna tarde espera")
    print("a la siguiente corrida del cron; el patron dice cuanto pesa eso)")
    print(f"{'hora':>5s} {'n':>5s} {'mediana':>8s} {'p90':>7s}")
    for h in sorted(lat_hora):
        v = lat_hora[h]
        print(f"{h:5d} {len(v):5d} {q(v,.5):8.2f} {q(v,.9):7.2f}")


if __name__ == "__main__":
    main()
