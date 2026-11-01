# -*- coding: utf-8 -*-
"""V1a. Segunda mitad de 161: K real contra un placebo SIN INFORMACION del mismo tamano.
Desde las tablas por pasada que el evaluador original escribe (t_C0_K.json, armadas con el predicado del tablero
ejecutado con node), por sensor: N = pasadas que C0 publica; r = las que K deja de publicar; P = protegidas
(etiqueta 'pos' con vrp_ref >= 1 MW: aproximacion propia de la lectura A, se compara con el conteo del evaluador);
p0 = probabilidad hipergeometrica de que un apagado AL AZAR de r de las N no toque ninguna de las P
(la que tendria un placebo del tamano de K). Y el placebo t1off medido en esta sesion.
Preguntas del instrumento: (1) si K fuera un apagado al azar, p0 seria grande y se veria; (2) si las tablas
estuvieran vacias, N seria 0. Ventanas: V1 2026-08-29 a 2026-10-08 (referencia congelada con OCR), V2 2026-03-01 a
2026-06-12 (tabla sola; VIIRS desde 2026-04-01).
Uso: python margen_k_v1a.py"""
import json
from math import comb, log10
D = r"D:/vrp-trabajo/temporales/s160_audit/v1a/"
for nom, f, desde_viirs in (("V1", D + "base_v1/tmp/t_C0_K.json", "0000"), ("V2 tabla sola", D + "tmp_v2_si/t_C0_K.json", "2026-04-01"),
                            ("V2 tabla+OCR", D + "tmp_v2_no/t_C0_K.json", "2026-04-01")):
    T = json.load(open(f, encoding="utf-8"))["pasadas"]
    for s in ("MODIS", "VIIRS375", "VIIRS750"):
        N = r = P = Pk = 0
        for k, v in T.items():
            if k.split("|")[1] != s or len(v) != 2: continue
            if s != "MODIS" and k.split("|")[2][:10] < desde_viirs: continue
            c, b = v["control"], v["brazo"]
            prot = c["lab"] == "pos" and (c["vrp_ref"] or 0) >= 1.0
            if c["pub"]:
                N += 1; P += prot
                if not b["pub"]: r += 1
                elif prot: Pk += 1
        p0 = comb(N - P, r) / comb(N, r) if N and r <= N - P else 0.0
        print("%-13s %-8s C0 publica %5d | K deja de publicar %5d (%.0f %%) | protegidas (aprox.) que C0 publica %3d, K conserva %3d | p0 de un azar del mismo tamano = %s" % (
            nom, s, N, r, 100 * r / N if N else 0, P, Pk, ("%.1e" % p0) if p0 else "0 (imposible)"))
