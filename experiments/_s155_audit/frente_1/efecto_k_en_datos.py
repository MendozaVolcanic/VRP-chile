"""Control de efecto (A116): produccion corre K de verdad, no solo en el YAML.
Mide en data/mirova_equivalent/*.json la fraccion de records con triggered_test1=True segun processed_utc
antes o despues del merge de #850 (2026-10-18T09:57:30Z).
P1: si K no estuviera corriendo, los records procesados despues del merge seguirian con triggered_test1=True
    en una fraccion parecida a la de antes.
P2: control positivo: la fraccion ANTES del merge debe ser > 0 (el campo existe y el Test 1 disparaba con C0);
    si diera 0 antes y despues, el instrumento no distingue (SIN DATO).
Ventana antes: records procesados antes del merge, toda la historia; despues: merge..fin del corpus del worktree cb90031a."""
import json, glob, sys
CUT = "2026-10-18T09:57:30"
a = [0, 0]; b = [0, 0]; src_after = {}
for f in sorted(glob.glob("data/mirova_equivalent/*.json")):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception as e:
        print("ERROR", f, e); continue
    for r in (d.get("records", []) if isinstance(d, dict) else d):
        p = str(r.get("processed_utc") or "")
        if not p: continue
        t1 = r.get("triggered_test1") is True
        if p < CUT:
            a[0] += 1; a[1] += t1
        elif p >= CUT:
            b[0] += 1; b[1] += t1
            s = r.get("final_hotspot_source"); src_after[s] = src_after.get(s, 0) + 1
print(f"antes  (procesados antes del merge, toda la historia): {a[1]} de {a[0]} con triggered_test1")
print(f"despues (procesados >= merge)         : {b[1]} de {b[0]} con triggered_test1")
print("final_hotspot_source despues del merge:", src_after)
sys.exit(0 if a[0] and b[0] else 2)
