# -*- coding: utf-8 -*-
"""S165 V375-E: diagnóstico de las diferencias de la equivalencia (equivalencia_v375e.json). Sólo lectura.

POR QUÉ aparte. El veredicto de equivalencia_v375e.py es el pre-registrado (PREREGISTRO_IMPL_V375E.md §3) y no se toca.
Este script, escrito DESPUÉS de verlo, responde la pregunta que el pre-registro manda hacer cuando algo no calza: ¿de
dónde sale cada diferencia? Dos lecturas:
  (1) VRP: cada pasada fuera de tolerancia contra la vara, ¿calza con el port usando el fondo de la regla de MATLAB
      (código independiente de S163)? Si calza, la diferencia es el relleno del port viejo, no la vía (adenda §7.3).
  (2) Publicación: cada pasada donde la vía y el port publican distinto con la regla que decide en evaluar.py
      («cercano»), ¿tiene la misma máscara y el mismo VRP (contra la vara o contra la regla de MATLAB)? Si los tiene,
      lo único que difiere es la regla de posición del record: la vía (procesar_grilla, compartida con VIIRS 750 y
      MODIS) mide la distancia del cúmulo 8-conexo de la alertada MÁS RADIANTE al cráter (corrección C-4 del censo
      S159); evaluar.py, la del alertado MÁS CERCANO a X0, Y0 (V-2 del verificador de S159: MIROVA informa el píxel
      cercano aunque haya uno lejano más brillante).
Uso: python diagnostico_equivalencia.py > diagnostico_equivalencia_salida.txt
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
TOL = 1e-3
d = json.loads((AQUI / "equivalencia_v375e.json").read_text(encoding="utf-8"))
F = {f["i"]: f for f in d["filas"]}
print("veredicto pre-registrado (no cambia):", d["veredicto"])

con = [f for f in d["filas"] if f["npix_p"] > 0]
fuera = [f for f in con if f["dvrp"] > TOL]
por_relleno = [f for f in fuera if f["dvrp_regla"] is not None and f["dvrp_regla"] <= TOL]
print(f"\n(1) VRP: {len(fuera)} de {len(con)} con alertas fuera de {TOL} MW contra la vara; de ellas {len(por_relleno)} "
      f"calzan con el port usando el fondo de la regla de MATLAB. Todas sobre 4 píxeles: "
      f"{all(f['npix_p'] > 4 for f in fuera)}. Contando esas, {len(con) - len(fuera) + len(por_relleno)} de {len(con)} "
      "dentro de tolerancia.")

dif = d["publicacion"]["cercano"]["distintas"]
print(f"\n(2) publicación con «cercano»: {len(dif)} pasadas distintas de {len(d['filas'])}")
solo_pos = 0
for x in dif:
    f = F[x[0]]
    vrp_igual = f["dvrp"] <= TOL or (f["dvrp_regla"] is not None and f["dvrp_regla"] <= TOL)
    solo = f["misma_mascara"] and vrp_igual
    solo_pos += solo
    print(f"   {f['i']} {f['volcan']} {f['hora']} protegida={f['prot']} npix={f['npix_p']} | publica vía={f['pub_via']} "
          f"port={f['pub_port']['cercano']} | cúmulo más radiante de la vía a {x[6]} km del cráter, alertado más "
          f"cercano del port a {x[7]} km de X0, Y0, inner {x[8]} | misma máscara y VRP: {solo}")
print(f"   con la misma máscara y el mismo VRP (sólo difiere la regla de posición): {solo_pos} de {len(dif)}; "
      f"protegidas: {sum(F[x[0]]['prot'] for x in dif)}; en todas la vía calla y el port publica: "
      f"{all((not F[x[0]]['pub_via']) and F[x[0]]['pub_port']['cercano'] for x in dif)}")
print("\nLectura: la vía de 375 detecta y mide igual que el port; publica distinto sólo donde la escena tiene un "
      "alertado cerca del cráter y otro más radiante lejos. Qué regla de posición es la de MIROVA es una decisión de "
      "método que afecta también a VIIRS 750 y MODIS (procesar_grilla es compartida): no se cambia en este PR.")
