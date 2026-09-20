# -*- coding: utf-8 -*-
"""d09: divergencia D20 ('despreciable': corrimiento del NTI banda 31 vs 32 de 0,0001 a 0,0054, CONTRA un margen de ~0,14 al K1=-0,8;
'en el dNTI se cancela porque es casi uniforme en la escena'). El umbral que gobierna la deteccion no es K1 sino el piso
C1 = 0,003 (summit) / 0,010 (scene) del dNTI. Aca: Planck monocromatico, corrimiento por T y su DIFERENCIA entre un pixel y
vecinos dT mas frios (lo que sobrevive en el dNTI), comparada contra C1.
Instrumento: (1) control: debe reproducir 0,0001 a 250 K y 0,0054 a 290 K; si no, mi Planck no es el de S128. (2) no aplica (calculo).
LIMITE: cuerpo negro homogeneo, sin respuesta espectral, sin atmosfera ni emisividad: orden de magnitud, no valor."""
import io, sys, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
C1, C2 = 1.191042e8, 1.4387752e4   # W um^4 m^-2 sr^-1 ; um K
def L(lam, T): return C1 / (lam**5 * (math.exp(C2/(lam*T)) - 1))
def nti(T, tir): m = L(3.959, T); t = L(tir, T); return (m - t) / (m + t)
def shift(T): return nti(T, 11.03) - nti(T, 12.02)
out = {"corrimiento_por_T": {T: round(shift(T), 5) for T in (250, 260, 270, 280, 290, 300)}}
out["diferencial_en_dNTI(pixel a T vs vecinos a T-dT)"] = {f"T={T},dT={d}": round(shift(T) - shift(T-d), 5) for T in (270, 280, 290) for d in (1, 3, 5, 10)}
out["umbrales"] = {"C1_summit": 0.003, "C1_scene": 0.010, "margen_K1_citado": 0.14}
out["peor_caso_como_fraccion_de_C1_summit"] = round(max(abs(v) for v in out["diferencial_en_dNTI(pixel a T vs vecinos a T-dT)"].values()) / 0.003, 2)
json.dump(out, open("d09_D20_banda31_vs_32.json", "w"), indent=1); print(json.dumps(out, indent=1))
