# ════════════════════════════════════════════════════════════════════
# FICHA SDA · miniaturas.py · SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Guardar y rotar una miniatura por pasada (las 10 más nuevas por volcán y sensor) para el panel
#                 «Últimas 10 pasadas» del tablero, como el Latest10NTI de MIROVA. NO decide nada: no cambia la
#                 detección, el VRP ni la clase; muestra la escena de cada pasada (nubes, borde de franja, foco).
# Lógica        : (1) la vía «código MIROVA» deja en el record una clave interna con el NTI de su grilla cuantizado
#                 (pipeline/mirova_v750_codigo.py::miniatura_nti, sólo con --miniaturas); (2) run_pipeline la saca
#                 antes de store.append_record (Recolector.recoger); (3) al terminar el volcán, para cada sensor se
#                 toman los 10 records más nuevos del store y se escribe su PNG si la corrida trae la miniatura del
#                 MISMO gránulo; si no, se conserva la anterior del mismo gránulo; los PNG que salen de las 10 se borran.
# Modelo/método : Reglas deterministas, sin ML (punto 5.5 Res.372). PNG gris de 8 bits escrito con la biblioteca
#                 estándar (el NRT no instala Pillow).
# Datos entrada : Records del store del volcán y las miniaturas de la corrida. SIN datos personales.
# Salida        : data/miniaturas/<Volcan>/<FAMILIA>/<AAAAMMDD_HHMM>_<SENSOR>.png y data/miniaturas/<Volcan>/indice.json
# Limitaciones  : Sólo pasadas nocturnas (el fetch no baja las diurnas; MIROVA muestra ambas). Las pasadas que caen a K
#                 no tienen grilla de MIROVA y quedan sin imagen (`sin_imagen: "detector_k"`).
# Refs/datos    : docs/DISENO_MINIATURAS_POR_PASADA.md. Ficha: docs/FICHA_SDA_VRP_CHILE.md
# ════════════════════════════════════════════════════════════════════
"""Miniaturas por pasada (S184). Ver la cabecera y docs/DISENO_MINIATURAS_POR_PASADA.md."""
from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

import numpy as np

CLAVE = "_miniatura"
N_ULTIMAS = 10
FAMILIAS = ("VIIRS375", "VIIRS750", "MODIS")
RAIZ_DEFECTO = Path(__file__).resolve().parent.parent / "data" / "miniaturas"
# Campos que el índice copia del record guardado. POR QUÉ copiarlos y no recalcularlos: así la miniatura y el tablero
# nunca dicen dos cosas distintas sobre la misma pasada.
_CAMPOS_RECORD = ("datetime_utc", "sensor", "granule", "product_version", "vrp_mw", "n_anomalous_pixels",
                  "sensor_zenith_deg", "sensor_azimuth_deg", "solar_zenith_deg", "distance_class",
                  "final_hotspot_dist_km", "via_codigo_mirova")
_CAMPOS_DIAG = ("motivo_vacio", "celdas_sin_dato", "dayflag", "sunglint")
_CAMPOS_MINI = ("n", "escala_nti", "alertadas", "nti_p2", "nti_p98")


def familia_de_sensor(sensor):
    """VIIRS_*_750 = 750 m (bandas M); VIIRS_* = 375 m (bandas I); MODIS_* = MODIS (A48)."""
    s = str(sensor or "")
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS"):
        return "VIIRS750" if s.endswith("_750") else "VIIRS375"
    return None


def _trozo(tipo, datos):
    return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF)


def _filtrar(u8, filtro):
    """Aplica un filtro PNG (0 a 4) a todas las filas. POR QUÉ: el filtro adecuado achica el archivo a la mitad o
    menos; se prueban los cinco y se queda el más chico (determinista)."""
    x = u8.astype(np.int16)
    arriba = np.vstack([np.zeros((1, x.shape[1]), np.int16), x[:-1]])
    izq = np.hstack([np.zeros((x.shape[0], 1), np.int16), x[:, :-1]])
    diag = np.hstack([np.zeros((x.shape[0], 1), np.int16), arriba[:, :-1]])
    if filtro == 0:
        pred = np.zeros_like(x)
    elif filtro == 1:
        pred = izq
    elif filtro == 2:
        pred = arriba
    elif filtro == 3:
        pred = (izq + arriba) // 2
    else:
        p = izq + arriba - diag
        pa, pb, pc = np.abs(p - izq), np.abs(p - arriba), np.abs(p - diag)
        pred = np.where((pa <= pb) & (pa <= pc), izq, np.where(pb <= pc, arriba, diag))
    return ((x - pred) % 256).astype(np.uint8)


