"""D3/D4: re-cuenta desde experiments/_s150_debiles/filas.json (1.143 alertas que B publica, abril a ago-27).
Etiqueta 'tabla' = alguna fila de la referencia con source CONS y tipo ALERTA_TERMICA. Camino D22 = B sin pixeles del
primer pase (diag_n_first_pass_pixels == 0). No reprocesa nada: depende de que filas.json sea fiel a los runs."""
import json, collections
R = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/experiments/_s150_debiles/filas.json"
d = json.load(open(R, encoding="utf-8"))
def tabla(r): return any(m.get("source") == "CONS" and "ALERTA" in str(m.get("tipo")) for m in r["mirova"])
def vrp(r): return max([m.get("vrp_mw") or 0 for m in r["mirova"]] or [0])
def sat(r): return (r.get("B") or {}).get("sensor", "?")
print("total", len(d), "perdidas", sum(r["perdida"] for r in d))
print("fuentes:", collections.Counter(m.get("source") for r in d for m in r["mirova"]))
for b in ("VIIRS375", "VIIRS_750", "VIIRS750", "MODIS"):
    p = [r for r in d if r["perdida"] and r["b"] == b]
    if not p: continue
    t = [r for r in p if tabla(r)]
    d22 = [r for r in t if (r.get("B") or {}).get("diag_n_first_pass_pixels") == 0]
    d22all = [r for r in p if (r.get("B") or {}).get("diag_n_first_pass_pixels") == 0]
    print(b, "perdidas", len(p), "con tabla", len(t), "D22 en tabla", len(d22), "D22 en todas", len(d22all))
    print("  D22 todas por etiqueta:", collections.Counter("tabla" if tabla(r) else "ocr" for r in d22all))
    print("  tabla por satelite:", collections.Counter(sat(r) for r in t))
    print("  D22 tabla vrp<0.10:", sum(vrp(r) < 0.10 for r in d22), " tabla vrp<0.10:", sum(vrp(r) < 0.10 for r in t))
# D4
for corte in (0.5, 0.2):
    allp = [r for r in d if vrp(r) >= corte]
    tab = [r for r in allp if tabla(r)]
    print(f"VRP>={corte}: alertas B {len(allp)} perdidas {sum(r['perdida'] for r in allp)}; con tabla {len(tab)} perdidas {sum(r['perdida'] for r in tab)}")
    for r in allp:
        if r["perdida"]:
            print("   ", r["clave"], vrp(r), "tabla" if tabla(r) else "solo-OCR", sat(r), r.get("solo_ocr"))
# vrp segun solo la fila CONS
def vrp_cons(r): return max([m.get("vrp_mw") or 0 for m in r["mirova"] if m.get("source") == "CONS" and "ALERTA" in str(m.get("tipo"))] or [0])
tab05 = [r for r in d if tabla(r) and vrp_cons(r) >= 0.5]
print("tabla con VRP_CONS>=0.5:", len(tab05), "perdidas", sum(r["perdida"] for r in tab05))
print("solo_ocr flag vs tabla():", collections.Counter((r.get("solo_ocr"), tabla(r)) for r in d))
print("--- D4 por banda ---")
for b in ("VIIRS375", "VIIRS750"):
    for corte in (0.5, 0.2):
        tab = [r for r in d if r["b"] == b and tabla(r) and vrp(r) >= corte]
        tabc = [r for r in d if r["b"] == b and tabla(r) and vrp_cons(r) >= corte]
        print(b, corte, "tabla (vrp max de filas)", len(tab), "perdidas", sum(r["perdida"] for r in tab),
              "| tabla (vrp CONS)", len(tabc), "perdidas", sum(r["perdida"] for r in tabc))
