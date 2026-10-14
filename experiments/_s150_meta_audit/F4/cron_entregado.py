"""F4 (meta-auditoria S150): corridas del NRT que GitHub entrega por dia, contra las 12 que declara el cron.

Afirmacion bajo prueba: CLAUDE.md l. 570 (A45) "NRT cron corre 12 veces/dia"; l. 607, 1546, 1687 "cron cada 2h".
Preguntas del instrumento:
1. Si el cron entregara menos de 12 por dia, se veria: cuento corridas con event == schedule por dia UTC.
2. Si el instrumento estuviera muerto (gh sin sesion, workflow mal nombrado) la lista saldria vacia y el
   script lo dice; el control positivo es que existan corridas workflow_dispatch contadas aparte.
Ventana: 2026-09-10 a 2026-10-02 (antes del apagon del token del 2026-10-03, que no cambia el cron porque
las corridas fallidas tambien se cuentan). Denominador: dias con al menos una corrida en la ventana.
Uso: python cron_entregado.py   (necesita gh autenticado; solo lectura)
"""
import collections, json, subprocess, sys

out = subprocess.run(["gh", "run", "list", "--repo", "MendozaVolcanic/VRP-chile", "--workflow", "nrt.yml",
                      "-L", "400", "--json", "createdAt,event"], capture_output=True, text=True).stdout
runs = json.loads(out or "[]")
if not runs:
    sys.exit("SIN DATO: gh no devolvio corridas")
ev = collections.Counter(r["event"] for r in runs)
por_dia = collections.Counter(r["createdAt"][:10] for r in runs if r["event"] == "schedule")
dias = [d for d in sorted(por_dia) if "2026-09-10" <= d <= "2026-10-02"]
n = sum(por_dia[d] for d in dias)
print("eventos en la muestra:", dict(ev), "| rango", min(por_dia), "a", max(por_dia))
print(f"ventana 2026-09-10..2026-10-02: {len(dias)} dias, {n} corridas schedule, {n/len(dias):.2f} por dia (declarado: 12)")