def png_gris(u8):
    """PNG gris de 8 bits, sin pérdida y determinista (mismos datos, mismos bytes), con la biblioteca estándar."""
    u8 = np.ascontiguousarray(u8, dtype=np.uint8)
    alto, ancho = u8.shape
    mejor = None
    for filtro in range(5):
        f = _filtrar(u8, filtro)
        crudo = np.hstack([np.full((alto, 1), filtro, np.uint8), f]).tobytes()
        comp = zlib.compress(crudo, 9)
        if mejor is None or len(comp) < len(mejor):
            mejor = comp
    ihdr = struct.pack(">IIBBBBB", ancho, alto, 8, 0, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + _trozo(b"IHDR", ihdr) + _trozo(b"IDAT", mejor) + _trozo(b"IEND", b"")


def _nombre(familia, rec):
    dt = str(rec.get("datetime_utc", "")).replace("-", "").replace(":", "").replace("T", " ").replace(" ", "_")
    return f"{familia}/{dt}_{rec.get('sensor')}.png"


def _escribir_si_cambia(ruta, datos):
    """Escribe sólo si cambia el contenido: un archivo reescrito igual no cambia nada en git, pero así tampoco se
    toca la fecha de modificación ni se gasta escritura."""
    if ruta.exists() and ruta.read_bytes() == datos:
        return
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(datos)


class Recolector:
    """Junta las miniaturas de una corrida, por volcán y por (datetime_utc, sensor), con el gránulo del que salen."""

    def __init__(self):
        self._m = {}

    def recoger(self, volcan, record):
        """Saca la clave interna del record (para que el store no la vea) y la guarda. Un record sin ella (K, o la
        vía apagada) no hace nada."""
        if not record:
            return
        mini = record.pop(CLAVE, None)
        if mini is None:
            return
        llave = (record.get("datetime_utc"), record.get("sensor"))
        self._m.setdefault(volcan, {})[llave] = (record.get("granule"), mini)

    def cantidad(self, volcan):
        return len(self._m.get(volcan, {}))

    def escribir_volcan(self, volcan, records, raiz=RAIZ_DEFECTO, n=N_ULTIMAS):
        """Reescribe data/miniaturas/<volcan>/ con las n pasadas más nuevas de cada sensor del store y devuelve el
        índice. POR QUÉ desde el store y no desde la corrida: el tablero muestra lo que el store guardó; la corrida
        sólo aporta las imágenes. POR QUÉ conservar la anterior del mismo gránulo: si NASA no entregó un gránulo en
        esta corrida, borrar su imagen la haría desaparecer del tablero sin que nada haya cambiado."""
        carpeta = Path(raiz) / volcan
        previo = {}
        ruta_idx = carpeta / "indice.json"
        if ruta_idx.exists():
            try:
                for fam, entradas in json.loads(ruta_idx.read_text(encoding="utf-8")).get("familias", {}).items():
                    for e in entradas:
                        previo[(e.get("datetime_utc"), e.get("sensor"))] = e
            except (json.JSONDecodeError, AttributeError):
                previo = {}
        corrida = self._m.get(volcan, {})
        indice = {"volcan": volcan, "n_ultimas": n, "familias": {}}
        conservar = set()
        for fam in FAMILIAS:
            recs = sorted((r for r in records if familia_de_sensor(r.get("sensor")) == fam),
                          key=lambda r: str(r.get("datetime_utc", "")), reverse=True)[:n]
            entradas = []
            for r in recs:
                llave = (r.get("datetime_utc"), r.get("sensor"))
                diag = r.get("diag_codigo_mirova") or {}
                e = {k: r.get(k) for k in _CAMPOS_RECORD}
                e.update({k: diag.get(k) for k in _CAMPOS_DIAG})
                nombre = _nombre(fam, r)
                gran, mini = corrida.get(llave, (None, None))
                ant = previo.get(llave)
                if mini is not None and gran == r.get("granule"):
                    _escribir_si_cambia(carpeta / nombre, png_gris(mini["u8"]))
                    e.update({k: mini.get(k) for k in _CAMPOS_MINI})
                    e.update({"archivo": nombre, "sin_imagen": None})
                elif (ant and ant.get("archivo") and ant.get("granule") == r.get("granule")
                      and (carpeta / ant["archivo"]).exists()):
                    e.update({k: ant.get(k) for k in _CAMPOS_MINI})
                    e.update({"archivo": ant["archivo"], "sin_imagen": None})
                else:
                    e.update({k: None for k in _CAMPOS_MINI})
                    e.update({"archivo": None,
                              "sin_imagen": ("detector_k" if r.get("via_codigo_mirova") is not True
                                             else "sin_granulo_en_esta_corrida")})
                if e["archivo"]:
                    conservar.add(e["archivo"])
                entradas.append(e)
            indice["familias"][fam] = entradas
        for fam in FAMILIAS:
            for p in (carpeta / fam).glob("*.png") if (carpeta / fam).exists() else ():
                if f"{fam}/{p.name}" not in conservar:
                    p.unlink()
        texto = json.dumps(indice, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        _escribir_si_cambia(ruta_idx, texto.encode("utf-8"))
        return json.loads(texto)
