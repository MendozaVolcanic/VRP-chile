"""Convert MIROVA CSV history to JSON for frontend."""
import csv, json
from pathlib import Path

root = Path(__file__).parent.parent
out_dir = root / "data" / "mirova"
out_dir.mkdir(parents=True, exist_ok=True)

rows = []
with open(root / "Historial_Puyehue_Cordon_Caulle.csv", newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        rows.append({
            "datetime_utc": r["Fecha_Satelite_UTC"],
            "sensor": r["Sensor"],
            "VRP_MW": float(r["VRP_MW"]),
            "distancia_km": float(r["Distancia_km"]) if r["Distancia_km"] else None,
            "clasificacion": r["Clasificacion Mirova"],
        })

rows.sort(key=lambda x: x["datetime_utc"])
out = {"volcano": "PuyehueCordonCaulle", "source": "MIROVA", "records": rows}
(out_dir / "PuyehueCordonCaulle.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False)
)
print(f"OK: {len(rows)} registros -> data/mirova/PuyehueCordonCaulle.json")
