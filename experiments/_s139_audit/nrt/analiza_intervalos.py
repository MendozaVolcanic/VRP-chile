"""S139: intervalo entre corridas schedule ENTREGADAS del MISMO workflow.

Hipotesis a distinguir:
  H-A  caida aleatoria por evento  -> los intervalos serian multiplos del cron
       repartidos geometricamente, con el multiplo 1 (el intervalo nominal) como
       el mas frecuente.
  H-B  limite de tasa por workflow -> hay un PISO: casi ningun intervalo por
       debajo de cierto valor, y el modo se corre a ese piso.

PREGUNTAS DEL INSTRUMENTO
 1. Si no hubiera piso alguno (entrega sana), la medicion lo veria: el histograma
    mostraria el intervalo nominal del cron como modo. El tramo ANTES sirve de
    control positivo exactamente para eso.
 2. Si el instrumento estuviera muerto, n=0 y se imprime SIN DATO.

Ventana y denominador declarados en la salida.
"""
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).parent
WF = {"nrt": 120, "sync-mirova-csv": 60, "pages-deploy": 120,
      "nrt-retry": 120, "reproc-watchdog": 60, "nrt-healthcheck": 1440}
CORTE = "2026-08-27"
FIN = "2026-09-14"


def serie(w, desde, hasta):
    p = AQUI / f"runs_{w}.json"
    ts = [datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00"))
          for r in json.loads(p.read_text(encoding="utf-8"))
          if r["event"] == "schedule" and desde <= r["createdAt"][:10] < hasta]
    return sorted(ts)


def main():
    for w, nominal in WF.items():
        print("=" * 78)
        print(f"{w}   (intervalo nominal del cron: {nominal} min)")
        for etiqueta, d0, d1 in (("ANTES", "2026-08-01", CORTE),
                                 ("DESDE", CORTE, FIN)):
            ts = serie(w, d0, d1)
            if len(ts) < 3:
                print(f"  {etiqueta} [{d0}..{d1}): SIN DATO (n={len(ts)})")
                continue
            gaps = [(ts[i + 1] - ts[i]).total_seconds() / 60 for i in range(len(ts) - 1)]
            # múltiplos del intervalo nominal
            mult = Counter(max(1, round(g / nominal)) for g in gaps)
            gs = sorted(gaps)
            q = lambda f: gs[int(f * (len(gs) - 1))]
            print(f"  {etiqueta} [{d0}..{d1}): n={len(gaps)} intervalos  "
                  f"min={gs[0]:.0f}  p05={q(.05):.0f}  mediana={q(.5):.0f}  p95={q(.95):.0f} min")
            print(f"      multiplos del nominal: "
                  + "  ".join(f"x{k}:{v}" for k, v in sorted(mult.items())[:10]))
        print()


if __name__ == "__main__":
    main()
