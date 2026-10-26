# -*- coding: utf-8 -*-
"""S162 V750-A: la vía «código MIROVA» de VIIRS 750 (pipeline/mirova_v750_codigo.py), apagada por flag.

POR QUÉ. La vía corre el paquete entero del código de MIROVA (su grilla, su detector, su fondo, su suma). Antes de
que nadie la encienda (A45) tiene que cumplir cuatro cosas, y cada una tiene una prueba aquí:
  1. el flag existe, se lee desde `pipeline.profile` en la sección donde el código lo lee (S124, A89) y está APAGADO
     en los perfiles de producción y laboratorio;
  2. (pendiente del sí de Nicolás, A45) el cableado en el procesador V750 y en el almacén: sus pruebas viven en
     experiments/_s162_v750a/cableado_pendiente/ junto al parche, y se mueven aquí cuando el parche entre;
  3. la grilla por volcán reproduce la geometría de MIROVA medida en S159 (regla GEO) y no se regenera sin revisar
     (A63);
  4. el port da lo mismo que el oráculo validado contra Octave (la equivalencia completa, sobre 510 grillas y 10
     recortes, es `experiments/_s162_v750a/equivalencia_v750a.py`; aquí va lo que corre sin datos externos: la pasada
     de Etna del OSF, que además se cruza con los números de producción de MIROVA, y una grilla sintética).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "experiments/_s158_audit_r2/oraculo"))

from pipeline import mirova_v750_codigo as MV  # noqa: E402

# Esquinas UL de los GeoTIFF VIIRS 375 UTM de MIROVA (experiments/_s158_d17_diseno/grilla_tif_salida.txt de la rama
# s159-pruebas, copiadas a mano en S162): la fuente contra la que se fija grillas_mirova.yaml.
UL_TIF_375 = {"Chaiten": (667206.2, 5280103.7), "NevadosDeChillan": (262920.4, 5942749.2),
              "Copahue": (282765.2, 5832977.6), "Isluga": (492688.9, 7907628.1), "Lascar": (604613.9, 7440011.2),
              "Lastarria": (524493.5, 7241420.3), "Llaima": (237462.7, 5738928.1),
              "PlanchonPeteroa": (332113.2, 6126161.8), "PuyehueCordonCaulle": (718789.4, 5527821.1),
              "Tupungatito": (400718.1, 6326373.5), "Villarrica": (222583.9, 5657578.2)}
# Volcanes cuyo punto de referencia NO es el del yaml, y a cuánto está (INFORME GEO de S159, punto 2), en metros
REFERENCIA_DISTINTA = {"Lascar": 233.0, "PlanchonPeteroa": 1885.0, "Tupungatito": 2787.0}


def _flag(perfil):
    """Lee el flag como lo lee el código: importando pipeline.profile con el perfil elegido (A89)."""
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", "import pipeline.profile as p; print(p.ENABLE_V750_CODIGO_MIROVA)"],
                       cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout.strip().splitlines()[-1]


# ------------------------------------------------------------------------------------------------ 1. el flag
@pytest.mark.parametrize("perfil", ["mirova_equivalent", "experimental"])
def test_flag_apagado_en_produccion_y_laboratorio(perfil):
    assert _flag(perfil) == "False"


def test_flag_se_lee_de_thresholds():
    """El flag vive bajo `thresholds:` (como todo enable_*, S124): un perfil que lo escribe ahí lo enciende."""
    src = (REPO / "pipeline/profile.py").read_text(encoding="utf-8")
    assert 'ENABLE_V750_CODIGO_MIROVA: bool = bool(_t.get("enable_v750_codigo_mirova", False))' in src


# ------------------------------------------------------------------------------------------------ 3. la grilla
@pytest.mark.parametrize("volcan", sorted(UL_TIF_375))
def test_grilla_reproduce_las_esquinas_de_miroVA(volcan):
    """Regla GEO: la grilla de 375 m es la del TIF; la de 750 m está (-187,5; -187,5) de ella (la que usó el censo
    S159) y la de MODIS (-312,5; +437,5), los desfases medidos en los 11 volcanes."""
    ux, uy = UL_TIF_375[volcan]
    g375, g750, g1000 = (MV.grilla_del_volcan(volcan, p) for p in (375.0, 750.0, 1000.0))
    assert (g375["n"], g750["n"], g1000["n"]) == (134, 67, 51)
    assert g375["ul_x"] == pytest.approx(ux, abs=1e-6) and g375["ul_y"] == pytest.approx(uy, abs=1e-6)
    assert (g750["ul_x"] - ux, g750["ul_y"] - uy) == pytest.approx((-187.5, -187.5), abs=1e-6)
    assert (g1000["ul_x"] - ux, g1000["ul_y"] - uy) == pytest.approx((-312.5, 437.5), abs=1e-6)


@pytest.mark.parametrize("volcan", sorted(UL_TIF_375))
def test_punto_de_referencia_contra_el_yaml(volcan):
    """Prueba independiente de la regla (no sale del TIF): en 8 volcanes (X0, Y0) es el lat/lon de volcanoes.yaml a
    ~1 m (redondeo del TIF); en los otros tres está a la distancia que midió S159."""
    import yaml
    from pyproj import Transformer
    v = {x["name"]: x for x in yaml.safe_load((REPO / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    r = MV._referencias()[volcan]
    x, y = Transformer.from_crs("EPSG:4326", f"EPSG:{r['epsg']}", always_xy=True).transform(v[volcan]["lon"],
                                                                                           v[volcan]["lat"])
    d = float(np.hypot(x - r["x0"], y - r["y0"]))
    assert d == pytest.approx(REFERENCIA_DISTINTA.get(volcan, 0.0), abs=2.0)


def test_volcan_sin_grilla_devuelve_none():
    assert MV.grilla_del_volcan("VolcanSinGrilla") is None


def test_roi_de_todos_los_volcanes_es_un_tipo_valido():
    for nombre, r in MV._referencias().items():
        assert r.get("roi_v750", "def") in MV.TIPOS_ROI, nombre


# ------------------------------------------------------------------------------------------------ cajas
def _caja_equivalencia(sensible):
    b = np.zeros((67, 67))
    b[23:44, 23:44] = 1
    b[30:37, 30:37] = 2
    if sensible:
        b[b == 1] = 2
    return b


def test_cajas_def_y_sens_son_las_de_la_equivalencia():
    assert np.array_equal(MV.caja_roi("def"), _caja_equivalencia(False))
    assert np.array_equal(MV.caja_roi("sens"), _caja_equivalencia(True))


def test_caja_crater_para_viirs_375_c13():
    """Diseño para VIIRS 375 (caja C13 en el cráter): la misma función con la grilla de 134 y lado 13."""
    b = MV.caja_roi("crater", n=134, celda_crater=(60, 70), lado_sensible=13, lado_anillo=41, paso_m=375.0)
    assert b.shape == (134, 134)
    assert (b == 2).sum() == 169 and b[54:67, 64:77].min() == 2 and b[53, 70] != 2


def test_caja_tipo_desconocido_falla():
    with pytest.raises(ValueError):
        MV.caja_roi("cualquiera")


# ------------------------------------------------------------------------------------------------ 4. el port
def test_etna_igual_al_oraculo_y_a_produccion_de_miroVA():
    """La pasada de ejemplo del OSF (Etna, NOAA-20, 2023-05-19 00:54): misma máscara y VRP que el oráculo, y los
    números de PRODUCCIÓN de MIROVA (OSF v2.5: Npix 5, Tot_Lmir_hot 1,965342) que ningún port lee."""
    import scipy.io as sio
    import mirova_v750_r2 as ORA
    S = sio.loadmat(REPO / "experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat")
    sg = MV.sunglint_deg(S["sat_zen"].item(), S["sun_zen"].item(), S["sat_azi"].item(), S["sun_azi"].item())
    m = MV.detectar_mirova(S["ZI_M13"], S["ZI_M15"], S["BOX"], int(S["dayflag"].item()), sg)
    ref = ORA.detectar(S["ZI_M13"], S["ZI_M15"], S["BOX"], int(S["dayflag"].item()), sg)[0]
    assert np.array_equal(m, ref) and int(m.sum()) == 5
    v, vr = MV.vrp_mirova(S["ZI_M13"], m), ORA.vrp(S["ZI_M13"], ref)
    assert v["VRP_MW"] == pytest.approx(vr["VRP_MW"], rel=1e-9)
    assert v["L_hot"] == pytest.approx(1.965342180, rel=1e-8)
    # el fondo de fillmissing2 tiene una banda de triangulación de ~3 % (control_etna_salida.txt): VRP contra el OSF
    assert v["VRP_MW"] * 1e6 / 9889528.362 == pytest.approx(1.0, abs=0.03)


def _escena(caliente=True, fila=33, col=33):
    """Grilla sintética de 67 x 67 con fondo tibio y ruido, y un píxel caliente."""
    rng = np.random.default_rng(162)
    T15 = 265.0 + rng.normal(0, 0.3, (67, 67))
    T13 = T15 - 3 + rng.normal(0, 0.3, (67, 67))
    if caliente:
        T13[fila, col] += 25
    return MV.temperatura_a_radiancia(T13, MV.LAMBDA_M13), MV.temperatura_a_radiancia(T15, MV.LAMBDA_M15)


def test_sintetico_igual_al_oraculo():
    import mirova_v750_r2 as ORA
    m13, m15 = _escena()
    for tipo in ("def", "sens", "corona"):
        box = MV.caja_roi(tipo)
        m = MV.detectar_mirova(m13, m15, box, 0, 40.0)
        ref = ORA.detectar(m13, m15, box, 0, 40.0)[0]
        assert np.array_equal(m, ref), tipo
        if ref.any():
            assert MV.vrp_mirova(m13, m)["VRP_MW"] == pytest.approx(ORA.vrp(m13, ref)["VRP_MW"], rel=1e-9)


def test_record_suma_todos_los_alertados_y_sin_modo_de_un_pixel():
    """vrp_mw = pc.vrp_mw = VRP de la UNIÓN (también de un cúmulo lejano); posición = cúmulo más radiante."""
    m13, m15 = _escena()
    T13 = MV.radiancia_a_temperatura(m13, MV.LAMBDA_M13)
    T13[33, 40] += 12                          # segundo foco, más débil, a 5,25 km
    m13 = MV.temperatura_a_radiancia(T13, MV.LAMBDA_M13)
    g = MV.grilla_del_volcan("Lascar")
    box = MV.caja_roi("sens")
    rec = MV.procesar_grilla(m13, m15, g, box, 0, 40.0, (33.0, 33.0), 5.0, "VIIRS_NOAA20_750")
    mask = MV.detectar_mirova(m13, m15, box, 0, 40.0)
    assert mask[33, 33] and mask[33, 40]
    assert rec["vrp_mw"] == rec["primary_cluster"]["vrp_mw"] == round(MV.vrp_mirova(m13, mask)["VRP_MW"], 3)
    assert rec["primary_cluster"]["centroid_dist_km"] == 0.0 and rec["distance_class"] == "summit"
    assert rec["primary_cluster"]["single_pixel_mode"] is False and "d9_capped" not in rec["primary_cluster"]
    assert rec["via_codigo_mirova"] is True and rec["n_anomalous_pixels"] == int(mask.sum())
    assert rec["t_bg_k"] is not None and rec["t_max_k"] > rec["t_bg_k"]


def test_celda_decisiva_para_s1():
    """El diagnóstico S-1 recibe la celda del 7 x 7 del cráter que decide, su zona, su pase y su margen contra el
    umbral de su zona (u2 en la zona 2): con el píxel caliente en el cráter, margen sobre 1 en esa celda."""
    m13, m15 = _escena()
    g = MV.grilla_del_volcan("Lascar")
    rec = MV.procesar_grilla(m13, m15, g, MV.caja_roi("def"), 0, 40.0, (33.0, 33.0), 5.0, "VIIRS_NOAA20_750")
    s1 = rec["diag_codigo_mirova"]["s1"]
    cd = s1["celda_decisiva"]
    assert (cd["fila"], cd["col"], cd["zona"]) == (33, 33, 2) and cd["margen"] > 1
    assert cd["u_nti"] == s1[f"pasada{cd['pase']}"]["u_nti2"] and cd["u_eti"] == s1[f"pasada{cd['pase']}"]["u_eti2"]
    assert s1["pasada1"]["sd_nti"] is not None and s1["pasada2"]["sd_eti"] is not None


def test_sin_alertas_el_record_queda_vacio_pero_con_s1():
    m13, m15 = _escena(caliente=False)
    rec = MV.procesar_grilla(m13, m15, MV.grilla_del_volcan("Lascar"), MV.caja_roi("def"), 0, 40.0, (33.0, 33.0),
                             5.0, "VIIRS_NOAA20_750")
    assert rec["vrp_mw"] == 0.0 and rec["primary_cluster"] is None
    assert rec["diag_codigo_mirova"]["s1"]["celda_decisiva"]["margen"] < 1
