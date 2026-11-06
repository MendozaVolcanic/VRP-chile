# -*- coding: utf-8 -*-
"""S173: copia del consolidado de hoy SIN unas claves, para probar las capas de recuperacion de la referencia.

POR QUE. Los tests de la union historica (S150) y del respaldo (S139/S140) usaban el snapshot VIVO como el
consolidado que perdio filas. El 2026-11-02 el consolidado remoto de Mirova-v1 repuso 3.444 filas (las perdidas de
la union bajaron de 2.503 a 37, commit 79f410697), los controles pasaron a rojo y los tests positivos quedaron
pasando sin probar nada (la fila llegaba por el snapshot, no por la capa). La perdida se simula: se escribe el
snapshot de hoy sin esas claves, asi la prueba no depende de lo que haga el remoto.

La clave se calcula con los mismos normalizadores que `leer_pasadas` (A6: el instrumento de la referencia), y la
copia se comprueba con `leer_pasadas` despues de escribirla: si la simulacion no quito lo que debia, falla aca.
"""
import csv
from pathlib import Path

from pipeline.mirova_csv_loader import normalize_sensor, normalize_volcano_name
from scripts.referencia_mirova_unificada import SNAP_CONS, clave, leer_pasadas


def snapshot_sin(claves_cons, destino: Path, origen: Path = SNAP_CONS, quitadas: Path = None) -> Path:
    """Escribe en `destino` el consolidado `origen` sin las filas cuyas claves (volcan, bucket, fecha[:16], "CONS")
    estan en `claves_cons`. Si se da `quitadas`, escribe ahi las filas quitadas con el mismo encabezado (sirve de
    union historica simulada). Devuelve `destino`."""
    quitar = set(claves_cons)
    with open(origen, encoding="utf-8", newline="") as fh:
        lector = csv.DictReader(fh)
        campos = lector.fieldnames
        filas, fuera = [], []
        for r in lector:
            k = (normalize_volcano_name(r.get("Volcan")), normalize_sensor(r.get("Sensor")),
                 (r.get("Fecha_Satelite_UTC") or "").strip()[:16], "CONS")
            (fuera if k in quitar else filas).append(r)
    with open(destino, "w", encoding="utf-8", newline="") as fh:
        esc = csv.DictWriter(fh, fieldnames=campos)
        esc.writeheader()
        esc.writerows(filas)
    if quitadas is not None:
        with open(quitadas, "w", encoding="utf-8", newline="") as fh:
            esc = csv.DictWriter(fh, fieldnames=campos)
            esc.writeheader()
            esc.writerows(fuera)
    # Control de dos lados (A110, verificador S173 P2): quito lo pedido y SOLO lo pedido. Las claves que quedan en la
    # copia son exactamente las del origen menos las quitadas; un helper que borrara todo pasaria el primer lado.
    antes = {clave(f) for f in leer_pasadas(origen, "CONS", "origen")}
    despues = {clave(f) for f in leer_pasadas(destino, "CONS", "simulada")}
    quedan = quitar & despues
    assert not quedan, f"la perdida simulada no quito {len(quedan)} claves, p. ej. {sorted(quedan)[:2]}"
    assert despues == antes - quitar, f"la perdida simulada toco {len((antes - quitar) ^ despues)} claves ajenas"
    assert quitar & antes, "ninguna de las claves pedidas estaba en el origen: no se simulo ninguna perdida"
    return destino
