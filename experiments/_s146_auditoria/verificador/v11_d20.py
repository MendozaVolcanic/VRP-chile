# -*- coding: utf-8 -*-
"""V-11: D20, banda 31 vs 32 en el NTI de MODIS. Calculo propio con Planck monocromatico (3.959, 11.03, 12.02 um).
Pregunta: el corrimiento es 'despreciable' contra QUE vara? D20 lo compara con el margen a K1 (~0.14). La vara que gobierna
en MODIS es el piso C1 = 0.003 sobre el dNTI (diferencia con los 8 vecinos). Se mide el cambio del dNTI entre bandas para
(i) un pixel mas tibio que sus vecinos por topografia (dT), (ii) un pixel con fraccion f de lava a 1000 K.
(1) roto? control: s(250K) y s(290K) deben reproducir el orden de magnitud de S128 (0.0001 y 0.0054). (2) muerto? si Planck diera
lo mismo en las dos bandas todas las diferencias serian 0 exacto.
Limite: monocromatico, sin respuesta espectral, sin atmosfera ni emisividad. Es orden de magnitud, no calibracion."""
import math, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
h, c, k = 6.62607015e-34, 2.99792458e8, 1.380649e-23
def B(lam_um, T):
    l = lam_um * 1e-6
    return 2*h*c*c / l**5 / (math.exp(h*c/(l*k*T)) - 1) * 1e-6   # W m-2 sr-1 um-1
def nti(T, tir, f=0.0, Th=1000.0):
    m = (1-f)*B(3.959, T) + f*B(3.959, Th); t = (1-f)*B(tir, T) + f*B(tir, Th)
    return (m - t) / (m + t)
C1 = 0.003
print("control S128: s(T)=NTI32-NTI31")
for T in (250, 260, 270, 280, 290): print(f"  T={T} K  NTI31={nti(T,11.03):+.4f}  NTI32={nti(T,12.02):+.4f}  s={nti(T,12.02)-nti(T,11.03):+.5f}")
print("\n(i) pixel dT mas tibio que sus 8 vecinos, sin lava: dNTI por banda y diferencia, en unidades de C1=0.003")
for T in (260, 270, 280):
    for dT in (2, 5, 10):
        d31 = nti(T+dT, 11.03) - nti(T, 11.03); d32 = nti(T+dT, 12.02) - nti(T, 12.02)
        print(f"  fondo {T} K dT={dT:2d}: dNTI31={d31:+.5f} dNTI32={d32:+.5f} dif={d32-d31:+.5f} = {(d32-d31)/C1:+.2f} C1 | cruza C1? b31 {d31>C1} b32 {d32>C1}")
print("\n(ii) pixel con fraccion f a 1000 K sobre fondo T, vecinos sin lava")
for T in (260, 275):
    for f in (1e-5, 2e-5, 5e-5, 1e-4):
        d31 = nti(T, 11.03, f) - nti(T, 11.03); d32 = nti(T, 12.02, f) - nti(T, 12.02)
        print(f"  fondo {T} K f={f:.0e}: dNTI31={d31:+.5f} dNTI32={d32:+.5f} razon32/31={d32/d31:.3f} | cruza C1? b31 {d31>C1} b32 {d32>C1}")
