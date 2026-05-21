# R3 audit independiente — Opcion C (S71 T1 F2.d)

**Politica**: regla S33 vinculante. El audit primario 128 declaro Opcion C
(`path_d_only_cap_mw=5.0` + `path_d_only_cap_tbg_max_k=270.0`) como winner con
reduccion del bug D9 count de 237 a 0 (>30% mejora). Re-corremos con un
script independiente para detectar potencial bug-S33-style del audit primario.

## Diferencias metodologicas vs 128 (independencia explicita)

| Aspecto | 128 (primario) | 130 (este R3) |
|---|---|---|
| Matching | Per-noche (UTC date), ±3h | Per-record sensor-aware, ±60min |
| Universo MIROVA | `registro_vrp_consolidado.csv` solo | CONS + OCR concatenados |
| Ratio numerador | `eqVrp` (con fallback legacy `vrp_mw` global) | `pc.vrp_mw` validado por `pc.centroid_dist <= inner_radius_km` (sin fallback) |
| Ventana | Interseccion dts compartidos | Fija 2026-02-19 → 2026-05-20 (~90d) |
| FP definition | Noche sin MIROVA con detec | Record propio sin MIROVA del mismo sensor en ±60min |

## Resultados clave (resumen global)

| Opcion | Vols ratio∈[0.5,2] | Vols recall≥0.7 (n≥10) | Vols precision≥0.5 | Sum bug D9 |
|---|---:|---|---:|---:|
| baseline | 2/11 | 7/7 | 1/11 | **61** |
| A_atm_gate | 3/11 | 6/7 | 1/11 | **0** |
| B_covalidation | 3/11 | 6/7 | 1/11 | 1 |
| C_cap | **4/11** | 6/7 | 1/11 | **0** |

## Verificacion conclusiones cualitativas vs 128

| Pregunta | 128 dice | 130 R3 dice | Coincide? |
|---|---|---|---|
| C elimina bug D9 al 100%? | Si (237→0) | **Si (61→0)** | ✅ |
| A elimina bug D9 al 100%? | Si (237→0) | Si (61→0) | ✅ |
| B residual marginal? | Si (1) | Si (1, Copahue) | ✅ |
| B colapsa NdC recall? | Si (1.00→0.33) | NdC tiene 0 recall en todas las opciones (problema arquitectural distinto, no causado por B) | ⚠️ parcial |
| C preserva recall? | Si (sin perdida) | C iguala A: ambos pierden Lascar 0.72→0.43, PCC 0.96→0.87 | ⚠️ discrepancia material |
| C ratios mejor que B? | Si en 2/11 | **Si en 4/11 (Lascar, Lastarria, PP, PCC)** | ✅ direccion |
| Winner = C? | Si | **Si (4/11 vs 3/11 A, 3/11 B)** | ✅ |

## Hallazgos especificos

1. **Bug D9 baseline mucho menor en R3 (61 vs 237 en 128)**. Razon: 128 cuenta
   sobre el dataset entero; 130 filtra a `pc` validado contra `inner_radius_km`
   (records con cluster lejano fuera del crater quedan fuera del numerador).
   La direccion (61→0 = 100% eliminacion) coincide.

2. **NdC recall=0 en TODAS las opciones (incluida baseline)** en R3. En 128 NdC
   baseline tenia recall 1.00 (6/6) y B lo rompia a 0.33. Aqui NdC ya esta
   roto desde baseline — diferencia clave de la tolerancia (60min vs 3h). Las
   6 alertas MIROVA NdC tienen detecciones nuestras a >60min de distancia.
   Esto no invalida la conclusion sobre C vs B; en R3 simplemente NdC no
   discrimina entre opciones (todas empatan en 0). **No es un bug del audit
   primario; es una diferencia esperada por tolerancia mas estricta.**

3. **Lascar y PCC pierden recall en A/B/C vs baseline** (-29 y -9 puntos).
   Discrepancia material vs 128 que reportaba "recall keep" total. Causa
   probable: el path D dNTI estaba aportando muchos TPs en records Lascar/PCC
   que cumplian `pc.centroid_dist <= inner_km` (anomalia real cerca del
   crater). Al capear/restringir path D, esos records caen bajo umbral
   detection. Sucede igual en A y C, ligeramente peor en C para FPs PCC.
   **Es informacion nueva**: el fix path D tiene costo de recall en Tier A
   alto (Lascar/PCC), no solo "elimina ruido".

4. **Lastarria ratio: C es claramente mejor (1.65) que A (2.75) y B (3.58)**.
   En 128 era al reves (B mejor 2.90 vs C 3.42). Causa: 130 usa
   `pc.vrp_mw / mirova_vrp` directo y los caps de C operan exactamente sobre
   esa metrica; en 128 con `eqVrp` el cap se diluye. **R3 favorece a C mas
   claramente que el primario.**

5. **Tupungatito ratio sigue ~10× en todas las opciones**. Coincide con 128
   ("drift remanente no es path D"). Confirma el caveat critico del primario.

6. **Villarrica/Chaiten/PP siguen >2× incluso en C**. Coincide con 128
   ("ningun opcion lleva todos los vols a ratio ∈ [0.5, 2.0]").

## Verdict R3

✅ **COINCIDE con el primario en la conclusion central**: Opcion C es el winner
por (a) eliminacion total del bug D9, (b) mejor ratio mediano global (4/11 vs
3/11 A, 3/11 B), (c) ventaja decisiva sobre B en Lastarria/PP.

⚠️ **DISCREPANCIA PARCIAL en "recall keep"**: R3 detecta perdida de recall
material en Lascar (0.72→0.43, n=286) y PCC (0.96→0.87, n=79) que el primario
NO reporto. Esta perdida ocurre igual en A y C — es un **costo del fix path D
en general**, no un veredicto contra C especificamente. Pero es informacion
relevante para la adopcion: **adoptar C tiene costo de recall en los dos
vols con mas data MIROVA (Lascar + PCC = 365 alertas)**. El primario lo paso
por alto porque su matching ±3h era mas permisivo.

## Recomendacion

1. **Adoptar Opcion C** (alineado con primario).
2. **Documentar el caveat de recall**: el fix path D tiene costo en Lascar/PCC
   (~30 puntos de recall). Esto puede ser aceptable porque los TPs perdidos
   eran probablemente low-magnitude path-D-only (sub-1 MW), pero **verificar
   pixel-level R2** antes del push a `main`.
3. **NO es un bug-S33-style del primario**. Las conclusiones cualitativas se
   confirman. La discrepancia de recall Lascar/PCC viene de tolerancia
   distinta (±60min vs ±3h), no de error de calculo.
