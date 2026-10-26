# -*- coding: utf-8 -*-
"""Pixel del crater (el mas cercano al ancla) y su vecindad de 3 x 3, por etapa, desde el jsonl del probe (brazo P).
Instrumento: mismas cantidades que analizar.py, cuyo control de identidad paso; solo cambia la seleccion de pixeles.
Uso: python vecindad.py <jsonl> > vecindad_salida.txt
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
for x in open(sys.argv[1], encoding="utf-8"):
    r = json.loads(x)
    P = r["P"]
    ic, jc = P["pixel_crater"][:2]
    print(f"{r['tag']} {r['granulo']} t_bg {P['t_bg']:.2f} crater (i,j)=({ic},{jc}) a {P['pixel_crater'][2]:.2f} km")
    print("   di dj  d_km  DN21  DN22  DN31  BT21   BT22   BTMIR  BT31   NTI      dNTI/umbral        dETI/umbral        T2 T3 comp hot")
    for p in sorted([p for p in P["pixeles"] if p["vecindad_3x3"]], key=lambda p: (p["i"], p["j"])):
        print(f"   {p['i'] - ic:+d} {p['j'] - jc:+d} {p['d_km']:5.2f} {p['dn21']:5d} {p['dn22']:5d} {p['dn31']:5d} "
              f"{p['bt21']:6.2f} {p['bt22']:6.2f} {p['btmir']:6.2f} {p['bt31']:6.2f} {p['nti']:+.4f} "
              f"{p['dnti']:+.5f}/{p['thr_dnti']:.5f} {p['deti']:+.5f}/{p['thr_deti']:.5f}  "
              f"{int(p['pasa2'])}  {int(p['pasa3'])}  {int(p['pasa_compuerta'])}    {int(p['hot'])}")
