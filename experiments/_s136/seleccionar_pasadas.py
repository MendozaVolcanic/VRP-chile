"""S136 - selecciona las pasadas del probe de 3 brazos (filtro contextual del Test 1).

POR QUE ESTAS. La pregunta es cuanto se inflaria la magnitud SIN la interseccion contextual,
en el regimen de hoy. El regimen lo fija el CODIGO que procesa, no la fecha del granule (A87),
asi que se pueden usar pasadas de junio-agosto, donde el ground truth es abundante, y
procesarlas con el codigo actual.

Criterios (fijados antes de mirar magnitudes):
  - nevados donde D10 ubico el fenomeno (Tupungatito el caso original) + control no nevado
    (Lascar, desierto, sin problema de magnitud) para que un efecto universal se distinga de
    uno del glaciar (fue el control el que refuto el proxy anterior);
  - la pasada tiene ALERTA de MIROVA en VIIRS375 a menos de 20 min => hay con que comparar;
  - el Test 1 disparo en nuestro record => el filtro tiene material sobre el que actuar;
  - se reparten en el tiempo (no todas la misma semana) para no medir una sola condicion.

Salida: pasadas_s136.json
"""
import io, json, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from pipeline.mirova_csv_loader import load_mirova_alertas

SNAP = RAIZ / "data" / "mirova_reference" / "mirova_v1_snapshot"
TOL = timedelta(minutes=20)
# 4 nevados + 2 controles no nevados. Tupungatito es el caso de D10.
OBJETIVO = {"Tupungatito": ("nevado", 6), "Villarrica": ("nevado", 4),
            "PlanchonPeteroa": ("nevado", 3), "Llaima": ("nevado", 3),
            "Lascar": ("control", 4), "Lastarria": ("control", 3)}
DESDE, HASTA = datetime(2026, 6, 1, tzinfo=timezone.utc), datetime(2026, 8, 31, tzinfo=timezone.utc)


def ts(s):
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
    s = (s or "").strip()
    if not s:
        return None
    if s.isdigit():
        return datetime.fromtimestamp(int(s), tz=timezone.utc)
    try:
        t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


sel = []
for vol, (clase, cupo) in OBJETIVO.items():
    p = RAIZ / "data" / "mirova_equivalent" / f"{vol}.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) else d
    nuestros = [r for r in recs
                if r.get("sensor", "").startswith("VIIRS") and "750" not in r.get("sensor", "")
                and r.get("triggered_test1") and ts(r.get("datetime_utc") or r.get("timestamp"))]
    alertas = [a for a in load_mirova_alertas(
        cons_path=SNAP / "registro_vrp_consolidado.csv",
        ocr_path=SNAP / "registro_vrp_ocr.csv", volcano=vol)
        if a.get("sensor_bucket") == "VIIRS375" and a.get("vrp_mw")]

    cands = []
    for a in alertas:
        ta = ts(a["timestamp"])
        if ta is None or not (DESDE <= ta <= HASTA):
            continue
        cand = [r for r in nuestros
                if abs(ts(r.get("datetime_utc") or r.get("timestamp")) - ta) <= TOL]
        if not cand:
            continue
        r = min(cand, key=lambda r: abs(ts(r.get("datetime_utc") or r.get("timestamp")) - ta))
        tr = ts(r.get("datetime_utc") or r.get("timestamp"))
        cands.append({"volcan": vol, "clase": clase, "pasada_utc": f"{tr:%Y-%m-%d %H:%M}",
                      "sensor": r.get("sensor"), "mirova_vrp_mw": a["vrp_mw"],
                      "mirova_dist_km": a.get("dist_km"), "mirova_source": a["source"],
                      "n_test1_pixels": r.get("n_test1_pixels")})
    # repartir en el tiempo: ordenar por fecha y tomar `cupo` equiespaciados
    cands.sort(key=lambda c: c["pasada_utc"])
    if len(cands) > cupo:
        paso = len(cands) / cupo
        cands = [cands[int(i * paso)] for i in range(cupo)]
    sel.extend(cands)
    print(f"{vol:22s} {clase:8s} candidatas={len(cands):3d} elegidas={min(len(cands), cupo)}")

out = Path(__file__).parent / "pasadas_s136.json"
out.write_text(json.dumps(sel, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\ntotal elegidas: {len(sel)} -> {out.name}")
for s in sel:
    print(f"  {s['volcan']:22s} {s['pasada_utc']}  {s['sensor']:16s} "
          f"MIROVA {s['mirova_vrp_mw']:7.2f} MW ({s['mirova_source']})")
