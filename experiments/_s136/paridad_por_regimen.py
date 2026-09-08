"""S136 - paridad de magnitud contra MIROVA, partida por regimen de fondo.

POR QUE: D10 justifico la interseccion contextual con un inflado de 8-19x en Tupungatito.
Esa medicion es previa a nadir-fijo (S103) y a #535 (S126). Si hoy, CON el filtro puesto, la
paridad de los nevados esta en banda, el filtro cumple su funcion o ya no hace falta; si esta
fuera de banda, el filtro no basta y el problema es otro. Ninguna de las dos posibilidades
sustituye al A/B (la data lleva el filtro puesto), pero acota el terreno.

Metrica nuestra: f5_core_vrp_mw con fallback a primary_cluster.vrp_mw (A10 + matiz S132/A46:
en VIIRS375 el dashboard publica el nucleo, no pc.vrp_mw).
Ground truth: cargador canonico CONS union OCR (A11).
Pareo: mismo volcan, mismo bucket de sensor, |dt| <= 20 min (patron del proyecto).
Todo numero con denominador y ventana (A90).
"""
import io, json, sys, statistics as st
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from pipeline.mirova_csv_loader import load_mirova_alertas

CORTE = datetime(2026, 8, 28, 23, 0, tzinfo=timezone.utc)
TOL = timedelta(minutes=20)
SNAP = RAIZ / "data" / "mirova_reference" / "mirova_v1_snapshot"
VOLS = ["Tupungatito", "Villarrica", "Llaima", "PlanchonPeteroa",
        "PuyehueCordonCaulle", "Lascar", "Lastarria", "Isluga"]


def ts(s):
    """El cargador devuelve `timestamp` como epoch en string; nuestros records, ISO."""
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
    s = (s or "").strip()
    if not s:
        return None
    if s.isdigit():  # epoch UTC (formato del CSV del scraper)
        return datetime.fromtimestamp(int(s), tz=timezone.utc)
    try:
        t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def magnitud(r):
    """A10 + S132/A46: el nucleo es lo que ve el operador en VIIRS375."""
    v = r.get("f5_core_vrp_mw")
    if v is None:
        pc = r.get("primary_cluster") or {}
        v = pc.get("vrp_mw")
    return v


print("=" * 104)
print("PARIDAD nuestra/MIROVA en VIIRS 375 m, partida por regimen de fondo")
print(f"Corte: {CORTE:%Y-%m-%d %H:%M} UTC (#535). Banda de paridad del proyecto: 0,5 - 2,0")
print("La data de AMBOS regimenes lleva el filtro contextual PUESTO (limite declarado).")
print("=" * 104)
print(f"{'volcan':22s} {'regimen':8s} {'pares':>6s} {'ratio mediano':>14s} {'p25':>7s} {'p75':>7s}")

resumen = {}
for vol in VOLS:
    p = RAIZ / "data" / "mirova_equivalent" / f"{vol}.json"
    if not p.exists():
        continue
    d = json.loads(p.read_text(encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) else d
    nuestros = [r for r in recs
                if r.get("sensor", "").startswith("VIIRS") and "750" not in r.get("sensor", "")
                and ts(r.get("datetime_utc") or r.get("timestamp")) and magnitud(r)]
    alertas = [a for a in load_mirova_alertas(
        cons_path=SNAP / "registro_vrp_consolidado.csv",
        ocr_path=SNAP / "registro_vrp_ocr.csv", volcano=vol)
        if a.get("sensor_bucket") == "VIIRS375" and a.get("vrp_mw")]

    for etiq in ("previo", "actual"):
        ratios = []
        for a in alertas:
            ta = ts(a["timestamp"])
            if ta is None:
                continue
            if (ta < CORTE) != (etiq == "previo"):
                continue
            cand = [r for r in nuestros
                    if abs(ts(r.get("datetime_utc") or r.get("timestamp")) - ta) <= TOL]
            if not cand:
                continue
            r = min(cand, key=lambda r: abs(ts(r.get("datetime_utc") or r.get("timestamp")) - ta))
            m = magnitud(r)
            if m and a["vrp_mw"] > 0:
                ratios.append(m / a["vrp_mw"])
        resumen[(vol, etiq)] = ratios
        if ratios:
            s = sorted(ratios)
            q = lambda f: s[min(len(s) - 1, int(f * len(s)))]
            print(f"{vol:22s} {etiq:8s} {len(s):6d} {st.median(s):14.2f} {q(.25):7.2f} {q(.75):7.2f}")
        else:
            print(f"{vol:22s} {etiq:8s} {0:6d} {'-':>14s}")
    print()

print("=" * 104)
print("LECTURA: el regimen 'actual' abarca solo desde el 28-ago, asi que su n es chico por")
print("construccion (A90: el denominador manda). Un ratio con n<10 no sostiene un veredicto.")
