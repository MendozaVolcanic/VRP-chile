"""S88 — Limpiar data/mirova_equivalent/Lascar.json con los records feb-2026
reprocesados con la config actual (A45, OK explícito de Nicolás).

Contexto: el reproceso de validación (run 26650931800, perfil
_s88_reproc_validation que `extends: mirova_equivalent`) regeneró Lascar feb-2026
con la config operacional ACTUAL. Como el único delta entre ese perfil y
mirova_equivalent es el `data_subdir`, los records de febrero son IDÉNTICOS a lo
que produciría un reproceso a mirova_equivalent. Por eso no re-corremos 70 min:
mergeamos los records feb del archivo de validación al operacional.

Mecanismo (espeja store.append_record con overwrite=True):
  - Para cada record feb-2026 del archivo de validación, reemplazar (o agregar)
    el record con misma key (datetime_utc, sensor) en el operacional.
  - Los records NO-feb del operacional quedan intactos.
  - Re-ordenar por datetime_utc.

Verificación post-merge (obligatoria, regla integridad S88):
  - El JSON resultante parsea.
  - Todos los records feb del resultado == los del archivo de validación.
  - Los records no-feb no cambiaron en cantidad.
  - Reporta cuántos records feb se reemplazaron / agregaron.

Uso: python experiments/_s88_lascar_reselect/clean_lascar_feb.py [--apply]
  Sin --apply: dry-run (reporta qué haría, NO escribe).
  Con --apply: escribe data/mirova_equivalent/Lascar.json.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
OP = ROOT / "data/mirova_equivalent/Lascar.json"
VAL = ROOT / "data/_s88_reproc_validation/Lascar.json"
APPLY = "--apply" in sys.argv


def is_feb(r):
    return str(r.get("datetime_utc", ""))[:7] == "2026-02"


def key(r):
    return (r.get("datetime_utc"), r.get("sensor"))


op = json.loads(OP.read_text(encoding="utf-8"))
val = json.loads(VAL.read_text(encoding="utf-8"))

op_recs = op["records"]
val_feb = [r for r in val["records"] if is_feb(r)]
val_feb_by_key = {key(r): r for r in val_feb}

op_feb_before = [r for r in op_recs if is_feb(r)]
op_nonfeb = [r for r in op_recs if not is_feb(r)]

# Construir el set nuevo (CONSERVADOR — no borra nada):
#   - no-feb intactos
#   - feb del operacional que NO están en validación (huérfanos) → SE PRESERVAN.
#     Son todos vrp_mw==0 ("procesado sin anomalía"); el reproceso no los
#     regeneró pero borrarlos perdería trazabilidad. No aparecen como detección.
#   - feb del archivo de validación → reemplazan los matched + agregan los nuevos.
op_feb_keys = {key(r) for r in op_feb_before}
replaced = sum(1 for k in val_feb_by_key if k in op_feb_keys)
added = sum(1 for k in val_feb_by_key if k not in op_feb_keys)
orphan_op_feb = [r for r in op_feb_before if key(r) not in val_feb_by_key]
# Salvaguarda dura: NUNCA preservar como huérfano un record con vrp>0 (sería
# una detección real que el reproceso perdió — habría que investigar, no mergear).
orphan_with_vrp = [r for r in orphan_op_feb if (r.get("vrp_mw") or 0) > 0]

new_recs = op_nonfeb + orphan_op_feb + val_feb
new_recs.sort(key=lambda r: r.get("datetime_utc", ""))

print("=== CLEAN LASCAR FEB (dry-run)" + (" — APPLY" if APPLY else "") + " ===")
print(f"operacional: {len(op_recs)} records ({len(op_feb_before)} feb, {len(op_nonfeb)} no-feb)")
print(f"validación:  {len(val['records'])} records ({len(val_feb)} feb)")
print(f"feb reemplazados: {replaced}")
print(f"feb agregados (nuevos): {added}")
print(f"feb huérfanos PRESERVADOS (op sin val, todos vrp=0): {len(orphan_op_feb)}")
print(f"  de ellos con vrp>0 (NO debería haber): {len(orphan_with_vrp)}")
print(f"resultado: {len(new_recs)} records (esperado {len(op_recs)} + {added} nuevos = {len(op_recs)+added})")

# --- Verificación ---
errors = []
# (0) salvaguarda: ningún huérfano preservado tiene vrp>0
if orphan_with_vrp:
    errors.append(f"{len(orphan_with_vrp)} huérfanos con vrp>0 — NO mergear, investigar")
# (1) cada feb de validación está en el resultado con su pc dist
res_feb = {key(r): r for r in new_recs if is_feb(r)}
for k, vr in val_feb_by_key.items():
    if k not in res_feb:
        errors.append(f"feb de validación ausente del resultado: {k}")
        continue
    vpc = (vr.get("primary_cluster") or {}).get("centroid_dist_km")
    rpc = (res_feb[k].get("primary_cluster") or {}).get("centroid_dist_km")
    if vpc != rpc:
        errors.append(f"pc dist mismatch en {k}: val={vpc} res={rpc}")
# (2) todos los huérfanos preservados siguen presentes
res_keys = {key(r) for r in new_recs}
for r in orphan_op_feb:
    if key(r) not in res_keys:
        errors.append(f"huérfano perdido: {key(r)}")
# (3) no-feb intactos
res_nonfeb = [r for r in new_recs if not is_feb(r)]
if len(res_nonfeb) != len(op_nonfeb):
    errors.append(f"no-feb count cambió: {len(op_nonfeb)} -> {len(res_nonfeb)}")
# (4) sin duplicados de key
if len(res_keys) != len(new_recs):
    errors.append(f"keys duplicadas: {len(new_recs)} records, {len(res_keys)} keys únicas")

if errors:
    print("\n[FALLO VERIFICACIÓN]")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("\n[VERIFICACIÓN OK] feb-validación presentes, huérfanos preservados, no-feb intactos, sin dups")

if APPLY:
    out = dict(op)
    out["records"] = new_recs
    # Formato IDÉNTICO a pipeline/store.py:_save — json.dump(indent=2) con
    # ensure_ascii=True (default, escapa no-ASCII a \uXXXX) + newline final.
    # Esto mantiene el diff de git acotado SOLO a los records feb que cambiaron.
    with open(OP, "w") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    # re-leer para confirmar que parsea
    check = json.loads(OP.read_text(encoding="utf-8"))
    assert len(check["records"]) == len(new_recs), "re-read mismatch"
    print(f"\n[APPLIED] {OP} escrito y re-parseado OK ({len(new_recs)} records)")
else:
    print("\n[DRY-RUN] no se escribió nada. Re-correr con --apply para aplicar.")
