"""Verificador S150, hallazgos D-01 y D-02.

Corre el main() REAL de scripts/auto_audit_weekly.py con "hoy" fijado al 2026-10-05
(la corrida que abrio el issue #757), con OUTDIR redirigido a esta carpeta (no toca
data/audit_continuous/) y con el bloque de falsas publicaciones apagado (necesita node y
no entra en recall ni cobertura). Despues recalcula, con los mismos insumos:
  (a) el recall por sensor quitando las noches del apagon (2026-10-03 a 2026-10-05, en
      que el NRT fallo por el token vencido; el ultimo record es del 2026-10-02 07:35);
  (b) la cobertura contada como dias con CUALQUIER record nuestro (dato), no solo dias
      con deteccion de crater.

Preguntas del instrumento:
1. Si el audit confundiera apagon con falla, ¿lo veria? Si: (a) dice cuantas noches
   ALERTA del denominador caen en dias sin ningun record nuestro.
2. Si el instrumento estuviera muerto, ¿se veria distinto? Control positivo: la corrida
   reproducida tiene que dar los mismos numeros que data/audit_continuous/latest.json del
   commit 80b358f6d (MODIS 85,7/28,6 n=7; V375 92,8 n=194; V750 82,0 n=50). Si no
   coinciden, los insumos cambiaron y lo digo.
"""
import io
import json
import os
import sys
from datetime import datetime as _dt, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "out_d01_d02"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
import auto_audit_weekly as A  # noqa: E402

HOY = _dt(2026, 10, 5, 18, 0, tzinfo=timezone.utc)


class FakeDT(_dt):
    @classmethod
    def now(cls, tz=None):
        return HOY if tz else HOY.replace(tzinfo=None)


A.datetime = FakeDT
A.OUTDIR = str(OUT)
A.medir_falsas_ventana = lambda win: (_ for _ in ()).throw(RuntimeError("apagado en verificador"))
A.main()
res = json.loads((OUT / "latest.json").read_text(encoding="utf-8"))
print("\n== reproduccion:", res["window"], res["verdict"], res["flags"])
for s, r in res["recall"].items():
    print("  ", s, r)
print("  cobertura:", {k: res["cobertura"][k] for k in ("cobertura_propia_pct", "dias_con_datos", "dias_ventana", "avisos")})

# --- (a) y (b) recalculados con los mismos insumos ---
win = res["window"]
alertas = A.load_mirova_alertas(cons_path=A.CONS, ocr_path=A.OCR)
coords = A._coords_por_volcan()
mir = {}
for a in alertas:
    dt = a["fecha_utc"] or ""
    if not (win[0] <= dt[:10] <= win[1]) or a["sensor_bucket"] not in A.SENSORS:
        continue
    ll = coords.get(a["volcano"])
    if ll:
        try:
            o = _dt.fromisoformat(dt).replace(tzinfo=timezone.utc)
        except ValueError:
            o = None
        if o and A.es_pasada_diurna_descartada(a["sensor_bucket"], ll[0], ll[1], o):
            continue
    if a["volcano"] in A.VOLS:
        mir[(a["volcano"], a["sensor_bucket"], dt[:10])] = 1

dias_dato = set()
dias_dato_vol_sensor = set()
crater = set()
dash = set()
for vol in A.VOLS:
    d = json.loads((REPO / "data/mirova_equivalent" / f"{vol}.json").read_text(encoding="utf-8"))
    for rec in d["records"]:
        dt = rec.get("datetime_utc") or ""
        if not (win[0] <= dt[:10] <= win[1]):
            continue
        b = A.our_bucket(rec.get("sensor", ""))
        if b is None:
            continue
        dias_dato.add(dt[:10])
        dias_dato_vol_sensor.add((vol, b, dt[:10]))
        pc = rec.get("primary_cluster") or {}
        v = pc.get("vrp_mw") or 0.0
        cd = pc.get("centroid_dist_km")
        if 0 < v <= A.CAP and cd is not None and cd <= A.INNER[vol]:
            crater.add((vol, b, dt[:10]))
            if not rec.get("distance_class") or rec.get("distance_class") == "summit":
                dash.add((vol, b, dt[:10]))

print("\n(b) cobertura por dias con CUALQUIER record:", len(dias_dato), "/", res["cobertura"]["dias_ventana"],
      "; ultimo dia con dato:", max(dias_dato))
falta = sorted(set(_dt.fromisoformat(win[0]).date().fromordinal(x).isoformat()
                   for x in range(_dt.fromisoformat(win[0]).toordinal(), _dt.fromisoformat(win[1]).toordinal() + 1))
               - dias_dato)
print("    dias sin ningun record:", falta)

print("\n(a) recall por sensor, total y sin las noches ALERTA sin dato nuestro de ese volcan-sensor-dia:")
for s in A.SENSORS:
    keys = [k for k in mir if k[1] == s]
    n = len(keys)
    c = sum(1 for k in keys if k in crater)
    sin_dato = [k for k in keys if k not in dias_dato_vol_sensor]
    sd_apagon = [k for k in sin_dato if k[2] >= "2026-10-03"]
    keys2 = [k for k in keys if k[2] < "2026-10-03"]
    c2 = sum(1 for k in keys2 if k in crater)
    print(f"  {s}: n={n} crater={c} ({100*c/n if n else 0:.1f} %) | noches ALERTA sin ningun record nuestro: "
          f"{len(sin_dato)} (de ellas desde 10-03: {len(sd_apagon)} {sorted(sd_apagon)}) | "
          f"sin 10-03..10-05: n={len(keys2)} crater={c2} ({100*c2/len(keys2) if keys2 else 0:.1f} %)")
