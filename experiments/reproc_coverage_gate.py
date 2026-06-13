"""Gate de completitud de reproc (AUDIT_S106 P2.6 / punto ciego 4.3).

Causa raíz de los 5 vols truncados S106: un reproc de GH Actions puede terminar con
`conclusion=success` y aun así dejar data PARCIAL — el circuit-breaker A64 degrada con
gracia (devuelve lo que pudo bajar) y ningún `reproc-*.yml` verifica completitud. El
único motivo por el que S106 lo detectó fue un audit manual. Esto lo hace un gate
reutilizable y assertable (exit!=0 bajo umbral) para usar como step de workflow o
chequeo pre-promoción.

Compara la cobertura de granules de un staging de reproc contra la PRODUCCIÓN actual
(o un baseline), por sensor-bucket, dentro de una ventana. Truncación real = el reproc
tiene MENOS granules que la referencia (no por ausencia de pasadas: la referencia ya
las incluye o no).

Uso:
  python reproc_coverage_gate.py --staging <dir> [--ref data/mirova_equivalent]
      [--sensor v375|v750|modis|all] [--win 2026-01-29:2026-06-08] [--min 0.95]
  staging: dir con <vol>.json (mergeados) o estructura <vol>/<chunk>/<vol>.json.
Exit 0 si todos los vols >= min cobertura; exit 1 si alguno trunca (lista los gaps).
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Tupungatito",
        "Chaiten", "Copahue", "NevadosDeChillan", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]


def _recs(p):
    obj = json.load(open(p, encoding="utf-8"))
    return obj.get("records", obj) if isinstance(obj, dict) else obj


def _bucket_ok(sensor, which):
    s = str(sensor or "")
    if which == "all":
        return s.startswith("VIIRS") or s.startswith("MODIS")
    if which == "modis":
        return s.startswith("MODIS")
    if which == "v750":
        return s.endswith("750")
    if which == "v375":
        return s.startswith("VIIRS") and not s.endswith("750")
    return False


def _keys(recs, which, w0, w1):
    out = set()
    for r in recs:
        d = (r.get("datetime_utc") or "")[:10]
        if _bucket_ok(r.get("sensor"), which) and w0 <= d <= w1:
            out.add((r.get("datetime_utc"), r.get("sensor")))
    return out


def _staging_recs(staging, vol):
    """Devuelve (records, present). Soporta 3 layouts: <vol>.json directo,
    <vol>/<chunk>/<vol>.json, y artifacts planos *<vol>*/<vol>.json (gh run
    download deja s106rest-<vol>-<chunk>/<vol>.json). present=False si el vol
    no figura en el staging (no se chequea)."""
    direct = staging / f"{vol}.json"
    if direct.exists():
        return _recs(direct), True
    out, present = [], False
    voldir = staging / vol
    if voldir.is_dir():
        present = True
        for chunk in sorted(voldir.glob("*")):
            f = chunk / f"{vol}.json"
            if f.exists():
                out.extend(_recs(f))
    for d in sorted(staging.glob(f"*{vol}*")):  # artifacts planos
        f = d / f"{vol}.json"
        if f.exists():
            present = True
            out.extend(_recs(f))
    return out, present


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--staging", required=True)
    ap.add_argument("--ref", default=str(ROOT / "data/mirova_equivalent"))
    ap.add_argument("--sensor", default="v375")
    ap.add_argument("--win", default="2026-01-29:2026-06-08")
    ap.add_argument("--min", type=float, default=0.95)
    a = ap.parse_args()
    w0, w1 = a.win.split(":")
    staging, ref = Path(a.staging), Path(a.ref)

    print(f"{'vol':<20}{'ref':>7}{'reproc':>8}{'cobertura':>11}  veredicto")
    truncated = []
    checked = 0
    for vol in VOLS:
        refp = ref / f"{vol}.json"
        if not refp.exists():
            continue
        rep_recs, present = _staging_recs(staging, vol)
        if not present:
            continue  # vol no incluido en este reproc
        checked += 1
        ref_k = _keys(_recs(refp), a.sensor, w0, w1)
        rep_k = _keys(rep_recs, a.sensor, w0, w1)
        cov = len(rep_k) / max(len(ref_k), 1)
        ok = cov >= a.min
        if not ok:
            truncated.append((vol, len(ref_k) - len(rep_k), cov))
        print(f"{vol:<20}{len(ref_k):>7}{len(rep_k):>8}{cov:>10.1%}  "
              f"{'OK' if ok else 'TRUNCADO (' + str(len(ref_k)-len(rep_k)) + ' faltan)'}")

    if checked == 0:
        print(f"\nGATE ERROR: 0 volcanes encontrados en {staging} — staging vacio o "
              f"layout no reconocido. Un gate que pasa sin chequear es peligroso (P2.6).")
        sys.exit(2)

    if truncated:
        print(f"\nGATE FALLA: {len(truncated)} vol(s) bajo {a.min:.0%} de cobertura.")
        print("Reprocesar los chunks faltantes ANTES de promover (la union conserva")
        print("legacy, pero deja el vol con posicion mixta honesta/legacy).")
        sys.exit(1)
    print(f"\nGATE OK: todos los vols >= {a.min:.0%} cobertura.")


if __name__ == "__main__":
    main()
