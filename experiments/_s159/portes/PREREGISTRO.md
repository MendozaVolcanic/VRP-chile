# Pre-registro del frente PORTES (S159): el código de VIIRS 750 de MIROVA, portado a VIIRS 375 y a MODIS

> Escrito y commiteado **antes** de despachar el workflow (`probe-s159-portes.yml`) y antes de ver ningún resultado del
> port en VIIRS 375 o MODIS. Lo que cambie después de este commit va en una adenda fechada al final, nunca
> reescribiendo esto. Es MEDICIÓN: no decide adopción ni toca `pipeline/`, `data/` ni `frontend/`.

## 1. Pregunta, hipótesis y refutación

MIROVA publicó en OSF (MIT) su código sólo para VIIRS 750 (`experiments/_s158_d17_diseno/osf_codigo_mirova/`). El frente N
mostró que ese código, en la grilla de GEO y con remuestreo lineal, reproduce la magnitud de MIROVA en VIIRS 750 (razón
0,999, cuartiles 0,978 y 1,007, 145 alertas; `experiments/_s159/n/INFORME.md` N-2). Para VIIRS 375 no hay paper que
describa la detección (`experiments/_s159/p2/INFORME.md` H1) y para el fondo de MODIS tampoco (`experiments/_s159/p3/INFORME.md` §0).

- **Hipótesis.** El MISMO código, cambiando sólo bandas, grilla y coeficiente (y nada de lo que el código fija como
  umbral), reproduce en VIIRS 375 y en MODIS las alertas, el silencio y la magnitud de MIROVA como lo hace en VIIRS 750.
- **Refutación por sensor.** Cualquiera de las lecturas R2, R3 o R4 de §5 sale NO REPRODUCE.
- Si reproduce, tenemos la descripción que el paper no da, medida contra MIROVA (A115). Si no, dónde se separa dice qué
  parte es propia del sensor.

## 2. Qué cambia por sensor y qué queda igual (`mirova_port.py`)

El port es un envoltorio del port de VIIRS 750 validado contra Octave en 791 escenas
(`experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py`); la detección y el fondo son sus funciones, sin tocar.

| pieza | VIIRS 750 (el `.m`) | VIIRS 375 | MODIS | de dónde |
|---|---|---|---|---|
| banda MIR | M13, λ 4,05 µm | I4, λ 3,74 | B22 primaria con B21 donde B22 satura (D21), λ 3,959 | `.m` l. 144; `pipeline/process_viirs.py:80`; `pipeline/process_modis.py:75-76`, `merge_mir_bands` |
| banda TIR | M15, λ 10,763 | I5, λ 11,45 | B31, λ 11,03 | `.m` l. 145; `process_viirs.py:1141`; `process_modis.py:81` |
| coeficiente × área | 1,97e7 × 0,5625 km² | 1,80e7 × 0,140625 | 1,89e7 × 1,0 | `.m` l. 88-91; CLAUDE.md «Reglas científicas» (validados S14 contra el OSF) |
| grilla | 67 × 67 de 750 m | 134 × 134 de 375 m, esquina del TIF UTM de MIROVA del 14 y 15 de septiembre | 51 × 51 de 1 km, esquina de 375 + (−312,5, +437,5) | GEO H1 y H2: centros en `X0 − 25000 : paso : X0 + 25000` |
| remuestreo | lineal (N-2) | lineal | lineal | N-2 descartó vecino y cúbico en 750 |
| caja (BOX) | ROI2 7 × 7 (cumbre, umbrales sensibles), ROI1 21 × 21 | mismo tamaño en metros: ROI2 ±2.625 m (14 × 14), ROI1 ±7.875 m (42 × 42) | ROI2 5 × 5, ROI1 15 × 15 | fuera del `.m`; HIPÓTESIS |
| geolocalización | VNP03MOD | VNP03IMG / VJ103IMG / VJ203IMG | MxD03 (1 km) | P3 §0: ninguna fuente dice cuál usa MIROVA en MODIS; HIPÓTESIS |

