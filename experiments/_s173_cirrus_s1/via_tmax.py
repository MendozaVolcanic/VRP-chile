"""S173 S1: distribucion de t_max_k y cenit en los records de la via en produccion (lee medir_ocultos.json)."""
import json, statistics
from pathlib import Path
d = json.loads((Path(__file__).parent / "medir_ocultos_antes.json").read_text(encoding="utf-8"))
via = d["via"]
for zc in ("z<30", "z>=30", "sin_z"):
    s = [r for r in via if r["zc"] == zc]
    t = [r["t_max"] for r in s if r["t_max"] is not None]
    print(f"{zc}: n {len(s)}  con t_max {len(t)}  t_max min {min(t) if t else '-'}  mediana "
          f"{statistics.median(t) if t else '-'}  bajo 273.15: {sum(1 for x in t if x < 273.15)}  bajo 278.15: "
          f"{sum(1 for x in t if x < 278.15)}  pc>10: {sum(1 for r in s if (r['pc'] or 0) > 10)}")
print("pc>10 MW:")
for r in via:
    if (r["pc"] or 0) > 10:
        print(" ", r["vol"], r["dt"], r["sensor"], "z", r["z"], "t_max", r["t_max"], "pc", r["pc"], "npx", r["npx"])
print("t_max mas frios de la via:")
for r in sorted([r for r in via if r["t_max"] is not None], key=lambda r: r["t_max"])[:8]:
    print(" ", r["vol"], r["dt"], "z", r["z"], "t_max", r["t_max"], "pc", r["pc"])
print("sin t_max:", sum(1 for r in via if r["t_max"] is None))
