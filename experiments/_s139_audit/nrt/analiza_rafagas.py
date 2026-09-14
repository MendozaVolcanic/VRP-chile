"""S139: prueba decisiva del modelo "GitHub evalua los cron de este repo por PASADAS".

MODELO. Desde el 2026-08-27 GitHub no evalua los cron de este repo de forma
continua sino cada ~4 h. En cada pasada dispara UNA corrida de cada workflow que
tenga alguna franja vencida. Predicciones, todas falsables:
  P1  las corridas de workflows DISTINTOS llegan agrupadas en rafagas
  P2  dentro de una rafaga aparece a lo sumo 1 corrida por workflow
  P3  el numero de rafagas por dia ~ el numero de corridas/dia de cada workflow
  P4  ANTES del 27-ago no hay rafagas (cada cron llega por su cuenta)

PREGUNTAS DEL INSTRUMENTO
 1. Si NO hubiera rafagas (entrega sana o caida aleatoria), la medicion lo veria:
    el tramo ANTES es el control positivo y debe dar muchas rafagas de 1-2
    workflows y ninguna de 5.
 2. Si el instrumento estuviera muerto (agrupamiento mal hecho), ANTES y DESDE
    darian lo mismo. Que difieran es la evidencia de que mide algo.

Rafaga = corridas separadas por menos de VENTANA minutos entre consecutivas.
Ventana y denominador declarados en la salida.
"""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
WF = ["nrt", "sync-mirova-csv", "pages-deploy", "nrt-retry",
      "reproc-watchdog", "nrt-healthcheck"]
VENTANA = 20  # min
CORTE = datetime(2026, 8, 27, tzinfo=timezone.utc)
FIN = datetime(2026, 9, 14, tzinfo=timezone.utc)
INI = datetime(2026, 9, 1, tzinfo=timezone.utc)   # tramo DESDE: septiembre entero
INI_A = datetime(2026, 8, 13, tzinfo=timezone.utc)  # tramo ANTES: desde que la API cubre los 4


def eventos(d0, d1):
    out = []
    for w in WF:
        for r in json.loads((AQUI / f"runs_{w}.json").read_text(encoding="utf-8")):
            if r["event"] != "schedule":
                continue
            t = datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00"))
            if d0 <= t < d1:
                out.append((t, w))
    return sorted(out)


def rafagas(ev):
    grupos, actual = [], []
    for t, w in ev:
        if actual and (t - actual[-1][0]).total_seconds() / 60 > VENTANA:
            grupos.append(actual); actual = []
        actual.append((t, w))
    if actual:
        grupos.append(actual)
    return grupos


def main():
    for etiqueta, d0, d1 in (("ANTES", INI_A, CORTE), ("DESDE", INI, FIN)):
        ev = eventos(d0, d1)
        dias = (d1 - d0).days
        if not ev:
            print(f"{etiqueta}: SIN DATO")
            continue
        gs = rafagas(ev)
        tam = Counter(len(g) for g in gs)
        wf_unicos = Counter(len({w for _, w in g}) for g in gs)
        dup = sum(1 for g in gs if len(g) != len({w for _, w in g}))
        print("=" * 78)
        print(f"{etiqueta}  [{d0.date()} .. {d1.date()}) = {dias} dias, "
              f"{len(ev)} corridas schedule de {len(WF)} workflows")
        print(f"  rafagas (separacion > {VENTANA} min): {len(gs)}  "
              f"= {len(gs)/dias:.1f} por dia")
        print(f"  tamano de rafaga (n corridas): "
              + "  ".join(f"{k}:{v}" for k, v in sorted(tam.items())))
        print(f"  workflows DISTINTOS por rafaga: "
              + "  ".join(f"{k}:{v}" for k, v in sorted(wf_unicos.items())))
        print(f"  P2 rafagas con el MISMO workflow repetido: {dup}/{len(gs)}")
        grandes = sum(v for k, v in wf_unicos.items() if k >= 4)
        print(f"  rafagas con >=4 workflows distintos: {grandes}  "
              f"({100*grandes/len(gs):.0f}% de las rafagas)")
        print()


if __name__ == "__main__":
    main()
