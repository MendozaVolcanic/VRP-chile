"""S160, D-42 §3: candados de punta a punta del evaluador de D25 sobre brazos sintéticos (V29-01 y V34-03 m20).

POR QUE. El verificador con contexto limpio de D-29 (experiments/_s159/instrumentos/verificador_d29/INFORME.md, V29-01)
mostró que las pruebas de D-29 miran el conjunto de días, la función aislada y el texto fuente, pero no el efecto en
`evaluar`: cinco mutaciones que dejan pasar días excluidos (crudos sin filtrar, tabla sin filtrar, cobertura sin
filtrar, fecha en hora de Chile, cabecera de V1 callada) pasaban en verde. Y V34-03 (m20): la marca «NO VALE PARA
DECIDIR» podía no llegar al estado de la ventana sin que ninguna prueba lo viera. La cuarta adenda (D-42, sellada por
Nicolás el 2026-10-22) pide un caso de punta a punta sobre brazos sintéticos, como
experiments/_s159/instrumentos/verificador_d29/cobertura_sintetica.py.

Los brazos se fabrican desde records de PRODUCCIÓN (data/mirova_equivalent, que es K desde el 2026-09-18), nunca desde
artefactos del A/B; la referencia de cobertura es sintética (directorios propios), y la de MIROVA, la congelada de V1.
Cada perturbación toca SÓLO días excluidos en UN consumidor, y cada aserción mira el número de ese consumidor:
  * D sin ninguna pasada del 17               -> crudos (cobertura entre brazos: «D: le faltan»)
  * la referencia de cobertura con 10 pasadas
    falsas por volcán y sensor el 13          -> referencia de cobertura («faltan N de M»)
  * D con los cúmulos movidos el 18           -> tabla K-brazo (P4 movidas)
  * una pasada a la 01:30 UTC del 13 (el 12 en
    hora de Chile) con el cúmulo movido en D  -> la fecha es la UTC (P4 movidas)
  * la cabecera «== EVALUADO SIN» en la primera línea del informe
Las mismas corridas fijan que el detalle de P2 del JSON trae la calibración (D-42 §2.7), que el estrato 203 se informa,
y, con --calibracion sellada, que la marca de validez llega al estado (D-30.4).
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
DIR = Path(os.environ.get("D25_EVALUADOR_DIR") or (RAIZ / "experiments" / "_s157_prereg_d25"))
EVALUADOR = DIR / "evaluar_d25.py"
REF_V1 = RAIZ / "experiments" / "_s157_prereg_d25" / "_congelado_v1"
VOLS = ["Lascar", "Villarrica"]
DESDE, HASTA = "2026-10-10", "2026-10-18"
MADRUGADA = "2026-10-13 01:30"
BRAZOS = {"K": "_s157_ab_d25_k_control", "G": "_s157_ab_d25_k_gemelo", "D": "_s157_ab_d25_k_on"}
DECLARADO_K = {"ENABLE_TEST1_PATH": False, "ENABLE_TESTS_23_PROSE_BRANCH": True, "ENABLE_MODIS_B22_PRIMARY": True,
               "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375": False, "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750": False,
               "VRP_BG_NEIGHBOR_MAX_HALF_PX": 3, "SENSOR_MODIS": False}
DECLARADO = {"K": DECLARADO_K, "G": DECLARADO_K,
             "D": dict(DECLARADO_K, ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375=True, ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750=True)}


def _bucket(s):
    s = s or ""
    return "VIIRS750" if s.startswith("VIIRS") and s.endswith("_750") else "VIIRS375" if s.startswith("VIIRS") else None


def _base():
    out = {}
    for v in VOLS:
        recs = json.load(open(RAIZ / "data" / "mirova_equivalent" / (v + ".json"), encoding="utf-8"))["records"]
        out[v] = [r for r in recs if DESDE <= r["datetime_utc"][:10] <= HASTA and _bucket(r.get("sensor"))]
    return out


def _mover(r):
    pc = r.get("primary_cluster")
    if pc and pc.get("centroid_lat") is not None:
        pc["centroid_lat"] = pc["centroid_lat"] + 0.002
        return 1
    return 0


def _armar(tmp):
    K = _base()
    # la pasada de la madrugada: copia de un record VIIRS 375 de Láscar, a la 01:30 UTC del 13 (el 12 en hora de Chile)
    src = next(r for r in K["Lascar"] if _bucket(r.get("sensor")) == "VIIRS375")
    K["Lascar"].append(dict(copy.deepcopy(src), datetime_utc=MADRUGADA))
    # pasadas que el determinismo (K' contra K) tiene que contar: las de K fuera de los días excluidos, por sensor
    excl = ("2026-10-13", "2026-10-17", "2026-10-18")
    esperado = {s: len({"%s|%s" % (v, r["datetime_utc"][:16]) for v in VOLS for r in K[v]
                        if _bucket(r.get("sensor")) == s and r["datetime_utc"][:10] not in excl})
                for s in ("VIIRS375", "VIIRS750")}
    en_excluidos = sum(r["datetime_utc"][:10] in excl for v in VOLS for r in K[v])
    G = copy.deepcopy(K)
    D = copy.deepcopy(K)
    movidos = 0
    for v in VOLS:
        D[v] = [r for r in D[v] if r["datetime_utc"][:10] != "2026-10-17"]
        for r in D[v]:
            if r.get("primary_cluster"):
                r["diag_bg_vecinos_n_sin_vecinos"] = 0
            if r["datetime_utc"][:10] == "2026-10-18" or r["datetime_utc"].startswith(MADRUGADA):
                movidos += _mover(r)
    raiz = tmp / "raiz"
    (raiz / "logs").mkdir(parents=True)
    for n, recs in (("K", K), ("G", G), ("D", D)):
        (raiz / BRAZOS[n]).mkdir()
        for v, rr in recs.items():
            json.dump({"records": rr}, open(raiz / BRAZOS[n] / (v + ".json"), "w", encoding="utf-8"))
            fl = dict(DECLARADO[n], PROFILE_NAME=BRAZOS[n], DATA_SUBDIR=BRAZOS[n])
            (raiz / "logs" / ("%s_%s.log" % (BRAZOS[n], v))).write_text("FLAGS_BRAZO " + json.dumps(fl) + "\n",
                                                                         encoding="utf-8")
    # referencia de cobertura sintética: histórico vacío; «producción» = K sin la madrugada, más 10 pasadas falsas por
    # volcán y sensor el 13 (03:00 a 03:09 UTC) que ningún brazo tiene
    hist, prod = tmp / "cob_hist", tmp / "cob_prod"
    hist.mkdir(); prod.mkdir()
    for v in VOLS:
        recs = [{"datetime_utc": r["datetime_utc"], "sensor": r["sensor"]} for r in K[v]
                if not r["datetime_utc"].startswith(MADRUGADA)]
        for sensor in ("VIIRS_NOAA20", "VIIRS_NOAA20_750"):
            recs += [{"datetime_utc": "2026-10-13 03:%02d" % i, "sensor": sensor} for i in range(10)]
        json.dump({"records": recs}, open(prod / (v + ".json"), "w", encoding="utf-8"))
    return raiz, hist, prod, {"movidos": movidos, "esperado": esperado, "en_excluidos": en_excluidos}


def _correr(tmp, calibracion):
    raiz, hist, prod, medido = _armar(tmp)
    out = tmp / "out.json"
    cmd = [sys.executable, str(EVALUADOR), "--ventana", "V1", "--raiz", str(raiz), "--logs", str(raiz / "logs"),
           "--out", str(out), "--tmp", str(tmp / "tmp"), "--vols", ",".join(VOLS), "--desde", DESDE, "--hasta", HASTA,
           "--ref", str(REF_V1), "--cobertura", str(hist), str(prod), "--calibracion", calibracion]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    assert p.returncode == 0, "el evaluador cayó:\n" + p.stderr[-3000:]
    return json.load(open(out, encoding="utf-8")), p.stdout, medido


@pytest.fixture(scope="module")
def simetrica(tmp_path_factory):
    return _correr(tmp_path_factory.mktemp("e2e_simetrica"), "simetrica")


@pytest.fixture(scope="module")
def sellada(tmp_path_factory):
    return _correr(tmp_path_factory.mktemp("e2e_sellada"), "sellada")


def test_poder_las_perturbaciones_existen(simetrica):
    """Sin esto las demás aserciones podrían pasar porque no hay nada que filtrar."""
    res, out, medido = simetrica
    assert medido["en_excluidos"] >= 20, "sólo %d pasadas de K en días excluidos: sin poder" % medido["en_excluidos"]
    assert medido["movidos"] >= 1, "ningún cúmulo movido en D en días excluidos: sin poder"
    assert min(medido["esperado"].values()) >= 20, medido["esperado"]
    assert res["dias_excluidos"] == ["2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20"], res["dias_excluidos"]


def test_la_cabecera_de_d29_es_la_primera_linea(simetrica):
    """V29-01 (p7): D-29 pide los días «declarados en el veredicto»; en V1 la primera línea del informe los nombra."""
    res, out, _ = simetrica
    primera = next(l for l in out.splitlines() if l.startswith("=="))
    assert primera.startswith("== EVALUADO SIN 2026-10-13, 2026-10-17"), primera


def test_la_exclusion_llega_a_los_crudos(simetrica):
    """V29-01 (p2): D no tiene ninguna pasada del 17, que está excluido. Si los crudos no se filtraran, la cobertura
    entre brazos diría «D: le faltan N de K»."""
    res, out, _ = simetrica
    assert "le faltan" not in out, [l for l in out.splitlines() if "le faltan" in l]
    assert res["cobertura_ok"] is True, [l for l in out.splitlines() if "faltan" in l]


def test_la_exclusion_llega_a_la_referencia_de_cobertura(simetrica):
    """V29-01 (p4): la referencia tiene 10 pasadas por volcán y sensor el 13 que ningún brazo tiene."""
    res, out, _ = simetrica
    assert not any("faltan " in l and " de " in l for l in out.splitlines()), [l for l in out.splitlines() if "faltan" in l]
    assert res["cobertura_ok"] is True


def test_la_exclusion_llega_a_la_tabla_y_la_fecha_es_utc(simetrica):
    """V29-01 (p3 y p6): el determinismo (K' contra K) cuenta las pasadas de la tabla K-brazo. Tiene que contar las de
    K fuera de los días excluidos, ni una más: ni las del 13, 17 y 18, ni la de la 01:30 UTC del 13 (el 12 en hora de
    Chile; la fecha que manda es la UTC). Y P4 no ve los cúmulos que D movió el 18 y en esa pasada."""
    res, out, medido = simetrica
    for s, n in medido["esperado"].items():
        linea = next((l for l in out.splitlines() if l.strip().startswith(s) and "pasadas, misma decisión" in l), None)
        assert linea is not None, "sin la línea de determinismo de %s" % s
        assert int(linea.split()[1]) == n, "%s: la tabla cuenta %s pasadas, fuera de los días excluidos son %d" % (s, linea.split()[1], n)
    assert res["P4"]["movidas"] == 0, res["P4"]
    assert MADRUGADA not in json.dumps(res, ensure_ascii=False)


def test_los_controles_pasan_y_el_veredicto_vale(simetrica):
    res, out, _ = simetrica
    assert res["controles_ok"] is True and all(res["cableado"].values()), (res["controles_ok"], res["cableado"])
    assert res["vale_para_decidir"] is True and "NO VALE PARA DECIDIR" not in res["estado"], res["estado"]


def test_el_json_trae_la_calibracion_de_p2_y_el_estrato_203(simetrica):
    """D-42 §2.7: «Se informa siempre, en el detalle de P2 del JSON». NOTA_ESTRATO_203.md: tabla y totales."""
    res, out, _ = simetrica
    for regla in ("original", "SN"):
        info = res["por_regla"][regla]["info"]
        for s in ("VIIRS375", "VIIRS750"):
            for campo in ("calibrada", "falsos_gana", "falsos_pierde", "falsos_bloquea", "n_sorteos",
                          "semilla_calibracion", "resultado_sin_calibrar"):
                assert campo in info["P2|%s" % s], (regla, s, campo)
        assert "estrato_203" in info, regla
        assert {"n", "recupera_D", "enciende_D", "no_cambia", "pasadas"} <= set(info["estrato_203"]), info["estrato_203"]


def test_la_marca_de_la_calibracion_sellada_llega_al_estado(sellada):
    """V34-03 (m20) y D-30.4: con --calibracion sellada el veredicto no vale para decidir, y lo dice el ESTADO de la
    ventana, no sólo el campo del JSON."""
    res, out, _ = sellada
    assert res["vale_para_decidir"] is False, res.get("vale_para_decidir")
    assert "NO VALE PARA DECIDIR" in res["estado"], res["estado"]
    assert "NO VALE PARA DECIDIR" in out.splitlines()[-1] or "NO VALE PARA DECIDIR" in out, out[-500:]
