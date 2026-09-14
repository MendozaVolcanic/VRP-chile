"""S139 auditoria NRT: cadencia real del cron contra la declarada.

PREGUNTAS DEL INSTRUMENTO
 1. Si la cadencia estuviera completamente rota (cero corridas), esta medicion lo
    veria: cuenta corridas creadas por evento `schedule` por dia y las compara con
    el numero que declara el cron. Un cero se distingue de "no medi" porque el
    rango de fechas cubierto por la API se imprime aparte.
 2. Si el instrumento estuviera muerto (API sin datos), el resultado se veria
    distinto: se imprime el total de corridas descargadas y su ventana. Cero
    corridas descargadas => SIN DATO, no OK.
 Control positivo: `event` distingue schedule de workflow_dispatch/push; los
 dispatch manuales aparecen y no se cuentan como cron. Y un dia con 12/12 (antes
 de agosto) demuestra que la medicion SI ve la cadencia completa cuando existe.

Denominador y ventana: se declaran en la salida, por dia y por workflow.
Solo lectura. No modifica nada del repo.
"""
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).parent

# corridas/dia que declara cada cron, derivado del yml (se verifica aparte)
ESPERADO = {
    "nrt": 12,               # 0 */2 * * *
    "sync-mirova-csv": 24,   # 12 * * * *
    "pages-deploy": 12,      # 50 */2 * * *
    "nrt-retry": 12,         # 30 1-23/2 * * *
    "reproc-watchdog": 24,   # 20 * * * *
    "nrt-healthcheck": 1,    # 0 12 * * *
}


def carga(nombre):
    p = AQUI / f"runs_{nombre}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    print("=" * 78)
    print("S139 / cadencia del cron - medicion sobre la API de GitHub")
    print("=" * 78)
    resumen = {}
    for nombre, esperado in ESPERADO.items():
        runs = carga(nombre)
        if runs is None:
            print(f"\n## {nombre}: SIN DATO (no se descargo el json)")
            continue
        if not runs:
            print(f"\n## {nombre}: SIN DATO (0 corridas devueltas por la API)")
            continue
        fechas = [r["createdAt"] for r in runs]
        print(f"\n## {nombre}  (esperado {esperado} corridas/dia por cron)")
        print(f"   corridas descargadas: {len(runs)}  ventana: {min(fechas)} .. {max(fechas)}")
        print(f"   eventos: {dict(Counter(r['event'] for r in runs))}")
        print(f"   conclusiones: {dict(Counter(r['conclusion'] for r in runs))}")

        por_dia = defaultdict(int)
        for r in runs:
            if r["event"] != "schedule":
                continue
            por_dia[r["createdAt"][:10]] += 1
        dias = sorted(por_dia)
        # descartar primer y ultimo dia (ventana parcial de la API / dia en curso)
        completos = dias[1:-1]
        if not completos:
            print("   SIN DATO: menos de 3 dias completos")
            continue
        corte = "2026-08-27"
        antes = [por_dia[d] for d in completos if d < corte]
        despues = [por_dia[d] for d in completos if d >= corte]
        def pct(v):
            return 100.0 * sum(v) / (esperado * len(v)) if v else float("nan")
        print(f"   ANTES  de {corte}: n={len(antes):3d} dias  media {sum(antes)/len(antes) if antes else float('nan'):.2f}/dia  = {pct(antes):.1f}%")
        print(f"   DESDE  {corte}: n={len(despues):3d} dias  media {sum(despues)/len(despues) if despues else float('nan'):.2f}/dia  = {pct(despues):.1f}%")
        resumen[nombre] = (pct(antes), pct(despues), len(antes), len(despues))
        print("   serie por dia: " + " ".join(f"{d[5:]}={por_dia[d]}" for d in completos))
    print("\n" + "=" * 78)
    print("RESUMEN (% de corridas por schedule entregadas frente al cron declarado)")
    print("=" * 78)
    print(f"{'workflow':22s} {'antes':>8s} {'desde 08-27':>12s}  dias(antes/desde)")
    for k, (a, b, na, nb) in resumen.items():
        print(f"{k:22s} {a:7.1f}% {b:11.1f}%  {na}/{nb}")


if __name__ == "__main__":
    sys.exit(main())
