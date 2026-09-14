"""S139: QUE franjas horarias sobreviven, y si el repo tiene un techo global.

PREGUNTAS DEL INSTRUMENTO
 1. Si la entrega de eventos schedule fuera aleatoria por evento, esta medicion lo
    veria: una caida aleatoria reparte uniforme sobre las 24 franjas y sobre los
    workflows. Una caida estructurada concentra. Se imprimen ambas vistas.
 2. Si el instrumento estuviera muerto, el conteo total por dia daria 0 y se
    imprime explicito; un dia sin corridas se distingue de un dia sin datos por el
    rango de la ventana, que se declara.
 Control positivo: nrt-healthcheck (1 corrida/dia) tiene 100% de entrega en la
 misma ventana. Si la medicion no lo viera al 100%, estaria rota.

Ventana y denominador declarados en cada salida.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).parent
WF = ["nrt", "sync-mirova-csv", "pages-deploy", "nrt-retry",
      "reproc-watchdog", "nrt-healthcheck"]
CORTE = "2026-08-27"
FIN = "2026-09-14"  # dia en curso, se excluye


def main():
    datos = {}
    for w in WF:
        p = AQUI / f"runs_{w}.json"
        datos[w] = [r for r in json.loads(p.read_text(encoding="utf-8"))
                    if r["event"] == "schedule"]

    print("=" * 78)
    print("A) Franja horaria de las corridas ENTREGADAS del NRT (cron 0 */2)")
    print("   ventana: desde", CORTE, "hasta", FIN, "(exclusivo)")
    print("=" * 78)
    for etiqueta, filtro in (("ANTES", lambda d: d < CORTE),
                             ("DESDE", lambda d: CORTE <= d < FIN)):
        horas = Counter()
        dias = set()
        for r in datos["nrt"]:
            d = r["createdAt"][:10]
            if not filtro(d):
                continue
            dias.add(d)
            horas[int(r["createdAt"][11:13])] += 1
        n = len(dias)
        if n == 0:
            print(f"{etiqueta}: SIN DATO")
            continue
        print(f"{etiqueta} (n={n} dias, denominador {n} corridas posibles por franja):")
        linea = []
        for h in range(0, 24, 2):
            linea.append(f"{h:02d}h:{horas.get(h,0):3d}/{n}")
        print("   " + "  ".join(linea))
        fuera = {h: c for h, c in horas.items() if h % 2 == 1}
        if fuera:
            print(f"   corridas en franja impar (no declarada por el cron): {fuera}")

    print()
    print("=" * 78)
    print("B) Minuto de creacion real vs minuto declarado del cron (retraso)")
    print("=" * 78)
    declarado = {"nrt": 0, "sync-mirova-csv": 12, "pages-deploy": 50,
                 "nrt-retry": 30, "reproc-watchdog": 20, "nrt-healthcheck": 0}
    for w in WF:
        for etiqueta, filtro in (("ANTES", lambda d: d < CORTE),
                                 ("DESDE", lambda d: CORTE <= d < FIN)):
            atrasos = []
            for r in datos[w]:
                d = r["createdAt"][:10]
                if not filtro(d):
                    continue
                m = int(r["createdAt"][11:13]) * 60 + int(r["createdAt"][14:16])
                dm = (m - declarado[w]) % 60
                atrasos.append(dm if dm < 30 else dm - 60)
            if not atrasos:
                print(f"{w:20s} {etiqueta}: SIN DATO")
                continue
            atrasos.sort()
            med = atrasos[len(atrasos) // 2]
            print(f"{w:20s} {etiqueta}: n={len(atrasos):4d}  atraso min/mediana/max = "
                  f"{atrasos[0]:+d}/{med:+d}/{atrasos[-1]:+d} min")

    print()
    print("=" * 78)
    print("C) Techo global del repo: corridas schedule ENTREGADAS por dia, todas juntas")
    print("=" * 78)
    por_dia = defaultdict(Counter)
    for w in WF:
        for r in datos[w]:
            por_dia[r["createdAt"][:10]][w] += 1
    dias = sorted(d for d in por_dia if d < FIN)
    print(f"{'dia':12s} {'total':>6s}  " + "  ".join(f"{w[:9]:>9s}" for w in WF))
    for d in dias[-28:]:
        c = por_dia[d]
        print(f"{d:12s} {sum(c.values()):6d}  " + "  ".join(f"{c.get(w,0):9d}" for w in WF))

    print()
    print("=" * 78)
    print("D) Espaciado entre corridas schedule CONSECUTIVAS del repo (cualquier workflow)")
    print("   Si hubiera un limite de tasa por repo, el espaciado tendria un piso.")
    print("=" * 78)
    from datetime import datetime
    for etiqueta, filtro in (("ANTES", lambda d: d < CORTE),
                             ("DESDE", lambda d: CORTE <= d < FIN)):
        ts = sorted(datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00"))
                    for w in WF for r in datos[w] if filtro(r["createdAt"][:10]))
        if len(ts) < 3:
            print(f"{etiqueta}: SIN DATO")
            continue
        gaps = sorted((ts[i + 1] - ts[i]).total_seconds() / 60 for i in range(len(ts) - 1))
        q = lambda f: gaps[int(f * (len(gaps) - 1))]
        print(f"{etiqueta}: n={len(gaps)} intervalos  min={gaps[0]:.1f}  p10={q(.1):.1f}  "
              f"mediana={q(.5):.1f}  p90={q(.9):.1f}  max={gaps[-1]:.1f} min")


if __name__ == "__main__":
    main()
