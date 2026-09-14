"""S139: el retraso REAL de cada corrida schedule respecto de su franja de cron.

Esta es la medicion que corrige el error del script de franjas (que plegaba el
retraso modulo 60 min y por eso no podia ver retrasos de horas).

Metodo: para cada corrida entregada se busca la franja declarada por el cron mas
cercana HACIA ATRAS (una corrida nunca se adelanta a su franja) dentro de 24 h.

PREGUNTAS DEL INSTRUMENTO
 1. Si no hubiera retraso (entrega sana), la medicion lo veria: mediana ~0-5 min.
    El tramo ANTES es el control positivo y debe dar justo eso.
 2. Si el instrumento estuviera muerto (mal parseo, mal calculo de franjas), el
    control positivo ANTES daria un retraso grande tambien. Un cero global seria
    sospechoso, no OK.

Ventana y denominador declarados en la salida.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).parent
CORTE = datetime(2026, 8, 27, tzinfo=timezone.utc)
FIN = datetime(2026, 9, 14, tzinfo=timezone.utc)

CRON = {
    "nrt": (0, list(range(0, 24, 2))),
    "sync-mirova-csv": (12, list(range(24))),
    "pages-deploy": (50, list(range(0, 24, 2))),
    "nrt-retry": (30, list(range(1, 24, 2))),
    "reproc-watchdog": (20, list(range(24))),
    "nrt-healthcheck": (0, [12]),
}


def franja_previa(t, minuto, horas):
    """La franja declarada mas reciente que sea <= t."""
    for dd in (0, 1):
        dia = (t - timedelta(days=dd)).date()
        cands = [datetime(dia.year, dia.month, dia.day, h, minuto, tzinfo=timezone.utc)
                 for h in horas]
        cands = [c for c in cands if c <= t]
        if cands:
            return max(cands)
    return None


def main():
    print(f"{'workflow':20s} {'tramo':6s} {'n':>4s} {'p05':>6s} {'mediana':>8s} {'p95':>7s} {'max':>7s}   (retraso en min)")
    for w, (minuto, horas) in CRON.items():
        runs = [datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00"))
                for r in json.loads((AQUI / f"runs_{w}.json").read_text(encoding="utf-8"))
                if r["event"] == "schedule"]
        for etiqueta, d0, d1 in (("ANTES", datetime(2026, 8, 1, tzinfo=timezone.utc), CORTE),
                                 ("DESDE", CORTE, FIN)):
            ds = []
            for t in runs:
                if not (d0 <= t < d1):
                    continue
                s = franja_previa(t, minuto, horas)
                if s is None:
                    continue
                ds.append((t - s).total_seconds() / 60)
            if not ds:
                print(f"{w:20s} {etiqueta:6s} SIN DATO")
                continue
            ds.sort()
            q = lambda f: ds[int(f * (len(ds) - 1))]
            print(f"{w:20s} {etiqueta:6s} {len(ds):4d} {q(.05):6.0f} {q(.5):8.0f} {q(.95):7.0f} {ds[-1]:7.0f}")


if __name__ == "__main__":
    main()
