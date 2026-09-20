# -*- coding: utf-8 -*-
"""S146: eje de referencia por pasada (`classification`), calculado en post-proceso.

POR QUE. El dashboard publica bastante mas que MIROVA y el operador no tiene como saber si lo que
mira esta respaldado por la referencia o es solo nuestro. El diseno aprobado
(docs/audit_s145/CLASSIFICATION_SUSTRATO_Y_DISENO.md §5.2) deriva cinco valores del cruce con el
CSV de MIROVA, reutilizando `scripts/banco_paridad.py:etiquetar`, y prohibe cualquier valor que
prometa un juicio fisico que el dato no sostiene.

Cada test que mide algo responde dos preguntas en su docstring:
  (1) si lo que mide estuviera roto, ¿fallaria?   (2) con el instrumento muerto, ¿se veria distinto?
"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import clasificacion_referencia as cr  # noqa: E402

SCRIPT = ROOT / "scripts" / "clasificar_referencia.py"
DATA = ROOT / "data" / "mirova_equivalent"
# Ventana fija dentro del regimen actual y cubierta por el canal OCR del snapshot.
INI, FIN = "2026-09-01", "2026-09-14"
VOL = "Villarrica"


def _rec(fecha_hora, sensor="VIIRS_SNPP"):
    dt = datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": VOL, "b": cr.bp.bucket(sensor), "dt": dt, "noche": fecha_hora[:10],
            "clave": f"{fecha_hora}|{sensor}"}


def _fila(fecha_hora, tipo, bucket="VIIRS375", source="CONS", vrp=0.0, dist=None):
    return {"volcano": VOL, "sensor_bucket": bucket, "fecha_utc": fecha_hora + ":00",
            "source": source, "tipo": tipo, "vrp_mw": vrp, "dist_km": dist}


def _clasificar(recs, filas):
    coords = cr.bp._coords_por_volcan()
    cr.clasificar_pasadas(recs, filas, coords, ("2026-09-01", "2026-09-30"))
    return [r["valor"] for r in recs]


# ---------------------------------------------------------------- un caso sintetico por valor
def test_confirmado_en_la_misma_pasada():
    """(1) Si el pareo a +-2 min se rompiera, daria no_reference. (2) Sin filas da no_reference."""
    assert _clasificar([_rec("2026-09-05 05:00")],
                       [_fila("2026-09-05 05:01", "ALERTA_TERMICA", vrp=0.4)]) == ["mirova_confirmed"]


def test_misma_noche_en_otra_pasada():
    """La alerta de MIROVA es de OTRO sensor y otra hora de la misma noche del volcan.
    (1) Si se perdiera el resumen por noche, daria mirova_silent. (2) Sin la alerta da silent."""
    filas = [_fila("2026-09-05 05:00", "ALERTA_TERMICA_OCR", bucket="MODIS", source="OCR", vrp=1.0),
             _fila("2026-09-05 06:40", "RUTINA")]
    assert _clasificar([_rec("2026-09-05 06:40")], filas) == ["mirova_same_night"]
    assert _clasificar([_rec("2026-09-05 06:40")], filas[1:]) == ["mirova_silent"]


def test_la_referencia_miro_y_no_publico():
    """(1) Si RUTINA con VRP 0 no se reconociera, daria no_reference. (2) Sin filas da no_reference."""
    assert _clasificar([_rec("2026-09-06 05:00")], [_fila("2026-09-06 05:00", "RUTINA")]) == ["mirova_silent"]


def test_la_referencia_vio_calor_fuera_del_limite():
    """(1) Si el tipo fuera-de-limite se confundiera con RUTINA, daria silent. (2) Idem sin filas."""
    recs = [_rec("2026-09-07 05:00")]
    assert _clasificar(recs, [_fila("2026-09-07 05:00", "FALSO_POSITIVO_OCR", source="OCR",
                                    vrp=0.8, dist=9.456)]) == ["mirova_saw_outside"]
    assert recs[0]["dist_ref_km"] == 9.456


def test_sin_dato_no_es_lo_mismo_que_miro_y_no_vio():
    """SIN DATO tiene valor propio. (1) Si sin-fila cayera en silent, el primer assert falla.
    (2) El segundo record, con fila RUTINA, prueba que el instrumento si distingue los dos casos."""
    filas = [_fila("2026-09-09 05:00", "RUTINA")]
    assert _clasificar([_rec("2026-09-08 05:00"), _rec("2026-09-09 05:00")], filas) == \
        ["no_reference", "mirova_silent"]


def test_rutina_que_solo_viene_del_ocr_no_cuenta_como_silencio():
    """Hereda la definicion del banco: el negativo limpio exige fila del consolidado."""
    assert _clasificar([_rec("2026-09-10 05:00")],
                       [_fila("2026-09-10 05:00", "RUTINA", source="OCR")]) == ["no_reference"]


# ---------------------------------------------------------------- vocabulario
def test_cinco_valores_y_ninguna_palabra_prohibida():
    """(1) Si alguien agrega un valor `artifact`, falla. (2) Se comprueba que la lista no es vacia."""
    assert list(cr.VALORES) == ["mirova_confirmed", "mirova_same_night", "mirova_silent",
                                "mirova_saw_outside", "no_reference"]
    prohibidas = ("artefact", "artifact", "fals", "false", "ruido", "noise", "spurious", "espuri")
    for valor, etiqueta in cr.VALORES.items():
        texto = (valor + " " + etiqueta).lower()
        assert not any(p in texto for p in prohibidas), texto
        assert len(etiqueta) > 10


# ---------------------------------------------------------------- corrida real (una por modulo)
def _sha_dir(d):
    h = hashlib.sha256()
    for p in sorted(Path(d).glob("*.json")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def _correr(out):
    r = subprocess.run([sys.executable, str(SCRIPT), "--inicio", INI, "--fin", FIN, "--out", str(out)],
                       capture_output=True, text=True, timeout=900,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stderr[-1500:]


@pytest.fixture(scope="module")
def corrida(tmp_path_factory):
    antes = _sha_dir(DATA)
    a, b = tmp_path_factory.mktemp("clasif_a"), tmp_path_factory.mktemp("clasif_b")
    _correr(a)
    _correr(b)
    return {"a": a, "b": b, "antes": antes, "despues": _sha_dir(DATA)}


def test_no_toca_los_records(corrida):
    """(1) Si el script escribiera un solo byte en data/mirova_equivalent/, el hash cambia.
    (2) El hash se calcula sobre 45+ archivos reales, no sobre un directorio vacio."""
    assert len(list(DATA.glob("*.json"))) >= 11
    assert corrida["antes"] == corrida["despues"]


def test_se_niega_a_escribir_dentro_de_los_records(tmp_path, monkeypatch):
    """La guarda cubre --out y --stats. Se prueba contra un directorio TEMPORAL que hace de
    records: si la guarda fallara de verdad, el test no debe ensuciar el directorio que el cron
    NRT escribe (hallazgo V-17 del verificador S146).
    (1) Sin la guarda, escribir() no levanta y el primer raises falla. (2) La ruta hermana que SI
    se acepta prueba que la guarda no rechaza todo."""
    falso = tmp_path / "records"
    falso.mkdir()
    monkeypatch.setattr(cr, "DATA_RECORDS", falso)
    with pytest.raises(SystemExit):
        cr.escribir(falso / "x", {}, (INI, FIN), {})
    with pytest.raises(SystemExit):
        cr.negar_si_dentro_de_records(falso / "stats.json")
    assert not (falso / "x").exists()
    assert cr.negar_si_dentro_de_records(tmp_path / "afuera") == (tmp_path / "afuera").resolve()


def test_precedencia_misma_noche_manda_sobre_fuera_de_limite():
    """La pasada tiene un fuera-de-limite de MIROVA Y hay alerta de MIROVA esa misma noche en otro
    sensor: el evento es el mismo, asi que vale mirova_same_night (diseno S145, 5.2).
    (1) Si la precedencia se invirtiera daria mirova_saw_outside (mutante M1 del verificador, que
    antes pasaba 12 de 12). (2) Sin la alerta de la noche da mirova_saw_outside: el test distingue."""
    fuera = _fila("2026-09-08 06:40", "FALSO_POSITIVO", vrp=0.8, dist=9.0)
    alerta = _fila("2026-09-08 05:00", "ALERTA_TERMICA", bucket="MODIS", vrp=1.0)
    assert _clasificar([_rec("2026-09-08 06:40")], [fuera, alerta]) == ["mirova_same_night"]
    assert _clasificar([_rec("2026-09-08 06:40")], [fuera]) == ["mirova_saw_outside"]


def test_determinista_y_lf(corrida):
    """(1) Un timestamp o un dict sin ordenar en la salida rompe la igualdad de bytes.
    (2) Se exige que haya 11 archivos con contenido, para que no pase comparando nada con nada."""
    archivos = sorted(p.name for p in corrida["a"].glob("*.json"))
    assert archivos == sorted(f"{v}.json" for v in cr.bp.VOLS)
    for n in archivos:
        ba, bb = (corrida["a"] / n).read_bytes(), (corrida["b"] / n).read_bytes()
        assert ba == bb and len(ba) > 200
        assert b"\r" not in ba and ba.endswith(b"\n")
        doc = json.loads(ba)
        assert set(v["valor"] for v in doc["clasificacion"].values()) <= set(cr.VALORES)


def test_control_positivo_noches_que_mirova_confirmo(corrida):
    """Recorrido INDEPENDIENTE del modulo: fila ALERTA del consolidado -> record nuestro del mismo
    volcan y sensor a +-2 min -> su valor tiene que ser mirova_confirmed.
    (1) Si el cruce estuviera roto (claves, zona horaria, bucket), estos records saldrian con otro
    valor y falla. (2) Se exige n > 50: con la referencia muerta n seria 0 y el test falla igual."""
    import csv
    n = 0
    docs = {v: json.loads((corrida["a"] / f"{v}.json").read_text(encoding="utf-8")) for v in cr.bp.VOLS}
    nuestros = {}
    for v in cr.bp.VOLS:
        for k in docs[v]["clasificacion"]:
            fh, sensor = k.split("|")
            nuestros.setdefault((v, cr.bp.bucket(sensor)), []).append(
                (datetime.strptime(fh, "%Y-%m-%d %H:%M"), k))
    from pipeline.mirova_csv_loader import normalize_sensor, normalize_volcano_name
    with open(cr.CONS_DEFECTO, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if not row["Tipo_Registro"].startswith("ALERTA") or not (INI <= row["Fecha_Satelite_UTC"][:10] <= FIN):
                continue
            vol, b = normalize_volcano_name(row["Volcan"]), normalize_sensor(row["Sensor"])
            t = datetime.strptime(row["Fecha_Satelite_UTC"][:16], "%Y-%m-%d %H:%M")
            for dt, k in nuestros.get((vol, b), []):
                if abs(dt - t) <= timedelta(seconds=120):
                    n += 1
                    assert docs[vol]["clasificacion"][k]["valor"] == "mirova_confirmed", (vol, k)
    assert n > 50, n


def test_instrumento_muerto_sin_referencia_todo_es_sin_dato():
    """(1) Si el valor sin dato no existiera o el defecto fuera silent, falla. (2) Es el control
    mismo: records reales con referencia vacia; la corrida real da OTROS valores (test anterior)."""
    res = cr.construir(DATA, [], (INI, FIN))
    valores = {e["valor"] for doc in res.values() for e in doc.values()}
    assert sum(len(d) for d in res.values()) > 500
    assert valores == {"no_reference"}
