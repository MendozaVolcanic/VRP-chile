# Tarea 1.14 (estudio A): definiciones y tolerancias escritas ANTES de correr

Escrito el 2026-10-14, antes de correr ningún script de esta carpeta. Va en el mismo commit que los
resultados, así que git no prueba el orden (V-16): lo que sí lo prueba es que ningún umbral de abajo
se cambió después de ver un número, y si alguno se cambia queda anotado en el README como enmienda.

## Identidad que se descompone

MIROVA y nosotros usamos la misma fórmula de área fija, VRP = k·A·Σ(L_píxel − L_fondo) (S139, paso 1).
Por eso la razón de una pasada se separa EXACTAMENTE en factores multiplicativos:

    R = D / V_M
      = (D / S_in)                      F_rec   recorte: lo publicado contra la suma de NUESTROS alertados dentro del inner
      × (n+ / Npix)                     F_n     conteo: píxeles que aportan energía, nuestros contra los de MIROVA
      × (Lh − Lbk_M) / (Lh_M − Lbk_M)   F_hot   nivel caliente por píxel, medido contra el fondo de MIROVA
      × (Lh − Lbg) / (Lh − Lbk_M)       F_bg    fondo: lo que resta nuestro fondo contra el de MIROVA

D publicado (V375 `f5_core_vrp_mw` con respaldo `pc.vrp_mw`; V750 y MODIS `pc.vrp_mw`; en la parte B el
valor que el tablero muestra, `mirovaEqVrpDisplay` ejecutado con node). S_in = suma del `vrp_mw` de los
`anomaly_pixels` a `dist_km` <= inner del volcán; n+ = cuántos de ellos tienen `vrp_mw` > 0; Lh = media
de L(bt) de esos n+; Lbg = Lh − S_in/(k·A·n+) (fondo implícito medio, exacto por construcción).
Npix, Lh_M = Tot_Lmir_hot/Npix y Lbk_M = Tot_Lmir_bk/Npix salen del OSF v2.5 (sólo 2025). En la
parte B (2026, referencia NRT sin Npix) sólo se separan F_rec y G = S_in / V_M.

Reparto del déficit: en escala logarítmica, la fracción que aporta cada factor es
media(ln F) / media(ln R) sobre las pasadas del estrato. Intervalos: bootstrap por noche de volcán
(se remuestrean noches, no pasadas, porque las pasadas de una misma noche no son independientes),
2.000 réplicas, percentiles 2,5 y 97,5, semilla 114.

Remuestreo (D17): dentro de G (o de F_n·F_hot en la parte A), efecto de la banda de ángulo cenital
contra la banda de nadir (0 a 20°), con efecto fijo por volcán. Su aporte por pasada es el efecto de
su banda; su fracción, la media de ese aporte sobre media(ln R).

## Población

- Parte A: OSF v2.5, `Dayflag == 0`, `class == 1`, VRP > 0, 11 Tier A, 2025-02-15 a 2025-12-01,
  record nuestro de la misma resolución a ±10 min con cúmulo en el cráter (predicado de S139).
- Parte B: referencia unificada (CONS ∪ OCR ∪ historia), filas ALERTA nocturnas a ±120 s de un record
  nuestro que el tablero publica. Dos tramos (A104): 2026-04-01 a 2026-08-28 y 2026-08-29 a 2026-10-14.
  VIIRS 375 con VRP de MIROVA <= 0,05 MW fuera de la razón (D-9, `experiments/_s151_alertas_minimas/`),
  contadas aparte. Pasadas con alerta que no publicamos: aparte (es recall, no magnitud).
- Parte C: pares de brazos de A/B ya corridos (ramas `s146-ab/<run>` y el zip de S143), sobre las
  mismas pasadas positivas, para medir cuánto mueve la magnitud cada palanca ya implementada.

## Controles que pueden fallar (tolerancias fijadas ahora)

- C1, reconstrucción por píxel (parte B, records con `diag_L_bg_w_m2_sr_um`, volcanes sin kernel
  local, `final_hotspot_source` distinto de `test1_roi`): `vrp_px` = k·A·(L(bt) − L_bg)/1e6 con mi
  propio Planck (c1 = 1,191042e8, c2 = 14388, λ 3,74 / 4,05 / 3,929 µm). Acierto si
  |Δ| <= max(0,0002 MW; 1 %). Pasa si acierta >= 95 % de los píxeles con `vrp_mw` > 0.
- C2, reconstrucción del cúmulo de un píxel (A y B): si `pc.n_pixels == 1`, hay un `anomaly_pixel` con
  |vrp − pc.vrp_mw| <= 0,0006 MW a <= 0,05 km del centroide. Pasa si >= 98 %.
- C3, réplica del núcleo F5' (V375): `pipeline.f5_core.f5_core_vrp_mw` recalculado desde los píxeles
  contra el persistido, |Δ| <= 0,001 MW. Pasa si >= 99 %.
- C4, fondo implícito contra anillo (parte A, sin kernel, sin `test1_roi`): |Lbg_px − L(t_bg_k)| /
  L(t_bg_k) <= 1 %. Pasa si >= 90 % de los píxeles.
- C5, pareo azaroso: el mismo pareo con la hora corrida +6 h debe dar <= 2 % de los pares reales.
- C6, punto de partida (parte B): con la definición del auto-audit (noche, máximo de `pc.vrp_mw` del
  tablero sobre máximo de alerta de MIROVA, 2026-08-15 a 2026-10-14) reproduzco la mediana por volcán
  de `data/audit_continuous/latest.json` dentro de ±0,05 en los volcanes con n >= 15. Puede fallar
  porque la data y la referencia siguieron creciendo desde las 11:53 UTC; si falla, se informa cuánto.
- C7, identidad: el producto de los factores reproduce R con error relativo < 1e-9 (sólo caza errores
  de código, no de física; se declara así).

Si un control falla, el factor que depende de él queda SIN DATO, no se interpreta.