**Queda IGUAL, y se declara como hipótesis** (son de VIIRS 750 y nadie ha dicho que valgan en otro sensor): NTI absoluto
−0,7 de noche, 10 y 5 sigma, mínimos 0,02 / 0,003 (NTI) y 0,01 / 0,003 (ETI), ventana de 3 × 3 **píxeles**, halo
k × k del fondo con k = 3, 5, 7 según cuántos alertados, piso de escena válida (mitad de NaN), TIR fría 200 K, sun-glint
12°. La radiancia saturada de VIIRS no se enmascara (el L1B la recorta, A37) y se cuenta.

**Variantes descriptivas** (no entran al veredicto): caja del mismo tamaño en **celdas** (7 × 7 y 21 × 21); caja física
con todo el ROI1 en umbrales de cumbre (N-3); en MODIS, banda 21 primaria (el histórico de D21) y geolocalización
interpolada de la grilla de 5 km (la de producción, `_interp_geo`).

## 3. Población y muestra (`01_poblacion.py`, `02_seleccion.py`, salidas al lado)

- Pasadas nocturnas de los 11 Tier A. VIIRS 375 del 2026-04-01 al 2026-10-21 (A119: por pasada desde abril); MODIS del
  2026-03-01 al 2026-10-21. Sin el 17 al 20 de octubre. Records de `data/mirova_equivalent` de `origin/main` 533398f8f
  (lo publicado, detector K); referencia remota de Mirova-v1 (consolidado `fe2d0a57`, OCR `4ddd5481`).
- Etiquetas: `scripts/banco_paridad.py::etiquetar` (±120 s) con la regla D-9 en modo SN (`clase_mirova`; en VIIRS 375 una
  alerta de 0,05 MW o menos cuenta como «MIROVA no vio nada»). Protegida = lectura A (≥ 1 MW). En VIIRS 375 las alertas
  sólo OCR antes del 2026-06-13 no deciden (A119) y quedan fuera del sorteo.
- Pasada partida (otro record nuestro del mismo volcán y plataforma a 7 min o menos): se marca y se informa aparte
  (MIROVA lista el gránulo sur y sólo alerta si el cráter está en él; `experiments/_s159/pareo_modis/verificador/INFORME.md`).
- Muestra (tope 300, coordinador), semilla 159, estratificada por volcán y cenit (≤ 40°, > 40°), peso N/n del estrato:

| sensor | pos_prot (alerta ≥ 1 MW) | pos_bajo (alerta < 1 MW) | neg_pub (K publica) | neg_resto (K no publica) | total |
|---|---|---|---|---|---|
| VIIRS 375 | 40 de 81 (las 3 que K no publica entran todas) | 45 de 952 | 20 de 134 | 45 de 3.348 | 150 |
| MODIS | 50 de 50 (censo) | 42 de 42 (censo) | 20 de 39 | 38 de 5.093 | 150 |

- **Control de VIIRS 750**: 10 pasadas del lote de N (incluidas Láscar 2026-10-08 05:42, Chillán 2026-10-10 05:54 y
  Villarrica 2026-09-19 05:48), peso 0.

## 4. Brazos y controles, que se miran ANTES de cualquier lectura

- **K**: lo publicado (record de `data/`, predicado del tablero con node). Se re-corre en el runner la función de
  producción del sensor sobre el mismo gránulo y se pasa por `store.append_record` en una carpeta temporal.
- **PORT**: §2, caja física. «Publica» = el MISMO predicado del tablero (node, `banco_paridad.correr_node`) aplicado a un
  **record sintético** (no hay record de producción para el port): `vrp_mw` = `primary_cluster.vrp_mw` =
  `f5_core_vrp_mw` = VRP del código (suma de todos los alertados de la ventana, como el `.m`), `distance_class` =
  «summit» si el centroide de los alertados está a `inner_radius_km` o menos del punto de referencia de MIROVA (X0, Y0),
  `t_max_k` = temperatura MIR del alertado más radiante. Es una aproximación declarada (el frente N usó la misma).

Controles (si fallan, la lectura no se hace):

