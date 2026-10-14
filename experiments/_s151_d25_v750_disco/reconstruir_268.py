# -*- coding: utf-8 -*-
"""S151 (loop 1.5): reconstruye EXACTAMENTE los 268 negativos de S149 y los congela por clave.

POR QUÉ. El número 268 (docs/AUDIT_S149.md:81, VERIFICADOR_MAGNITUD_CERO.md §5) no dejó la lista de
pasadas. Con el código de hoy la misma definición da 271 (A90: el corpus y el cargador cambiaron).
Para que el probe mida "los 268" y no "unos 271", aquí se rehace el cálculo con TODO tal como estaba
en el commit de S149: los JSON de `data/mirova_equivalent/`, el snapshot de la referencia (los tres
CSV), `volcanoes.yaml`, `frontend/index.html` (predicado) y los scripts del arnés. Medido: con los
JSON y el arnés de ese commit da 3.118 negativos limpios, 268 en la condición y 28 alertas, que son
los números del informe. Hoy da 271, por dos causas distintas (atribución en techo.json, control C4):
los JSON de S149 leídos con el arnés de hoy (el cargador de Loop 0.1, #778) dan 270, y eso explica a
Chaitén 2026-08-17 06:12 y Nevados de Chillán 2026-06-29 06:24; el tercero, Isluga 2026-09-21 05:42, es
del corpus: en S149 su cúmulo tenía 0,025 MW y hoy tiene 0,0 (A90).

Corre el arnés viejo en un subproceso aislado (otro sys.path) para no mezclar módulos.
Salida: lista_268_s149.json. USO: python experiments/_s151_d25_v750_disco/reconstruir_268.py
"""
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REV = "d46b7ec593644397e7bd76e5918c5a411d4ff009"   # el commit que agregó v3_out_20260601.txt (S149, #750)
ARCHIVOS = ["scripts/banco_paridad.py", "scripts/referencia_mirova_unificada.py",
            "scripts/auto_audit_weekly.py", "scripts/calidad_referencia_mirova.py",
            "frontend/index.html", "volcanoes.yaml",
            "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv",
            "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv",
            "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"]

HIJO = r'''
import sys, json, subprocess
from datetime import datetime, timezone
raiz, rev, repo = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, raiz + "/scripts"); sys.path.insert(1, raiz); sys.path.append(repo)
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR
INI, FIN = "2026-06-01", "2026-09-21"
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
por_vb, ns, nv, _ = bp.indexar_referencia(cargar_referencia_unificada(SNAP_CONS, SNAP_OCR), coords, (INI, FIN))
recs = []
for vol in bp.VOLS:
    txt = subprocess.run(["git", "show", f"{rev}:data/mirova_equivalent/{vol}.json"], capture_output=True,
                         check=True, cwd=repo).stdout
    for r in json.loads(txt)["records"]:
        if bp.bucket(r.get("sensor")) != "VIIRS750" or not (INI <= r.get("datetime_utc", "")[:10] <= FIN): continue
        dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if bp.es_pasada_diurna_descartada("VIIRS750", *coords[vol], dt): continue
        recs.append({"vol": vol, "b": "VIIRS750", "dt": dt, "noche": r["datetime_utc"][:10], "r": r})
bp.etiquetar(recs, por_vb, ns, nv)
def s0(x):
    r = x["r"]; pc = r.get("primary_cluster")
    if not pc or (pc.get("vrp_mw") or 0) != 0 or r.get("distance_class") != "summit": return False
    d = pc.get("centroid_dist_km"); return d is not None and d <= inner[x["vol"]]
k = lambda x: [x["vol"], x["r"]["datetime_utc"], x["r"]["sensor"]]
print(json.dumps({"neg_limpio_v750": sum(x["lab"] == "neg_limpio" for x in recs),
                  "negativos": sorted(k(x) for x in recs if x["lab"] == "neg_limpio" and s0(x)),
                  "alertas": sorted(k(x) for x in recs if x["lab"] == "pos" and s0(x))}))
'''


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        for a in ARCHIVOS:
            dst = Path(tmp) / a
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(subprocess.run(["git", "show", f"{REV}:{a}"], capture_output=True, check=True,
                                           cwd=ROOT).stdout)
        o = subprocess.run([sys.executable, "-c", HIJO, tmp, REV, str(ROOT)], capture_output=True, text=True,
                           encoding="utf-8")
        if o.returncode != 0:
            raise SystemExit("el arnés de S149 falló:\n" + o.stderr[-2000:])
    d = json.loads(o.stdout.strip().splitlines()[-1])
    d["rev"] = REV
    d["coincide_con_el_informe"] = (d["neg_limpio_v750"] == 3118 and len(d["negativos"]) == 268
                                    and len(d["alertas"]) == 28)
    (HERE / "lista_268_s149.json").write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"neg_limpio V750 {d['neg_limpio_v750']} | negativos en la condición {len(d['negativos'])} | "
          f"alertas {len(d['alertas'])} | coincide con el informe S149 (3118/268/28): {d['coincide_con_el_informe']}")
    if not d["coincide_con_el_informe"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
