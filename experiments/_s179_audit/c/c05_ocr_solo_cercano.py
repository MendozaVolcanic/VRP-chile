# -*- coding: utf-8 -*-
"""Frente C, auditoria S179. Instrumento c05: las protegidas solo del OCR de F26-V en VIIRS 375 y 750, por brazo.

QUE MIDE. El §4.1 del pre-registro manda a DECIDE NICOLAS (fila 4) toda protegida solo del OCR que la via pierde y K
publica, y dice que N-3 queda subsumida. El lector (lectura L4) saca de la fila 4 las de Suomi NPP anteriores al
2026-10-09. Aqui se cuenta, con las funciones del propio lector (objeto de la auditoria) y sin la exencion L4,
cuantas protegidas solo del OCR pierde cada brazo de posicion (radiante, cercano, pico) que K publica.

LAS DOS PREGUNTAS. (1) Si la exencion escondiera perdidas, esto lo ve: lista cada pasada con lo que publica cada
brazo. (2) Si el instrumento estuviera muerto: tiene que encontrar las 21 (VIIRS 375) y 20 (VIIRS 750) protegidas
solo del OCR que c03 conto con codigo propio; si da 0, aborta. Control positivo: con el brazo radiante tienen que
salir las mismas 3 perdidas que dio c03.

Uso: python c05_ocr_solo_cercano.py   (lee D:/vrp-trabajo/temporales/s179-audit/c/tabla_tag.json e insumos/)
"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
WT = Path("D:/vrp-trabajo/worktrees/s178-lectura")
T = Path("D:/vrp-trabajo/temporales/s179-audit/c")
sys.path.insert(0, str(WT / "experiments/_s172_retro_paquete"))
import leer_retro as L          # objeto de la auditoria: se usa su variante de posicion y su predicado

R = L.Reglas()
tabla = json.load(open(T / "tabla_tag.json", encoding="utf-8"))
ocr = [f for f in tabla if f["tramo"] == "F26-V" and f["estado"] == "ok" and f["lab_union"] == "protegida"
       and f["lab"] != "protegida"]
print("protegidas solo del OCR en F26-V (evaluables):", len(ocr), {b: sum(1 for f in ocr if f["b"] == b) for b in ("VIIRS375", "VIIRS750")})
if not ocr:
    sys.exit("ABORTA: 0 protegidas solo del OCR")
via = {}
for vol in {f["vol"] for f in ocr}:
    d = json.load(open(T / "insumos/via" / (vol + ".json"), encoding="utf-8"))
    for r in d["records"]:
        via[(vol, r["sensor"], r["datetime_utc"][:16])] = r
import banco_paridad as bp
inner = bp.inner_desde_html()
casos, idx = [], []
for i, f in enumerate(ocr):
    rec = via[(f["vol"], f["sensor"], f["dt"])]
    for brazo in L.BRAZOS:
        casos.append((L._variante(R, rec, L.REGLA_DE[brazo], inner[f["vol"]]), inner[f["vol"]]))
        idx.append((i, brazo))
for (i, brazo), v in zip(idx, R.F4.predicado_node(casos)):
    ocr[i]["pub_" + brazo] = int(v[0]); ocr[i]["mag_" + brazo] = float(v[1] or 0.0)
for b in ("VIIRS375", "VIIRS750"):
    print("\n" + b)
    for brazo in L.BRAZOS:
        perd = [f for f in ocr if f["b"] == b and f["pub_K"] and not f["pub_" + brazo]]
        n3 = [f for f in perd if "SNPP" in f["sensor"] and f["dt"][:10] < "2026-10-09"]
        print(f"  brazo {L.REGLA_DE[brazo]}: solo OCR que K publica y el brazo no: {len(perd)} (de ellas N-3, Suomi NPP antes del 2026-10-09: {len(n3)})")
        for f in perd:
            print("     ", f["vol"], f["sensor"], f["dt"], "OCR", f.get("mir_union"), "MW | K publica", f["mag_K"], "| via: cumulo", f.get("pc_V"),
                  "MW, clase", f.get("dc_V"), ", a", f.get("fh_V"), "km")
    print("  plataformas de las solo OCR:", sorted({f["sensor"] for f in ocr if f["b"] == b}))
