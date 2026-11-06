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
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "_s172_retro_paquete"


def _cargar(nombre, archivo, var):
    # mutar_leer_retro.py corre esta batería contra una copia mutada (la variable de entorno da su ruta)
    spec = importlib.util.spec_from_file_location(nombre, os.environ.get(var) or EXP / archivo)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


AM = _cargar("armar_manifiesto_t", "armar_manifiesto.py", "ARMAR_MANIFIESTO_MODULO")
MO = _cargar("armar_montaje_t", "armar_montaje.py", "ARMAR_MONTAJE_MODULO")


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


def test_el_manifiesto_sale_del_blob_del_ref_y_no_del_disco(monkeypatch):
    """Control de que el instrumento puede fallar: si el blob del ref difiere del disco, manda el blob."""
    monkeypatch.setattr(AM, "_blob", lambda ref, ruta: b"contenido del ref\r\n")
    m = AM.manifiesto("cualquier-ref", ["scripts/clase_mirova.py"])
    assert m["scripts/clase_mirova.py"] == hashlib.sha256(b"contenido del ref\n").hexdigest()


def test_un_preregistro_cambiado_desde_el_sello_no_es_igual(monkeypatch):
    monkeypatch.setattr(AM, "_blob", lambda ref, ruta: b"sello" if ref == AM.TAG_SELLO else b"otro texto")
    assert AM.verificar_preregistro("rama")["igual"] is False
    monkeypatch.setattr(AM, "_blob", lambda ref, ruta: b"mismo\r\n" if ref == AM.TAG_SELLO else b"mismo\n")
    assert AM.verificar_preregistro("rama")["igual"] is True          # el fin de línea no cuenta


# ------------------------------------------------------------------------------------------- verificador de #946
def test_main_del_manifiesto_corta_con_3_si_el_preregistro_cambio(monkeypatch, tmp_path):
    """VPR946-03 (G1): el pre-registro distinto del sello corta con 3 y no escribe el manifiesto."""
    monkeypatch.setattr(AM, "_blob", lambda ref, ruta: b"sello" if ref == AM.TAG_SELLO else b"otro")
    sal = tmp_path / "m.json"
    assert AM.main(["--ref", "r", "--salida", str(sal)]) == 3 and not sal.exists()


def test_main_del_manifiesto_incluye_referencias_y_osf(monkeypatch, tmp_path):
    """VPR946-02 (G3): las referencias congeladas y el OSF entran al manifiesto, además de los requeridos."""
    monkeypatch.setattr(AM, "_blob", lambda ref, ruta: b"igual")
    sal = tmp_path / "m.json"
    assert AM.main(["--ref", "r", "--referencia", "ref/cons.csv", "--osf", "ref/osf.csv", "--salida", str(sal)]) == 0
    m = __import__("json").loads(sal.read_text(encoding="utf-8"))
    assert {"ref/cons.csv", "ref/osf.csv"} <= set(m)
    assert set(sys.modules["leer_retro_para_manifiesto"].REQUERIDOS_MANIFIESTO) <= set(m)


def test_montaje_exige_un_tag_por_origen_en_main(tmp_path):
    """VPR946-05 (G4)."""
    err = None
    try:                                     # por aserción, no por pytest.raises: otra excepción tiene que fallar aquí
        MO.main(["--despacho", "HEAD", "--origen", "MOD-D fase 4=HEAD", "--origen", "V375-E=HEAD",
                 "--via-dm", str(tmp_path), "--salida", str(tmp_path / "m.json")])
    except BaseException as e:  # noqa: BLE001
        err = e
    assert isinstance(err, SystemExit) and "un tag por origen" in str(err), repr(err)
    assert not (tmp_path / "m.json").exists()


def test_el_diff_listado_va_de_cada_tag_de_origen_al_despacho(monkeypatch):
    """VPR946-05 (G2): el git diff se pide entre el tag de cada origen y el del despacho, no del despacho contra sí."""
    llamadas = []

    class _R:
        returncode, stdout, stderr = 0, "", ""

    monkeypatch.setattr(MO.subprocess, "run", lambda args, **k: llamadas.append(args) or _R())
    tags = {o: f"tag-{i}" for i, o in enumerate(MO.ORIGENES)}
    MO.listar_diff(tags, "despacho")
    assert [a[2:4] for a in llamadas] == [[tags[o], "despacho"] for o in MO.ORIGENES]
