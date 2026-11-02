# -*- coding: utf-8 -*-
"""V2 repro de 205: ¿auto_audit_weekly.main() cae con ValueError la primera vez que la vía publica MODIS en una noche
con alerta de MIROVA?

Pregunta 1 (si estuviera roto, ¿lo veo?): corro main() entero con un escenario donde una pasada MODIS de la vía SÍ
se publica (vrp>0, dash) en una noche con alerta: si REGIMENES no trae VIA_MODIS, estratificar_magnitud cae en
REGIMENES.index. Pregunta 2 (instrumento muerto): control = el mismo escenario con la vía publicada pero
`via=None` (K) tiene que terminar sin excepción y escribir latest.json; y un tercer brazo = el escenario del test
del PR A (vía NO publicada) que tiene que terminar bien (muestra por qué la prueba no lo vio).

Uso: python -I repro_205_valueerror.py <ruta_worktree>
"""
import json
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import scripts.auto_audit_weekly as aa  # noqa: E402

FRONTERA = "2026-09-18"
SHA = "f" * 40
HOY = datetime.now(timezone.utc).date()


def _dia(n):
    return (HOY - timedelta(days=n)).isoformat()


def _rec(fecha, sensor="MODIS_AQUA", vrp=1.0, via=None, hora="07:20"):
    r = {"datetime_utc": f"{fecha} {hora}", "sensor": sensor, "distance_class": "summit",
         "primary_cluster": {"vrp_mw": vrp, "centroid_dist_km": 1.0} if vrp else {},
         "anomaly_pixels": [{}] if vrp else [], "regimen": {"codigo_sha": SHA}}
    if via is not None:
        r["via_codigo_mirova"] = via
    return r


def _brec(fecha, b, pub, lab, sensor="MODIS_AQUA"):
    dt = datetime.strptime(f"{fecha} 07:20", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": "Villarrica", "b": b, "dt": dt, "noche": fecha, "pub": pub, "lab": lab, "lab_original": lab,
            "sha": SHA, "z": 20.0, "sensor": sensor}


def escenario(via_publica, con_via):
    """36 noches con alerta MIROVA MODIS Villarrica; 16 recientes de la vía (si con_via)."""
    records, alertas = [], []
    for n in range(0, 36):
        d = _dia(n)
        alertas.append({"volcano": "Villarrica", "sensor_bucket": "MODIS", "fecha_utc": d + " 07:20:00",
                        "vrp_mw": 0.5})
        reciente = n < 16
        vrp = (1.0 if via_publica else 0.0) if reciente else 1.0
        records.append(_rec(d, vrp=vrp, via=(True if (reciente and con_via) else None)))
    banco = ([_brec(_dia(2), "MODIS", via_publica, "pos")],
             [{"volcano": "Villarrica", "sensor_bucket": "MODIS", "fecha_utc": _dia(2) + " 07:20:00", "vrp_mw": 2.0,
               "tipo": "ALERTA_TERMICA", "source": "CONS"}])
    return records, alertas, banco


def correr(nombre, via_publica, con_via, outdir):
    records, alertas, banco = escenario(via_publica, con_via)
    outdir.mkdir(parents=True, exist_ok=True)
    with mock.patch.multiple(aa, leer_frontera_k=lambda *a: FRONTERA, alertas_mirova=lambda *a, **k: alertas,
                             cargar_filas_referencia=lambda: None,
                             cargar_records=lambda: ({"Villarrica": records},
                                                     {"parse_errors": [], "duplicates_total": 0}),
                             banco_ventana=lambda win: banco, _coords_por_volcan=lambda: {"Villarrica": (-39.42, -71.94)},
                             es_pasada_diurna_descartada=lambda *a: False, _csv_ultima_fecha=lambda p: HOY.isoformat(),
                             OUTDIR=str(outdir), leer_ceses=lambda *a, **k: ([], None)):
        try:
            aa.main()
        except Exception as e:  # noqa: BLE001
            tb = traceback.format_exc().strip().splitlines()
            print(f"[{nombre}] EXCEPCION {type(e).__name__}: {e}")
            print("   " + "\n   ".join(tb[-6:]))
            return "EXCEPCION"
    out = json.loads((outdir / "latest.json").read_text(encoding="utf-8"))
    regs = sorted({rg for d in out.get("magnitud_publicada_by_vol_sensor_regimen", {}).values() for rg in d})
    print(f"[{nombre}] OK verdict={out['verdict']} regimenes_en_salida={regs} "
          f"vigente_por_sensor={out['detector'].get('vigente_por_sensor')}")
    return "OK"


if __name__ == "__main__":
    base = Path(__file__).resolve().parent / "repro_205_out"
    print("REGIMENES =", aa.REGIMENES)
    r1 = correr("A: via PUBLICA (vrp>0) en noche con alerta", True, True, base / "via_publica")
    r2 = correr("B control: misma escena sin via (K publica)", True, False, base / "k_publica")
    r3 = correr("C escena del test del PR A: via NO publica", False, True, base / "via_no_publica")
    print("RESULTADO:", {"via_publica": r1, "control_k": r2, "test_pr_a": r3})
