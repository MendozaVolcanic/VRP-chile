# -*- coding: utf-8 -*-
"""S151 (loop 1.5): las dos variantes del fondo por vecinos (D25) en VIIRS 750, como funciones puras.

POR QUÉ UN MÓDULO APARTE. El probe de CI (`probe_d25_v750.py`) y el control sintético local
(`control_sintetico.py`) tienen que usar EXACTAMENTE la misma lógica; si la variante (b) se escribiera
dos veces, el control validaría una copia y el probe correría otra. Sin red y sin escribir nada.

LAS DOS VARIANTES.
  (a) canon: Coppola 2016a p. 8 ec. 6 (con Fernandina 2025 p. 9 y Campus 2024 p. 3): el fondo de cada
      píxel alertado es la media de la radiancia de sus vecinos NO alertados. Es lo que ya hace
      `pipeline.process_viirs_mod.vrp_bg_neighbor_mean_v750` con el flag D25 encendido; acá no se
      reimplementa, se llama.
  (b) canon + descarte de vecinos nublados: además se sacan del promedio los vecinos con BT11 < 255 K.
      Ese descarte es de Coppola 2014 (IJRS, p. 3412, que lo toma de Giglio 2003), NO del canon 2016a
      (docs/audit_s150/meta/VERIFICADOR_DATOS.md D9). Se reporta como variante, no como "lo que exige
      el paper". En M-band la banda de 11 µm más cercana es M15 (10,76 µm).

NaN en M15: el vecino NO se marca como nublado (no hay evidencia de nube). Decisión declarada antes
de correr; el probe cuenta cuántos vecinos quedaron en esa situación.
"""
import numpy as np

UMBRAL_NUBE_K = 255.0


def mascara_nube(bt_tir, umbral_k=UMBRAL_NUBE_K):
    """True donde BT11 < umbral (nube fría). NaN cuenta como no nublado."""
    t = np.asarray(bt_tir, dtype=np.float64)
    with np.errstate(invalid="ignore"):
        return np.isfinite(t) & (t < umbral_k)


def alertados_mas_nube(alert_mask, bt_tir, umbral_k=UMBRAL_NUBE_K):
    """Máscara que se le pasa al fondo por vecinos en la variante (b).

    Un vecino nublado se trata igual que uno alertado: no entra al promedio. Así se reusa la función
    del pipeline sin tocarla y el respaldo (píxel sin vecinos útiles cae al fondo de hoy) es el mismo.
    """
    a = np.asarray(alert_mask, dtype=bool)
    t = np.asarray(bt_tir)
    if a.shape != t.shape:
        raise ValueError(f"alert_mask {a.shape} y bt_tir {t.shape} difieren: la variante (b) no puede correr")
    return a | mascara_nube(t, umbral_k)


def contar_vecinos_nublados(alert_mask, bt_tir, hot_rows, hot_cols, half=1, umbral_k=UMBRAL_NUBE_K):
    """Cuántos de los vecinos (ventana 2*half+1, sin el centro) no alertados están bajo el umbral.

    Diagnóstico para el informe: dice si la variante (b) llegó a cambiar algo en cada píxel.
    """
    a = np.asarray(alert_mask, dtype=bool)
    nube = mascara_nube(bt_tir, umbral_k)
    nr, nc = a.shape
    out = []
    for r, c in zip(hot_rows, hot_cols):
        r, c = int(r), int(c)
        r0, r1, c0, c1 = max(0, r - half), min(nr, r + half + 1), max(0, c - half), min(nc, c + half + 1)
        libres = ~a[r0:r1, c0:c1]
        out.append({"no_alertados": int(libres.sum()), "nublados": int((libres & nube[r0:r1, c0:c1]).sum())})
    return out