1. **Cobertura (A108)**: pasadas con estado ok por sensor y clase; las que faltan, SIN DATO por pasada.
2. **Port sin red**: el envoltorio con la configuración de 750 da lo mismo que el oráculo de N en sus 391 grillas
   (`03_control_v750_sin_red.py`: 391 de 391 en npix y VRP, hecho antes de este commit) y la caja física es la de 750.
3. **CTL750 en el runner**: en las 10 pasadas de control, la cadena completa (bajada, lectura, grilla, port) reproduce
   npix y VRP del oráculo de N (a 1e-6 MW). Si no, la cadena nueva está rota.
4. **K reproduce lo publicado**: publica igual que el record de `data/` y `pc.vrp_mw` a 0,001 MW. Toda diferencia se
   lista; si pasa del 5 % de las pasadas, la lectura de K se hace sobre lo re-corrido y se dice.
5. **Control positivo del port**: alguna alerta protegida de Láscar o Chillán tiene que dar píxeles en el port. Si el
   port da 0 píxeles en todas, el instrumento está muerto en ese sensor (no «no reproduce»).

## 5. Qué cuenta como «reproduce» contra MIROVA (por sensor; las varas son las medidas en VIIRS 750 por N)

- **R1. Protegidas** (regla 1 de MISSION): protegidas que K publica y el port no. Si > 0: **PIERDE PROTEGIDA**.
- **R2. Detección**: recall ponderado de las alertas que deciden (protegidas y bajo 1 MW juntas y por separado). Vara:
  el oráculo en VIIRS 750 detectó 145 de 181 (0,80) y 71 de 78 protegidas (0,91). REPRODUCE si el IC 95 % (Wilson,
  sobre la muestra cruda; ponderado por bootstrap estratificado) contiene o supera la vara; NO REPRODUCE si queda entero
  bajo ella.
- **R3. Silencio**: publicación ponderada en negativos limpios. Vara: la de K en ese sensor (población: VIIRS 375 134 de
  3.482, MODIS 39 de 5.132, sin el 17 al 20 de octubre). REPRODUCE si el IC 95 % del port queda bajo la de K o la
  contiene; NO REPRODUCE si queda entero sobre ella. Se informa también contra el 0 de MIROVA.
- **R4. Magnitud**: razón VRP del port / VRP de MIROVA (máximo VRP de las alertas de la pasada) en las alertas que el
  port publica. REPRODUCE si la mediana está en [0,95; 1,05] y al menos 3 de cada 4 caen en [0,8; 1,25] (la banda que
  usó N; N midió 0,876); NO REPRODUCE si la mediana sale de [0,8; 1,25]; PARCIAL en medio. Las de un píxel se informan
  con su banda de triangulación (20 perturbaciones, cota inferior: O1 midió hasta 1,82 entre modelos de `fillmissing2`).
  La misma razón para K (lo que el tablero muestra) se informa al lado. Los cortes 0,95 / 1,05 y 3 de 4 son una
  **convención declarada**, tomada del 0,999 y el 0,876 de VIIRS 750, no una tolerancia elegida a gusto.
- **Veredicto MISSION del port como brazo contra K** (descriptivo, no adopción): `ΔE = (alertas bajo 1 MW perdidas −
  ganadas) + (negativos encendidos − apagados)`, ponderado, con IC 95 % por bootstrap estratificado por clase (2.000
  réplicas, semilla 159). PIERDE PROTEGIDA si R1 > 0; si no, GANA (ΔE < 0 con el IC entero bajo 0), ENCIENDE DE MÁS
  (IC entero sobre 0), EMPATE (ΔE = 0) o NO RESUELTO (el IC contiene 0).
- Estratos que se informan siempre: volcán, cenit, clase, partidas aparte, y en VIIRS 375 antes y después del 2026-06-13.

## 6. Lo que este pre-registro no hace

No adopta nada ni propone cambiar producción. No mide el día (sólo nocturnas). Agrandar el lote más allá de 300
pasadas es decisión de Nicolás. Un humo de pocas pasadas puede correrse antes del lote para probar la cadena; sus
resultados no se leen para el veredicto y entran al lote sólo si la cadena no cambió.
