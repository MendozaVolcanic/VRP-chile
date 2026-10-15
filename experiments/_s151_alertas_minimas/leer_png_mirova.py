# -*- coding: utf-8 -*-
"""Lee, sin OCR externo, el banner y la hora de adquisicion de las imagenes VRP de MIROVA del archivo local.

POR QUE. El OCR de Mirova-v1 empezo a leer el banner ("Thermal anomaly: NONE / VERY LOW / LOW ...") recien en
su version 30 (agosto de 2026), y en esa muestra el banner solo aparece en VIIRS 375 por debajo de 1 MW. El
archivo local `mirova-tif-archive` (lectura local, sin pull: su copia llega al 2026-05-20) guarda las mismas
imagenes de mayo de 2026 para los tres sensores. Leerlas da una segunda muestra, de otro mes y leida por otro
instrumento, para ubicar la frontera NONE / VERY LOW.

Como se lee. Las imagenes las dibuja MIROVA siempre con la misma fuente y en la misma posicion:
- la hora de adquisicion es el texto rojo "Last Update:DD-Mon-AAAA HH:MM:SS" (UTC: coincide al segundo con las
  horas de `Fecha_Satelite_UTC` del consolidado). Se segmenta por columnas vacias y cada glifo se identifica por
  el hash de su mascara; los 27 glifos distintos de las 4.541 imagenes se etiquetaron a mano mirando la hoja de
  contacto (son "Last Update:", digitos, "-May-" y el sufijo del sensor en las imagenes COMB, que no se usan);
- el banner se clasifica dos veces, por el hash de su mascara de texto (14 mascaras distintas, cada una
  etiquetada mirando un ejemplo) y por el color de fondo mas el ancho del texto (gris NONE, verde VERY LOW o
  LOW, amarillo MODERATE). Las dos lecturas tienen que coincidir en cada imagen; si no, la imagen se reporta.
"""
from __future__ import annotations

import csv
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

ARCHIVO = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/mirova-tif-archive")
VOLCAN = {"ChillanNevadosde": "NevadosDeChillan"}  # el resto de las carpetas ya trae el nombre normalizado

GLIFOS = {"413b65a4cb": "0", "3c096d2707": "a", "262b43eda2": ":", "a81fefb9a6": "2", "ee2c733397": "t",
          "0d5bffb8d1": "-", "c505dc6c4b": "1", "2d9e790dcc": "6", "3fae8b7881": "M", "e574ee26fa": "L",
          "ee6cb076f7": "s", "232cccfd9b": "U", "54c4d76ecb": "p", "18c8edb062": "d", "168a102ab8": "e",
          "abf4adf4a1": "y", "d973ebb605": "5", "b8f149b4d2": "4", "2d954ea772": "8", "249c78cc5b": "9",
          "d1c3a9d33d": "3", "8447f5a6d0": "7",
          # solo en las imagenes COMB (sufijo del sensor), que no se usan
          "9e17309657": "#", "38c84d1953": "#", "787449a552": "#", "fb8b6a3405": "#", "e26147a0e5": "#"}

BANNER_MASCARA = {"6e820d0cad": "NONE", "f887855120": "NONE", "9a5f314838": "VERY_LOW", "ae7e374bd3": "NONE",
                  "bf22b88635": "LOW", "6524471b84": "VERY_LOW", "6a47fa1a01": "NONE", "3c3db194bb": "LOW",
                  "ef32654dc7": "LOW", "e318111afa": "LOW", "b5bf1b3d0d": "NONE", "85cce2968d": "MODERATE",
                  "3fac6c1000": "VERY_LOW", "ec7153cac6": "NONE"}

PATRON = re.compile(r"^LastUpdate:(\d\d)-May-(\d{4})(\d\d):(\d\d):(\d\d)$")


def leer_hora(im: np.ndarray):
    red = (im[48:76, 85:435, 0] > 180) & (im[48:76, 85:435, 1] < 120) & (im[48:76, 85:435, 2] < 120)
    cols = red.any(0)
    x, s = 0, []
    while x < len(cols):
        if cols[x]:
            x0 = x
            while x < len(cols) and cols[x]:
                x += 1
            g = red[:, x0:x]
            ys = np.where(g.any(1))[0]
            g = g[ys.min():ys.max() + 1]
            s.append(GLIFOS.get(hashlib.md5(g.tobytes() + str(g.shape).encode()).hexdigest()[:10], "?"))
        else:
            x += 1
    texto = "".join(s)
    m = PATRON.match(texto)
    if not m:
        return texto, None
    d, a, hh, mm, ss = m.groups()
    return texto, datetime(int(a), 5, int(d), int(hh), int(mm), int(ss), tzinfo=timezone.utc)


