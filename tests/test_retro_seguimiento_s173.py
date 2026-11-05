# -*- coding: utf-8 -*-
"""S173: lo que el PR #940 declaró faltante antes de leer F26 (pre-registro SELLADO
experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md, tag s173-prereg-retro-sellado, §6 C-montaje y §11).

POR QUÉ. El candado y C-montaje son los controles que dicen «lo que se lee es lo que se selló» y «la vía del despacho es
la vía que midieron los A/B». Si el generador del manifiesto leyera el disco en vez del ref del despacho, o si el de
C-montaje pudiera salir OK con los comparadores propios de cada A/B todavía sin escribir, los dos controles darían verde
sin haber mirado. Cada prueba exige que el instrumento pueda dar rojo.
"""
import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "_s172_retro_paquete"


def _cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, EXP / archivo)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


AM = _cargar("armar_manifiesto_t", "armar_manifiesto.py")
MO = _cargar("armar_montaje_t", "armar_montaje.py")


def _tag(t):
    return subprocess.run(["git", "rev-parse", "-q", "--verify", t], cwd=ROOT, capture_output=True).returncode == 0


def test_el_manifiesto_se_calcula_sobre_el_ref_con_fin_de_linea_lf():
    ruta = "scripts/clase_mirova.py"
    blob = subprocess.run(["git", "show", f"HEAD:{ruta}"], cwd=ROOT, capture_output=True).stdout
    m = AM.manifiesto("HEAD", [ruta])
    assert m == {ruta: hashlib.sha256(blob.replace(b"\r", b"")).hexdigest()}


def test_el_manifiesto_rehusa_una_ruta_que_no_existe_en_el_ref():
    with pytest.raises(SystemExit):
        AM.manifiesto("HEAD", ["no/existe.py"])


def test_el_manifiesto_por_defecto_cubre_lo_que_exige_el_candado():
    rutas = AM.rutas_requeridas(["experiments/x/cons.csv"])
    L = sys.modules["leer_retro_para_manifiesto"]
    assert set(L.REQUERIDOS_MANIFIESTO) <= set(rutas) and set(L.MANIFIESTO_REGLAS) <= set(rutas)
    assert "experiments/x/cons.csv" in rutas


@pytest.mark.skipif(not _tag("s173-prereg-retro-sellado"), reason="sin el tag del sello en este clon")
def test_el_preregistro_del_sello_tiene_el_sha256_lf_declarado():
    r = AM.verificar_preregistro("s173-prereg-retro-sellado")
    assert r["sello"] == "b58a225404c80ae0929b5096d30eea2d36c33cea09979427123f291f3c153c91"
    assert r["igual"] is True


def _rec(vrp, clase="summit"):
    return {"primary_cluster": {"vrp_mw": vrp} if vrp else None, "distance_class": clase}


def test_montaje_compara_pasada_por_pasada_vrp_y_clase():
    k1, k2, k3 = (("Lascar", "MODIS_AQUA", "2026-10-05 05:00"), ("Isluga", "MODIS_AQUA", "2026-10-06 05:00"),
                  ("Llaima", "MODIS_AQUA", "2026-10-07 05:00"))
    via = {k1: _rec(1.0), k2: _rec(0.5), k3: _rec(0.2)}
    ab = {k1: _rec(1.0005), k2: _rec(0.6), ("Copahue", "MODIS_AQUA", "2026-10-08 05:00"): _rec(0.1)}
    d = MO.comparar(via, ab)
    campos = sorted((x["pasada"].split("|")[0], x["campo"]) for x in d)
    assert campos == [("Copahue", "falta_en_via"), ("Isluga", "vrp_mw"), ("Llaima", "falta_en_ab")]
    assert all(x["explicada_por"] is None for x in d)
    assert MO.comparar(via, {k1: _rec(1.0, "far"), k2: _rec(0.5), k3: _rec(0.2)})[0]["campo"] == "distance_class"


def test_montaje_con_comparadores_pendientes_no_puede_salir_ok():
    """Mientras falten los comparadores propios de cada A/B, el JSON de C-montaje no pasa validar_montaje."""
    L = sys.modules["leer_retro_para_montaje"]
    tags = {o: "HEAD" for o in MO.ORIGENES}
    out = MO.armar(tags, "HEAD", {}, {o: {} for o in MO.ORIGENES})
    assert MO.PENDIENTES and not out["estado"].startswith("OK")
    assert L.validar_montaje(out)["estado"].startswith("ROJO")
    assert set(out["tags"]) == set(MO.ORIGENES) and "sin diferencias" in out["diff_listado"]
