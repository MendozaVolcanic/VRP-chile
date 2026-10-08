"""Verificador S150, D-01/D-02 con los insumos TAL COMO ESTABAN el 2026-10-05.

El primer intento (v_d01_d02_audit_semanal.py) fallo su control positivo: con los datos
de hoy el recall V375 da 98,5 % y no 92,8 %, porque la recuperacion del NRT del
2026-10-08 relleno los dias 10-03 a 10-05. Aca se extraen con `git show` (solo lectura)
los 11 JSON Tier A y los dos CSV de referencia del commit 80b358f6d (el commit del audit
que abrio #757) a una carpeta propia, y se corre el main() real contra ellos.

Control positivo: tiene que reproducir latest.json de ese commit (V375 92,8 % n=194;
MODIS 85,7/28,6 n=7; V750 82,0 n=50; cobertura 58/61).
"""
import io
import json
import os
import subprocess
import sys
from datetime import datetime as _dt, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
REPO = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent / "snap_80b358f6d"
COMMIT = "80b358f6d"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
import auto_audit_weekly as A  # noqa: E402


def show(rel, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return
    data = subprocess.run(["git", "-C", str(REPO), "show", f"{COMMIT}:{rel}"],
                          capture_output=True, check=True).stdout
    dest.write_bytes(data)


for v in A.VOLS:
    show(f"data/mirova_equivalent/{v}.json", BASE / "data/mirova_equivalent" / f"{v}.json")
snap = "data/mirova_reference/mirova_v1_snapshot"
show(f"{snap}/registro_vrp_consolidado.csv", BASE / snap / "registro_vrp_consolidado.csv")
show(f"{snap}/registro_vrp_ocr.csv", BASE / snap / "registro_vrp_ocr.csv")

HOY = _dt(2026, 10, 5, 18, 0, tzinfo=timezone.utc)


class FakeDT(_dt):
    @classmethod
    def now(cls, tz=None):
        return HOY if tz else HOY.replace(tzinfo=None)


A.datetime = FakeDT
A.ROOT = str(BASE)
A.CONS = str(BASE / snap / "registro_vrp_consolidado.csv")
A.OCR = str(BASE / snap / "registro_vrp_ocr.csv")
A.OUTDIR = str(BASE / "out")
A.medir_falsas_ventana = lambda win: (_ for _ in ()).throw(RuntimeError("apagado en verificador"))
A.main()
res = json.loads((BASE / "out/latest.json").read_text(encoding="utf-8"))
print("\n== reproduccion 10-05:", res["verdict"], res["flags"])
for s, r in res["recall"].items():
    print("  ", s, r)
print("  cobertura:", {k: res["cobertura"][k] for k in ("cobertura_propia_pct", "dias_con_datos", "dias_ventana", "avisos")})

# Recalculo: noches ALERTA del denominador sin NINGUN record nuestro ese volcan-sensor-dia
win = res["window"]
alertas = A.load_mirova_alertas(cons_path=A.CONS, ocr_path=A.OCR)
coords = A._coords_por_volcan()
mir = set()
for a in alertas:
    dt = a["fecha_utc"] or ""
    if not (win[0] <= dt[:10] <= win[1]) or a["sensor_bucket"] not in A.SENSORS or a["volcano"] not in A.VOLS:
        continue
    ll = coords.get(a["volcano"])
    if ll:
        try:
            o = _dt.fromisoformat(dt).replace(tzinfo=timezone.utc)
        except ValueError:
            o = None
        if o and A.es_pasada_diurna_descartada(a["sensor_bucket"], ll[0], ll[1], o):
            continue
    mir.add((a["volcano"], a["sensor_bucket"], dt[:10]))
dato, crater, dias_dato, dias_crater = set(), set(), set(), set()
for v in A.VOLS:
    for rec in json.loads((BASE / "data/mirova_equivalent" / f"{v}.json").read_text(encoding="utf-8"))["records"]:
        dt = rec.get("datetime_utc") or ""
        if not (win[0] <= dt[:10] <= win[1]):
            continue
        b = A.our_bucket(rec.get("sensor", ""))
        if b is None:
            continue
        dato.add((v, b, dt[:10]))
        dias_dato.add(dt[:10])
        pc = rec.get("primary_cluster") or {}
        x = pc.get("vrp_mw") or 0.0
        cd = pc.get("centroid_dist_km")
        if 0 < x <= A.CAP and cd is not None and cd <= A.INNER[v]:
            crater.add((v, b, dt[:10]))
            dias_crater.add(dt[:10])
print("\nultimo dia con dato:", max(dias_dato), "| dias con dato:", len(dias_dato),
      "| dias con deteccion crater (lo que cuenta el guard):", len(dias_crater))
print("dias con dato pero sin deteccion de crater:", sorted(dias_dato - dias_crater))
for s in A.SENSORS:
    ks = [k for k in mir if k[1] == s]
    sin = sorted(k for k in ks if k not in dato)
    fallos = [k for k in ks if k not in crater]
    ks2 = [k for k in ks if k in dato]
    c2 = sum(1 for k in ks2 if k in crater)
    print(f"  {s}: n={len(ks)} fallos={len(fallos)}; de esos fallos, sin NINGUN record nuestro: {len(sin)} "
          f"{sin} | recall sobre noches con dato: {c2}/{len(ks2)} = {100*c2/len(ks2) if ks2 else 0:.1f} %")
