"""S139: la franja que falta, ¿coincide con una corrida anterior todavia viva?

Hipotesis H-SOLAPE: GitHub descarta el evento `schedule` cuando ya hay una corrida
del MISMO workflow sin terminar (en cola o en curso). Si fuera cierta, cada franja
faltante caeria dentro del intervalo [createdAt, updatedAt] de la corrida previa.

Hipotesis H-CAP: hay un limite de tasa por workflow (~6/dia) independiente de si
la corrida previa termino. Si fuera cierta, habria franjas faltantes con TODAS las
corridas previas ya terminadas.

Las dos son distinguibles con este dato y la medicion las separa.

PREGUNTAS DEL INSTRUMENTO
 1. Si H-SOLAPE fuera cierta al 100%, la medicion lo veria: "faltantes con el
    workflow ocioso" daria 0. Si H-SOLAPE fuera falsa del todo, daria el total.
 2. Si el instrumento estuviera muerto (mal parseo de fechas), el tramo ANTES
    daria basura: ANTES es control positivo, ahi casi no faltan franjas y las
    duraciones deben ser < 2 h.

Duracion usada: createdAt -> updatedAt (incluye la espera en cola, que es
justamente lo que interesa para el grupo de concurrencia push-main).
Ventana y denominador declarados en la salida.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).parent
CORTE = datetime(2026, 8, 27, tzinfo=timezone.utc)
FIN = datetime(2026, 9, 14, tzinfo=timezone.utc)
INICIO = datetime(2026, 8, 1, tzinfo=timezone.utc)

# workflow -> (minuto declarado, horas en las que dispara)
CRON = {
    "nrt": (0, list(range(0, 24, 2))),
    "sync-mirova-csv": (12, list(range(24))),
    "pages-deploy": (50, list(range(0, 24, 2))),
    "nrt-retry": (30, list(range(1, 24, 2))),
    "reproc-watchdog": (20, list(range(24))),
    "nrt-healthcheck": (0, [12]),
}
TOL = timedelta(minutes=75)   # una corrida cuenta como "de esta franja" si se creo
                              # dentro de +-75 min del minuto declarado


def carga(w):
    p = AQUI / f"runs_{w}.json"
    out = []
    for r in json.loads(p.read_text(encoding="utf-8")):
        if r["event"] != "schedule":
            continue
        c = datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00"))
        u = datetime.fromisoformat(r["updatedAt"].replace("Z", "+00:00"))
        out.append((c, u, r["conclusion"], r["databaseId"]))
    return sorted(out)


def franjas(w, d0, d1):
    minuto, horas = CRON[w]
    t = d0
    out = []
    while t < d1:
        for h in horas:
            s = t.replace(hour=h, minute=minuto)
            if d0 <= s < d1:
                out.append(s)
        t += timedelta(days=1)
    return sorted(out)


def main():
    for w in CRON:
        runs = carga(w)
        if not runs:
            print(f"{w}: SIN DATO")
            continue
        cobertura0 = runs[0][0]
        print("=" * 78)
        print(f"{w}   (API cubre desde {cobertura0.isoformat()})")
        for etiqueta, d0, d1 in (("ANTES", max(INICIO, cobertura0 + timedelta(hours=6)), CORTE),
                                 ("DESDE", CORTE, FIN)):
            if d1 <= d0:
                print(f"  {etiqueta}: SIN DATO (la API no cubre el tramo)")
                continue
            sl = franjas(w, d0, d1)
            if not sl:
                print(f"  {etiqueta}: SIN DATO (0 franjas)")
                continue
            entregadas, faltan = 0, []
            for s in sl:
                if any(abs((c - s).total_seconds()) <= TOL.total_seconds() for c, _, _, _ in runs):
                    entregadas += 1
                else:
                    faltan.append(s)
            # de las que faltan, cuantas caen con el workflow OCIOSO
            ocioso = 0
            for s in faltan:
                viva = any(c <= s <= u for c, u, _, _ in runs)
                if not viva:
                    ocioso += 1
            dur = sorted((u - c).total_seconds() / 60 for c, u, _, _ in runs
                         if d0 <= c < d1)
            dtxt = (f"dur createdAt->updatedAt  mediana={dur[len(dur)//2]:.0f}  "
                    f"p95={dur[int(.95*(len(dur)-1))]:.0f}  max={dur[-1]:.0f} min") if dur else "SIN DATO"
            print(f"  {etiqueta} [{d0.date()}..{d1.date()}): franjas declaradas={len(sl)}  "
                  f"entregadas={entregadas} ({100*entregadas/len(sl):.0f}%)  faltan={len(faltan)}")
            print(f"      de las faltantes, con el workflow OCIOSO (nada en curso): "
                  f"{ocioso}/{len(faltan)}" + (f" = {100*ocioso/len(faltan):.0f}%" if faltan else ""))
            print(f"      {dtxt}")
        print()


if __name__ == "__main__":
    main()