def banner_por_mascara(im: np.ndarray):
    b = im[48:76, 630:770].sum(2) < 250
    return BANNER_MASCARA.get(hashlib.md5(b.tobytes()).hexdigest()[:10], "?")


def banner_por_color(im: np.ndarray):
    reg = im[48:76, 445:765]
    fondo = reg[reg.sum(2) > 300]
    r, g, b = np.median(fondo, axis=0)
    # Ancho del texto sin el borde del recuadro (que tambien es oscuro): "...: VERY LOW" ocupa unos 253 px,
    # "...: LOW" unos 207 (medido sobre las 4.541 imagenes; la primera version medía con el borde y la
    # comparacion con la lectura por mascara la marco en 60 imagenes).
    oscuro = im[52:72, 455:755].sum(2) < 150
    xs = np.where(oscuro.any(0))[0]
    ancho = int(xs.max() - xs.min()) if len(xs) else 0
    if r > 200 and g > 200 and b < 120:
        return "MODERATE"
    if g > 200 and r < 150 and b < 150:
        return "VERY_LOW" if ancho > 230 else "LOW"   # "Thermal anomaly: VERY LOW" es mas ancho que "...: LOW"
    if abs(r - g) < 20 and abs(g - b) < 20:
        return "NONE"
    return "?"


def hojas_de_contacto(destino: Path):
    """Para re-verificar a ojo las etiquetas: cada glifo rojo con su etiqueta y un ejemplo de cada mascara de banner.

    Uso: python leer_png_mirova.py <carpeta temporal>   (escribe glifos_rojos.png y banners.png; no van al repo)
    """
    from PIL import ImageDraw
    destino.mkdir(parents=True, exist_ok=True)
    glifos, banners = {}, {}
    with open(ARCHIVO / "index_png.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["kind"] != "VRP":
                continue
            im = np.array(Image.open(ARCHIVO / r["png_path"]).convert("RGB")).astype(int)
            hb = hashlib.md5((im[48:76, 630:770].sum(2) < 250).tobytes()).hexdigest()[:10]
            banners.setdefault(hb, im[46:76, 440:770].astype("uint8"))
            red = (im[48:76, 85:435, 0] > 180) & (im[48:76, 85:435, 1] < 120) & (im[48:76, 85:435, 2] < 120)
            cols, x = red.any(0), 0
            while x < len(cols):
                if cols[x]:
                    x0 = x
                    while x < len(cols) and cols[x]:
                        x += 1
                    g = red[:, x0:x]
                    ys = np.where(g.any(1))[0]
                    g = g[ys.min():ys.max() + 1]
                    glifos.setdefault(hashlib.md5(g.tobytes() + str(g.shape).encode()).hexdigest()[:10], g)
                else:
                    x += 1
    hoja = Image.new("RGB", (6 * 90, 50 * ((len(glifos) + 5) // 6)), "white")
    d = ImageDraw.Draw(hoja)
    for i, (h, g) in enumerate(sorted(glifos.items())):
        img = Image.fromarray(((~g) * 255).astype("uint8")).resize((g.shape[1] * 3, g.shape[0] * 3), Image.NEAREST)
        x0, y0 = (i % 6) * 90, (i // 6) * 50
        hoja.paste(img, (x0 + 2, y0 + 2))
        d.text((x0 + 40, y0 + 15), repr(GLIFOS.get(h, "?")), fill="red")
    hoja.save(destino / "glifos_rojos.png")
    hoja = Image.new("RGB", (330 + 120, 30 * len(banners)), "white")
    d = ImageDraw.Draw(hoja)
    for i, (h, b) in enumerate(sorted(banners.items())):
        hoja.paste(Image.fromarray(b), (0, i * 30))
        d.text((335, i * 30 + 10), BANNER_MASCARA.get(h, "?"), fill="red")
    hoja.save(destino / "banners.png")


def leer_archivo(sensores=("MODIS", "VIIRS375", "VIIRS750")):
    """Una fila por imagen VRP de un sensor (no COMB): volcan, sensor, hora leida, banner (dos lecturas)."""
    out = []
    with open(ARCHIVO / "index_png.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["kind"] != "VRP" or r["sensor"] not in sensores:
                continue
            p = ARCHIVO / r["png_path"]
            im = np.array(Image.open(p).convert("RGB")).astype(int)
            texto, hora = leer_hora(im)
            out.append({"volcano": VOLCAN.get(r["volcano"], r["volcano"]), "sensor": r["sensor"],
                        "png": r["png_path"], "last_modified": r["last_modified_utc"], "texto_hora": texto,
                        "hora": hora, "banner_mascara": banner_por_mascara(im), "banner_color": banner_por_color(im)})
    return out


if __name__ == "__main__":
    import sys
    hojas_de_contacto(Path(sys.argv[1]))
