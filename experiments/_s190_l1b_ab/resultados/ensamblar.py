"""Ensambla los resultados del A/B: partes 1-5 del run 44016316141 (intento 1), parte 0 del intento 1 sin las pasadas que
fallaron, y el reintento (run 44024005897). Verifica que no haya pasadas duplicadas ni faltantes contra el manifiesto."""
import json, shutil, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
T = Path(r"D:\vrp-trabajo\temporales\s190_l1b_ab")
E = T / "ensamblado"
shutil.rmtree(E, ignore_errors=True); E.mkdir()
for k in range(1, 6):
    shutil.copy(T / f"run/s190-ab-fase-{k}/s190_parte{k}.json", E / f"s190_parte{k}.json")
p0 = [i for i in json.load(open(T / "run/s190-ab-fase-0/s190_parte0.json", encoding="utf-8")) if i.get("ok")]
re = json.load(open(T / "run3/s190-ab-fase-reintento/s190_reintento.json", encoding="utf-8"))
json.dump(p0 + re, open(E / "s190_parte0.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
todos = sum((json.load(open(f, encoding="utf-8")) for f in sorted(E.glob("*.json"))), [])
claves = [(i["volcan"], i["l1b"]) for i in todos]
man = json.load(open(r"D:\vrp-trabajo\worktrees\s190-l1b-ab\experiments\_s190_l1b_ab\manifiesto_s190.json", encoding="utf-8"))["pasadas"]
print("items", len(todos), "unicos", len(set(claves)), "manifiesto", len(man), "faltan", len({(p["volcan"], p["l1b"]) for p in man} - set(claves)),
      "no_ok", sum(not i.get("ok") for i in todos), "no_reproduce", sum(i.get("ok") and not i.get("reproduce") for i in todos))
