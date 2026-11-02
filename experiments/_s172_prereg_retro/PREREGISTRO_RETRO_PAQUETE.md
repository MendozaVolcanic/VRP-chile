# Pre-registro: prueba retrospectiva del paquete de las tres vías «código MIROVA» en los 11 Tier A

Estado: **BORRADOR, RONDA 3, SIN SELLO; R-1 a R-15 contestadas «sí» (§12)** (hora del servidor de GitHub al empezar la ronda 3: 2026-11-02 12:52:40 GMT,
`gh api -i repos/MendozaVolcanic/VRP-chile`, cabecera `Date`). Ronda 1: un agente de S172 la escribió a pedido de la
coordinadora (hora del servidor al empezar: 2026-11-02 01:36:17 UTC) y la coordinadora la commiteó en `loop/activo`
como `experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md`, commit `01be21ff5` (01:42:57 UTC; sha256 del
archivo `45f48a93…`). Ronda 2: el mismo agente aplicó los cambios del verificador limpio
(`D:/vrp-trabajo/temporales/ver_s172_prereg_retro/INFORME.md`, Sonnet 5.5, SELLABLE CON CAMBIOS, VPR172-01 a 15;
hora del servidor al empezar la ronda 2: 2026-11-02 02:05:11 UTC; commit `18ab00217`, sha256 `aad33de7…`). Ronda 3: un
agente de S173 aplicó los 14 cambios del segundo verificador limpio (`experiments/_s173_aud/vpr/INFORME.md`, Fable 5.1,
SELLABLE CON CAMBIOS, VPR2-01 a VPR2-14, con su evidencia en esa misma carpeta); commit `bf13d7aa2`, sha256 LF
`62d8839b…`. Después, el mismo agente recalculó las cifras de F26 del §3 y del §7 con la referencia congelada (hora del
servidor: 2026-11-02 13:01:39 GMT; script y salida en esta carpeta): no cambia ningún conteo; cambian los cenit del §3.3
y el 317 del §5.1 (pasa a 315). Las tablas «hallazgo, tratamiento» de las dos verificaciones están en el §15.

Es el paso 1 del plan `docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md` (`loop/activo` `fa22f4b87`), Tarea 0.1.
No se corrió ningún brazo ni se miró ningún resultado de la vía. Sobre datos sólo se contó la referencia de MIROVA y K
de disco, para el poder. Las cifras de F26 del §3 y del §7 se recalcularon con la referencia congelada del §4.1
(`recalcular_s7_ref_congelada.py` y su salida, en esta carpeta) y dan lo mismo que con el snapshot de `origin/main`
que usó el segundo verificador; las de R25 salen del OSF y no dependen de la tabla (§7, «Con qué se contó»).

Rutas de repo relativas a `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\`. Commits citados:
`origin/main` = `14fb62030` (2026-11-01 23:34 UTC), `loop/activo` = `fa22f4b87` salvo que se diga otro.

---

## 0. En una pantalla (para Nicolás)

**Qué contesta.** Si el paquete (las tres vías encendidas a la vez, el mismo perfil que la sombra) se comporta como
MIROVA en pasadas que **ninguna regla usó para elegir sus parámetros**: febrero y marzo de 2026 contra la tabla de
MIROVA, y febrero a diciembre de 2025 contra el OSF v2.5. Algunas de esas pasadas sí se miraron por nombre en
diagnósticos (§3.1): se informan aparte, con y sin ellas.

**Lo que hay que saber antes de leer cualquier resultado.** Fuera de muestra, **las alertas protegidas son casi todas
de Láscar**: en la tabla congelada de febrero y marzo, 26 de 26 en VIIRS 375, 29 de 30 en VIIRS 750 (la otra es de
Isluga) y 9 de 9 en MODIS de febrero (§7). En 2025 el OSF trae algo más: en VIIRS 375, 44 protegidas de Puyehue-Cordón Caulle,
Planchón-Peteroa e Isluga, además de las 273 de Láscar. O sea:
- sobre **no perder alertas** la prueba habla de **Láscar**, y sólo en VIIRS 375 de 2025 de tres volcanes más;
- sobre **callar donde MIROVA calla** (negativos limpios) habla de **los 11**, porque hay noches limpias en todos.
Cada veredicto lleva escrito ese alcance (§8). La evidencia sobre recall en los volcanes de señal débil sigue siendo la
de dentro de muestra (MOD-D, V375-E, V750-B), rotulada como tal, y la de las sombras.

**Qué no contesta.** No prueba el sistema que va a publicar (LANCE, cortes de NASA, cron) ni el régimen sin Suomi NPP:
eso lo prueba sólo la sombra. No prueba nada en Chillán en erupción (toda su erupción está dentro de muestra). No dice
nada de los 34: sus grillas y sus vecinos (11 de los 34 tienen otro volcán dentro de la grilla, bitácora 2026-11-02
01:50) no están en los 11.

**Lo esperable en MODIS: SIN PODER.** En febrero K se equivoca en sólo 6 bloques noche-volcán; para que la vía «gane»
tendría que arreglar casi todos. Lo más probable es SIN PODER o EMPATE (§7). Eso **no posterga nada**: la paridad de
MODIS se sigue apoyando en MOD-D (dentro de muestra) y en su sombra y guardia.

**Para qué sirve, dado que ya aprobaste la sombra de los 34.** El 2026-11-02 dijiste «continúa con todo para que
avancemos más rápido» y la sombra de los 34 con las vías ya está preparada (bitácora 01:24 y 01:50). Esta prueba ya no
abre esa sombra: aporta, **por sensor**, a dos decisiones tuyas: con qué detector publicarían los 34 ese sensor y la
Compuerta B (§8.2).

**Cuándo y cuánto.** Después de V750-B (2026-11-03) y del merge de `roi_v750` (~11-04 a 11-06). Unas 185 a 220 h de
runner para la vía y 13 a 16 h para el control de K; pared de 34 a 41 h en cuatro despachos (§10). Lectura y
verificador hacia el **2026-11-10 a 11-12**.

**Lo que tienes que decidir** está en el §12.

---

## 1. Pregunta y unidad, como geólogo

**El fenómeno.** Un cráter activo de noche es una fracción mínima de un píxel de 375 m, 750 m o 1 km. MIROVA lo ve
interpolando el gránulo a una grilla fija, comparando cada celda con su entorno por NTI y ETI, midiendo el fondo bajo un
halo y sumando la radiancia de todas las celdas alertadas. Las tres vías hacen eso con el código de MIROVA, y dentro de
muestra se equivocan menos que K y miden la magnitud cerca de la de MIROVA (MOD-D: razón 0,983,
`experiments/_s168/modd_f4_candado/lectura_ab2/leer_f4_salida.txt` en `e0bb1b150`; V375-E: 0,9996,
`experiments/_s172_chillan/auditor/v375e_lectura_salida.txt`; port de V750 0,996 a 0,998 en Chillán, 0,996 sobre 22
alertas y 0,998 sobre 28, `experiments/_s172_chillan/verificador/INFORME.md` l. 28). El segundo verificador localizó
las tres citas (`leer_f4_salida.txt` l. 2 y 17, razón 0,9827; `v375e_lectura_salida.txt` l. 39; la de V750 corregida
de «0,994 a 0,998» a lo que dice la l. 28, VPR2-12); son cifras dentro de muestra y no se re-midieron.

**La sospecha que esta prueba busca refutar.** Los parámetros se eligieron mirando abril a octubre de 2026 (otoño,
invierno, primavera: cumbres nevadas, fondos fríos, gradiente topográfico fuerte, A69). Febrero y marzo son verano y
2025 trae las cuatro estaciones. Si las reglas se ajustaron a una estación, aquí se ve.

**Un límite físico que la prueba no puede saltar.** Un cráter brillante como el de Láscar lo ve casi cualquier
detector: el riesgo de perder una alerta está en los volcanes de señal débil (Isluga, Lastarria, Planchón-Peteroa,
Puyehue), y fuera de muestra casi no hay alertas suyas. Esta prueba puede refutar que la vía pierda lo evidente y que
publique de más en los 11; no puede probar que no pierda lo débil.

**La pregunta.** En febrero y marzo de 2026 y en 2025, por sensor: ¿el paquete (a) no pierde alertas protegidas que
MIROVA publicó (y en qué volcanes se pudo medir), (b) se equivoca menos que K, o igual, en lo débil (alertas bajo 1 MW
perdidas más publicaciones donde MIROVA calló), y (c) mide la magnitud como MIROVA, también cuando el satélite mira de
lado?

**Unidad.** La **pasada** (gránulo, volcán, sensor), donde se aplican las reglas y se parea con MIROVA a ±120 s. Y la
**noche-volcán** para lo que vive el operador (§5.5), que informa. Decide la pasada, porque así lo dicen las reglas y el
criterio de victoria (`docs/MISSION.md` l. 115: «por sensor y por tramo»).

---

## 2. Qué se prueba: el paquete y los brazos

| brazo | qué es | papel |
|---|---|---|
| **VIA** | `run_pipeline.py` con el perfil aislado `_s172_retro_paquete` (§10.1): K de producción con las tres vías encendidas y MxD03 apagado, en el commit del tag del despacho; `store.append_record` como en producción | lo que se mide |
| VIA-radiante, VIA-cercano, VIA-pico | el record de VIA con la distancia al cráter de cada regla de posición (`variante_posicion` de MOD-D fase 4; `distancias_desde_record` del lector de V375-E) | decide el que eligió cada regla (§5.1); los otros informan |
| **K** | los records de `data/mirova_equivalent/` en el tag del despacho, leídos de `origin/main` (no del checkout local, que está atrasado: A52, seguimiento S-1 del verificador) | control y vara de las reglas |
| **K-gemelo** | el código del tag con el perfil `_s172_retro_k` (vías apagadas), corrido en el runner sobre DM entero, Láscar y Chillán en F26 enteros y tres días de cada otro volcán en F26 (§10.3) | control: K de disco = K de hoy, y nulo entre runners |
| **PLACEBO** | el record de K con toda magnitud × 1,2 | programa §2, obligatorio |

**Por qué K de disco con control y no K re-corrido entero.** Correrlo entero suma ~180 h. Hay dos mediciones previas de
K re-corrido = publicado (V375-E 2.342 de 2.342; control `k_produccion` de MOD-D fase 4). Pero los records de K de F26
se escribieron con cuatro versiones de código (`3695f6758` 6.411; `57d18ad78` 429 y `c408a909e` 6, todos de Chillán;
`255e97e77` 10; `k_shas_por_volcan_salida.txt` del verificador): por eso el K-gemelo cubre Chillán en F26 entero y un
poco de cada volcán. Si falla, K de disco no sirve (§6, C-K).

**Por qué el paquete entero.** Es lo que corre la sombra y lo que se publicaría. Cada vía cambia sólo el procesador de
su sensor (comentario de `pipeline/profiles/sombra_codigo_mirova.yaml`), así que el veredicto se lee por sensor.

---

## 3. Población por tramo y qué está dentro de muestra

### 3.1 Inventario de exposiciones (corrige la ronda 1: «ninguna regla lo miró» era falso para los diagnósticos)

Tres tipos de exposición, de más a menos grave:

**(a) Ventana de selección de parámetros** (alguien eligió un umbral, una caja, una ROI o una posición mirando esas
pasadas). Medir ahí reproduce.

| regla | ventana | evidencia (verificada por el verificador, V-1a) |
|---|---|---|
| K (#848) | V1 2026-08-29 a 10-08; V2 2026-03-01 a 06-12, VIIRS decide desde 04-01 | `experiments/_s151_prereg_fk_11/PREREGISTRO.md` l. 90 a 102 |
| MOD-D censo | 2026-03-01 a 10-16 | `experiments/_s162_modis_paquete/PREREGISTRO.md` l. 56 a 58 |
| MOD-D fase 4 (sellado) | C 2026-03-01 a 10-16; E 10-17 a 10-26 | `experiments/_s166_modd_f4/PREREGISTRO_MODD_F4.md` l. 92 a 121, tag `s168-modd-f4-sellado` |
| V375-E (sellado) y caja C13 | 2026-04-01 a 10-21 sin el 12, 13 y 17 a 20 de octubre | `experiments/_s162_v375/PREREGISTRO_E.md` l. 70 y 550 a 556, tag `s170-v375e-lector` |
| V750-B (sellado; elige la ROI) | T 2026-04-01 a 06-12; O 06-13 a 11-02 12:59 UTC | `experiments/_s162_v750b/PREREGISTRO_V750B.md` l. 97 a 106, tag `s167-v750b-adenda3-sellada` |
| V750-A (borrador) | la de V750-B | `experiments/_s162_v750a/PREREGISTRO_V750A.md` l. 130 a 137, `aa5583646` |
| Regla de posición (S165) | ventana O | `experiments/_s165_regla_posicion/INFORME.md` |
| D25 (S143, S157; no se adopta, S162) | 2026-06-01 a 08-31 y 09-01 a 09-15 (S143); 2026-04-01 a 06-12 y 08-29 a 10-08 (S157) | `docs/PREREGISTRO_AB_D22_D25_S143.md` l. 89 y 91; `experiments/_s157_prereg_d25/PREREGISTRO.md` (verificado por el segundo verificador, VPR2-10) |

Ninguna toca febrero de 2026 ni 2025 (el segundo verificador lo comprobó línea a línea en cada pre-registro citado,
`experiments/_s173_aud/vpr/INFORME.md` §5, eje 1). Marzo de 2026 lo tocan MOD-D y la V2 de K (control), sólo en
MODIS: la V2 de K deja decidir a VIIRS desde el 04-01 (`_s151_prereg_fk_11/PREREGISTRO.md` l. 99 a 102;
`experiments/_s153_fk_v2/v2.log` l. 15).

**(b) Pasadas miradas por nombre en diagnósticos** (no eligieron parámetros, pero motivaron o probaron las vías):
- MODIS, Láscar: 2026-02-11 01:20 Terra (bajo 1 MW), 2026-02-11 07:00 Aqua (bajo 1 MW) y **2026-02-16 01:20 Terra
  (protegida)**. Son las tres de febrero en que K no publica una alerta
  (`experiments/_s159/mxd03_prereg/sustrato_mirova_modis_feb_salida.txt` l. 27 a 29; la de 02-11 07:00 es el control
  positivo del etiquetado de MxD03 y de la sonda M, `experiments/_s159/m/INFORME.md` l. 52 y 58; la de 02-16 es el caso
  de `experiments/_s158_audit_r2/verificador/va/INFORME.md` l. 37); la cuarta es un negativo que K publica:
- MODIS, **Lastarria 2026-02-24 07:05 Aqua** (negativo limpio que K publica con 0,529 MW; mirada por la sonda M,
  `experiments/_s159/m/INFORME.md` l. 49; es uno de los cinco bloques de F26-M en que K publica un negativo,
  `experiments/_s173_aud/vpr/contar_f26_F26M_bloques_modis.txt`; VPR2-01).
- VIIRS 750: los ceros de K de febrero que S158 RA1 listó por nombre (Láscar 02-04, 02-05, 02-12, 02-21, 02-25, 02-26;
  Isluga 02-26; Puyehue-Cordón Caulle 02-01; Tupungatito 02-26) y Láscar 2026-03-11 06:18
  (`experiments/_s158_audit_r2/ra1/contar_ceros_v750.txt`).
- 2025 (contra el OSF): Llaima 2025-02-15 03:15 (1,243 MW), Láscar 2025-03-17 06:25, 2025-05-23 07:25 y 2025-06-02
  07:20, Cordón Caulle 2025-08-03 06:35 (MODIS, sonda M, `experiments/_s159/m/INFORME.md` l. 50, 51 y 78); Láscar VIIRS
  750 2025-07-07 05:24 (CM162, `experiments/_s162_vuelta2/CUMULOS_POR_MATRIZ.md` l. 15); Chillán 2025-11-04 06:00
  (auditor de S172, `experiments/_s172_chillan/auditor/INFORME.md` l. 153). Fuente del inventario:
  `experiments/_s173_aud/vpr/pasadas_2025_nombradas.txt` y `febrero_pasadas_nombradas.txt` (VPR2-01).

**(c) Diagnósticos de K contra la referencia sobre todo un tramo** (sin nombre por pasada): S158 RA1 sobre VIIRS 750 del
2025-02-15 al 2026-10-21; A99, pareo de magnitud de K contra el OSF de 2025 (342 pares); el auditor de Chillán S172
sobre el OSF de 2025 (`s04`); la calibración de `WOOSTER_COEFF` de S14 sobre todo el OSF chileno (ver §4.3: no ajusta
nada a nuestras detecciones).

**Cómo entra al análisis.** La vía de 750 es un port literal del `.m` de MIROVA y las de MODIS y 375 trasladan su
estructura: ninguna se ajustó a (b) ni a (c), así que el sesgo de selección es débil (SOSPECHA, no medido). Pero en
MODIS de febrero el contraste vía contra K descansa justamente en esas cuatro pasadas. Por eso el lector informa P1, P2
y M de F26-M y de F26-V (750) **con y sin** las pasadas de (b), y P1-OSF y la magnitud de R25 con y sin las de 2025; si
el veredicto cambia al sacarlas, el sensor va a DECIDE NICOLÁS (§8, fila 4).

### 3.2 Tramos

| tramo | fechas (UTC, pasadas nocturnas) | volcán-día | rol |
|---|---|---|---|
| **F26-V** | 2026-02-01 a 03-31, VIIRS 375 y 750; Tupungatito desde 02-23 | 627 | **decide** |
| **F26-M** | 2026-02-01 a 02-28, MODIS; Tupungatito desde 02-23 | 286 | **decide** |
| F26-M3 | 2026-03-01 a 03-31, MODIS | 341 | control (tramo C de MOD-D) |
| **R25** | 2025-02-15 a 12-31, los tres sensores, 10 volcanes (sin Tupungatito: 0 filas en el OSF) | 3.200 | **decide sólo P1-OSF; magnitud informa** |
| DM | 2026-10-01 a 10-16 (VIIRS sin el 12 ni el 13) | 176 | **control de montaje**, no evidencia |
| enero de 2026 | | 0 | fuera (A119) |

Restricciones:
- **Tupungatito**: la tabla no lo tiene antes del 2026-02-14 y hasta el 02-23 el scraper rotulaba con 5 km y no 7
  (hitos de `scripts/calidad_referencia_mirova.py`). En R25, **SIN DATO** y no se despacha.
- **NOAA-21**: 895 de 895 pasadas de 375 y 889 de 889 de 750 en F26 quedan `sin_info` (tabla congelada y snapshot de
  `origin/main`, iguales; `experiments/_s172_prereg_retro/recalcular_s7_ref_congelada_salida.txt`); la primera etiquetada en la tabla
  es del **2026-04-03** (medido por el verificador; el hito del script dice 04-09 con una cifra «no reconstruida», S-6).
  El OSF no trae NOAA-21 en ningún año (códigos 3 y 4 = VIIRS, 4 desde 2018; 1 y 2 = MODIS; verificación empírica).
  Sus pasadas no entran a nada que decida; en R25 sólo cuestan (S-2), y no se pueden saltar sin tocar el código.
- **Sólo noche**, como todos los pre-registros de las vías. El día es #813.

### 3.3 Composición de F26-V y desviación declarada de A119(b)

**Desviación.** A119(b) (`scripts/calidad_referencia_mirova.py` l. 27) dice que una tasa por pasada de VIIRS anterior a
abril no es comparable con una posterior, y K decidió VIIRS sólo desde el 2026-04-01
(`_s151_prereg_fk_11/PREREGISTRO.md` l. 100). Esta prueba **sí hace decidir a VIIRS de febrero y marzo**, porque es el
único tramo de VIIRS fuera de la selección de parámetros con negativos limpios. Lo que se compara es vía contra K sobre
las mismas pasadas, nunca una tasa de F26 contra una de abril en adelante.

**Composición medida** con las reglas de este documento (tabla sola, noche por elevación solar, SN, Tupungatito desde el
02-23) y la **tabla congelada** del §4.1 (`experiments/_s172_prereg_retro/recalcular_s7_ref_congelada_salida.txt`; con el snapshot de `origin/main` da lo mismo, igual que
`experiments/_s173_aud/vpr/contar_f26_F26_salida.txt` del segundo verificador, VPR2-11). «Etiquetada» = la pasada
tiene fila de la tabla (cualquier etiqueta salvo `sin_info`); cenit = mediana de `sensor_zenith_deg` del record de K:
- VIIRS 375: 1.708 de 2.660 records (64 %) sin fila. NOAA-20, 790 etiquetadas (cenit 47,7°) y 111 sin fila (54,8°);
  Suomi NPP, sólo 162 etiquetadas, con cenit **63,1°**, y 702 sin fila (44,3°); NOAA-21, 895 sin fila (47,2°).
- VIIRS 750: NOAA-20, 844 etiquetadas (48,7°) y 49 sin fila (24,9°); Suomi NPP, 198 etiquetadas (62,6°) y 656 sin
  fila (42,5°); NOAA-21, 889 sin fila (47,3°).

La ronda 3 traía los cenit del primer verificador (NOAA-20 375 etiquetadas 47,4°; Suomi NPP 375 sin fila 44,9°; Suomi
NPP 750 sin fila 42,6°); los de arriba los reemplazan.
O sea: **la evidencia de F26-V es NOAA-20 y las pasadas oblicuas de Suomi NPP**. Todo resultado de F26-V va rotulado así,
y la curva de cenit de F26-V se lee por satélite.

**Por qué igual no sesga el contraste.** La tabla decide qué pasadas exponer sin mirar lo que publicamos; la selección
baja el denominador y cambia la mezcla de cenit, pero afecta a la vía y a K por igual en cada pasada. Sí puede afectar a
la lectura de la noche (una pasada con alerta que la tabla no expone deja a las otras de esa noche como limpias): por eso
la noche limpia del §5.5 exige que todas nuestras pasadas de la noche tengan fila.

**Régimen.** F26 y R25 son anteriores a #535 y a K, pero los dos brazos se calculan hoy con un mismo código. K de disco
se escribió con el reproceso #883 (octubre), ya con #535 y K. Se lee **por tramo** porque cambia la referencia.

---

## 4. La referencia por tramo y su calidad

### 4.1 F26: la tabla de MIROVA, sola

- **Decide la tabla sola** (`calidad_referencia_mirova.etiqueta_que_decide`). El OCR está en su peor tramo: una protegida
  sólo del OCR **no veta**; se lista con la cabecera de la imagen revisada (A61) y, si la vía la pierde y K la publica,
  el sensor va a DECIDE NICOLÁS (como MOD-D fase 4 §5 y §7 fila 5). N-3 queda subsumida.
- Cobertura de la tabla: 98,2 a 99,6 % de las noches en febrero; 99 a 100 % desde marzo.
- **Referencia congelada** por sha256 antes del despacho: la unión que carga
  `scripts/referencia_mirova_unificada.cargar_referencia_unificada`. Recomendación: la de MOD-D fase 4 (consolidado
  `cb91eb506c37cff0b83164dd602d8a5340277637`, OCR `cfc57c4d8bc57c5ccd5219ff3a91749dae167b97`,
  `PREREGISTRO_MODD_F4.md` l. 124 a 128); si se toma otra, se listan las filas de F26 que cambian.
- **Etiquetas** de `banco_paridad` y `scripts/clase_mirova.py`, sin cambio: `protegida` (lectura A; `docs/MISSION.md`
  l. 92 a 113), `bajo1`, `neg_limpio`, `far_ref`, `sin_info`. Los recálculos se hacen sobre un `git archive` de
  `origin/main`, no sobre el checkout local.
- **Regla D-9 (SN)** en VIIRS 375 (`docs/MISSION.md` l. 119 a 131): decide SN; se informan SE, la regla original y el
  umbral 0,04.

### 4.2 R25: el OSF v2.5 de MIROVA

**Qué es (A105).** Base reprocesada y filtrada (clase DBSCAN y umbrales de VRP por sensor; Coppola et al. 2026, Tabla 1
p. 8 y p. 7). Sirve para sus alertas y su magnitud; **no para contar publicaciones de más**. En R25 no hay negativos
limpios ni P2.

Hechos (archivo local `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv`, fuera de git, sha256
`0863c2407eadd09722ccd98fd50c48eefdc871a4b68f843bd8478f94f5eb29da`; trae 2001 a 2025; reproducido por el verificador):
- 2.577 filas chilenas del 2025-02-15 al 2025-12-31, de 10 volcanes (Tupungatito 0).
- **Piso de VRP por sensor**: 0,011 MW en 375 m, 0,176 MW en 1 km y **5,05 MW en 750 m** (globales 2025: 0,010 / 0,101 /
  5,003). En 750 el OSF sólo trae pasadas de 5 MW o más.
- `timeUTC` truncado al minuto; con K todas las pasadas pareadas dan Δt = 0 s.
- `Dayflag` 0 es noche en 2.524 de 2.528 filas y 1 es día en 49 de 49 según la elevación solar del proyecto (horas UTC
  de las filas 0 entre 01 y 20; las cuatro diurnas con 0 son MODIS, tres de 1 MW o más: Chaitén 2025-05-14 20:10, 1,27
  MW; Copahue 2025-08-13 12:40, 1,53 MW; Villarrica 2025-03-26 13:55, 14,39 MW; la cuarta, Villarrica 2025-04-07 13:35,
  0,99 MW; `experiments/_s173_aud/vpr/contar_osf_vent_salida.txt`, VPR2-05). Verificación empírica; la
  definición del paper sigue SIN VERIFICAR. **Se usa la noche del proyecto (elevación solar), no `Dayflag`.**
- Columnas (esquema v2.5, `experiments/_s172_chillan/auditor/schema_osf_v25_texto.txt`): `VRP` en watts; `LAT`/`LON`
  del píxel más caliente; `Max_Dist` al píxel alertado más lejano, en metros; `class` 1 volcánica, 0 no, «a screening
  indicator rather than a definitive label» (l. 62); `SatZen` cenit.

Ninguna columna se usa sin leer antes su definición en Coppola et al. 2026 renderizado (A95); faltan `Dayflag` y la
tabla de `Satellite`, que esta prueba ya no necesita para decidir.

**Definiciones de R25:**
- **Pareo**: misma resolución, ±120 s, mismo volcán.
- **Protegida OSF**: fila nocturna (elevación solar), `class` 1, `VRP` ≥ 1e6 W, píxel más caliente a no más de
  `inner_radius_km` del cráter de `volcanoes.yaml` (decisión R-1). **317 en 375 m** (273 Láscar, 28 PCC, 14
  Planchón-Peteroa, 2 Isluga), **17 en 750 m** (todas Láscar, todas de 5 MW o más), **161 en 1 km** (155 Láscar, 6
  Planchón-Peteroa). La fila de Villarrica que la ronda 2 contaba (2025-03-26 13:55, 14,39 MW, `Dayflag` 0) es diurna
  con la noche del proyecto y no entra (VPR2-05; `experiments/_s173_aud/vpr/contar_osf_vent_salida.txt`, igual con el
  centro en `contar_osf_centro_salida.txt`).
- **K ya las publica todas**: 317 de 317, 17 de 17 y 160 de 161 con record (una MODIS sin record de K a ±120 s; misma
  salida). P1-OSF es por eso un control de **«la vía no pierde las evidentes»**, no de recall en volcanes débiles (S-3).
- **Bajo 1 MW OSF** (sólo 375 y 1 km): informa, con SN por analogía en 375.
- **Lejana OSF** (análogo de `far_ref`, corrige la ronda 1): filas `class` 1 de 1 MW o más **fuera** del radio interno.
  Son 49, todas de Chillán entre el 2025-02-15 y el 03-05, a 12,1 a 19,6 km del cráter, mediana 17 MW
  (`osf_class0_salida.txt`). Si la vía las publica como cumbre, se informa como E_lejana (no decide). Importa porque la
  vía suma toda la grilla: el calor lejano puede quedar en la magnitud de la cumbre (el mismo hallazgo de los vecinos de
  los 34, en pequeño).
- **Ambiguas**: las 13 filas `class` 0 de 1 MW o más **dentro** del radio (9 Láscar, 4 Puyehue) se listan aparte, sin
  decidir; las 92 de fuera del radio se cuentan.

### 4.3 Independencia de la razón contra el OSF y su truncamiento

**Independencia.** La vía de 750 usa el coeficiente del `.m` (1,97e7 × 0,5625 km²); las de MODIS y 375 los de S14
(`pipeline/mirova_v750_codigo.py` l. 70 a 85, `origin/main`). S14 no los ajustó a nuestras detecciones: son la constante
k·A de MIROVA, recuperada de `VRP / ΔL` del OSF, constante por resolución con cv del orden de 1e-8
(`osf_k_constante_salida.txt`). La razón vía/OSF no está contaminada por esa calibración.

**Truncamiento.** Una razón calculada sólo sobre las filas que el OSF conserva selecciona por el denominador (un VRP de
MIROVA alto por azar da razón baja), y más en 750, donde todo es de 5 MW o más. Por eso **la razón de R25 se lee sólo
como cota, no decide en ningún sensor y no se compara con la de F26**.

---

## 5. Lecturas y criterios

Todo por pasada nocturna. «Publica» y «magnitud mostrada» = el predicado de `frontend/index.html` del tag, ejecutado con
node sobre el record de `store.append_record` (`banco_paridad.correr_node`, A97). Bloque = noche-volcán.

### 5.1 Lectura A: la regla de adopción de cada sensor, fuera de la selección de parámetros (decide)

| sensor | regla | tramo que decide | brazo de posición que decide |
|---|---|---|---|
| MODIS | §7 de `PREREGISTRO_MODD_F4.md` (l. 209 a 241, tag `s168-modd-f4-sellado`): P1, P1b, P2, P2', M | F26-M | VIA-radiante (lo eligió MOD-D: «posición: V (ninguno gana contra V)», `leer_f4_salida.txt`) |
| VIIRS 375 | §5.4 (a) a (d) de `PREREGISTRO_E.md` (l. 134 a 151, tag `s170-v375e-lector`) con N-3 (§8.13, l. 503) y el código del §9.7 | F26-V | **VIA-cercano** («cercano decide», §10, l. 703 a 714). Además, **VIA-radiante con la misma regla, al lado**: el record de la vía publica hoy con radiante (l. 716), así que un veredicto de cercano no describe lo que publicaría el paquete tal como está. Si los dos difieren en el veredicto, el techo de VIIRS 375 es DECIDE NICOLÁS |
| VIIRS 750 | §6 punto 2 de `PREREGISTRO_V750A.md` con §6 bis y §6 ter, **sólo si V750-A está sellado con su verificador limpio antes del despacho D2** (§10.3). Si no, se aplica como anexo **no verificado** el texto de `aa5583646:experiments/_s162_v750a/PREREGISTRO_V750A.md` §6 (l. 217 a 243), §6 bis (l. 174 a 196) y §6 ter (l. 197 a 216), y el techo de VIIRS 750 es DECIDE NICOLÁS. Si V750-A se sella en otro commit, se lista el diff de esas tres secciones contra `aa5583646` antes de D2 (VPR2-07). Este documento no sella el texto de V750-A | F26-V | el que elija el §6 bis de V750-A en su censo; si no ha corrido, VIA-radiante, y los otros dos informan |

Las diferencias con cada regla sellada están todas en la tabla del §5.6 (ninguna cambia un umbral).

Particularidades:
- **F26 decide con la tabla sola** en los tres. La rama «tabla más OCR» que pide V750-A §6.2 se calcula e informa; una
  pérdida sólo OCR va a DECIDE NICOLÁS.
- **V375-E §5.4 (d)** se lee con los controles de su §4. Si F26-V no tiene 8 noches con pares, (d) es SIN SUSTRATO y se
  informa (hay 315 noches-volcán con dos o más pasadas etiquetadas en 375, con la tabla congelada y la definición
  de «etiquetada» del §3.3, `experiments/_s172_prereg_retro/recalcular_s7_ref_congelada_salida.txt`; la ronda 3 decía 317, del primer verificador; pero las publicadas por los dos brazos con
  alerta son muchas menos).
- **V750-A §6.2 M** (banda [0,9; 1,1]) decide en F26-V si V750-A está sellado; son unas 30 pasadas de Láscar y se dice.
- **R25** aporta P1-OSF (§5.2) y la magnitud como cota (§4.3).

### 5.2 P1-OSF en R25

Para cada protegida OSF: la vía no y K sí, **candidata a veto**: se diagnostica con el record y la imagen si existe;
**no veta sola**, lleva el sensor a DECIDE NICOLÁS. Ni la vía ni K: se lista. La vía sí y K no: no puede ocurrir (K
publica todas), y si ocurre es un defecto del lector. Recall de la vía por sensor, **por volcán y sin Láscar** (44
protegidas no Láscar en 375, 6 en 1 km, 0 en 750).

### 5.3 Magnitud partida por cenit (informa; en F26 es además la M de cada regla)

**Por qué.** Medido en Chillán: la razón de K contra MIROVA cae con el cenit en los tres sensores (Spearman −0,87 MODIS
n 12, −0,50 VIIRS 375 n 53, −0,81 VIIRS 750 n 39, fuera del barajado; cerca del nadir 0,75 / 0,74 / 0,85, sobre 60°
0,08 / 0,33 / 0,11; réplica del 27-oct al 1-nov; `experiments/_s172_chillan/auditor/INFORME.md` §2 y
`verificador/INFORME.md` §2). Las vías llevan Chillán cerca de 1 (dentro de muestra). MIROVA también cae con el cenit
(en 750, 0,503 de la pasada más oblicua sobre la menos oblicua; programa §1 punto 6): **la meta es caer como MIROVA**.

**Qué se mide, por sensor y tramo, y en F26-V además por satélite (§3.3):**
1. Razón vía/MIROVA y K/MIROVA por pasada pareada (los dos publican, VRP mayor que 0): mediana con IC por bootstrap de
   noches, por tramo de 10° de cenit y por volcán. En R25, sólo cota (§4.3), con el control C-cenit contra `SatZen`.
2. Spearman de la razón contra el cenit con 200 barajados dentro del sensor (semilla 172; instrumento de `s03_estratos.py`).
3. Razón doble dentro de la noche con el veredicto de V375-E §5.3 aplicado a los tres sensores, con sus seis nombres y
   en este orden: SIN SUSTRATO con menos de 8 noches en la lectura o en el nulo; NULO SESGADO si el nulo no contiene 1;
   CAE MÁS QUE MIROVA si el IC de la mediana queda entero bajo 1; CAE MENOS si queda entero sobre 1; REPRODUCE LA CURVA
   si lo contiene y la mediana está en [0,8; 1,25]; NO RESUELTO en otro caso (`s170-v375e-lector:
   experiments/_s162_v375/PREREGISTRO_E.md` §5.3; extracto en `experiments/_s173_aud/vpr/cita_v375e_s53.txt`; VPR2-13).
   En V375-E la curva retrospectiva sólo informa (§9.7, fila (d)); aquí CAE MÁS QUE MIROVA lleva a DECIDE NICOLÁS (§8.1
   fila 4): desviación conservadora, declarada en el §5.6.
- **Límite**: Chillán no erupcionaba en F26 ni en R25; la curva fuera de muestra es sobre todo la de Láscar.

### 5.4 Lectura B: paridad absoluta contra MIROVA (informa)

Por sensor, tramo **y volcán**, de la vía y de K, con numerador, denominador y ventana: recall de protegidas (con la
lista de perdidas), recall bajo 1 MW (F26, SN), tasa en negativos limpios con cota de Wilson (F26), razón de magnitud.
Una fila por volcán aunque tenga ceros: el cero se ve.

No decide porque no hay un umbral absoluto de «igual a MIROVA» que salga de los datos de MIROVA (MISSION punto 4, A115).
Recomendación de lectura (R-6): «a la par de MIROVA en ese sensor y esos volcanes» sólo si la vía no pierde ninguna
protegida que K publica, su tasa en negativos limpios no supera la de K (cotas solapadas o menor) y su razón cumple
[0,8; 1,25] (V375-E §5.3, el único número sellado de «se parece a MIROVA» en magnitud).

### 5.5 La noche del operador (informa)

- Noche protegida: noche-volcán con alguna protegida de MIROVA en algún sensor. ¿El tablero publica algo esa noche?
- Noche limpia: noche-volcán en que **todas** nuestras pasadas tienen fila de la tabla y todas sus filas son RUTINA (con
  SN). ¿El tablero calla?
- Vía contra K sobre las mismas pasadas (mismo número de oportunidades, GUIA §3b fila 12).

### 5.6 Qué cambia respecto de las reglas selladas (todo lo demás se conserva tal cual)

| pieza | regla sellada | aquí | por qué |
|---|---|---|---|
| población | muestra con pesos (V375-E §9.2, `N_h / n_ok_h`); censo con identidad (MOD-D) | censo de las pasadas nocturnas con fila; pesos 1 | se corre todo el tramo. Efecto declarado: con censo crece B, y el corte «4 bloques o menos = SIN SUSTRATO» decide en menos casos |
| ventana | la de cada pre-registro | F26 y R25 | es la pregunta |
| canal en F26 | V750-A: tabla y tabla más OCR | decide la tabla; la rama con OCR informa y una pérdida sólo OCR va a DECIDE NICOLÁS | A119; como MOD-D fase 4 §5 |
| VIIRS desde abril (A119 b, K) | VIIRS decide desde el 04-01 | VIIRS decide en febrero y marzo, sólo vía contra K | §3.3; desviación declarada |
| identidad de punta a punta (MOD-D §8.2) | V contra las grillas del censo en 5.321 pasadas | no se calcula en F26 ni R25 (no hay grillas guardadas); se reemplaza por C-montaje en DM | en F26 y R25 una vía distinta del port sólo se vería si cambia lo que publica; se declara |
| tramo E de MOD-D | protocolo propio | no aplica | no hay cola |
| SIN SUSTRATO (MOD-D fila 4) | INDECIDIBLE | SIN PODER FUERA DE MUESTRA, sólo si no se cumple ninguna condición de DECIDE NICOLÁS (§8) | nombre más preciso; el orden de las filas corrige VPR172-03 |
| C-via (MOD-D §8.6) | cualquier record sin la marca: rojo | en F26 y DM: igual, rojo; en R25: el record sin marca sale de los dos brazos a SIN DATO, con veto si es protegida que K publica y rojo sobre 10 % por clase | en 2025 la disponibilidad de MxD03 es SIN DATO; un rojo por un día sin MxD03 perdería todo R25 (§6) |
| V375-E §5.4 | retrospectiva **y** sombra | sólo la parte retrospectiva | la sombra la lee su propio lector; este veredicto no la reemplaza |
| posición en VIIRS 375 | cercano decide (sombra) | cercano decide y radiante se informa con la misma regla; si difieren, techo DECIDE NICOLÁS | VPR172-08 |
| V750-A | borrador | se aplica sólo si está sellado con verificador antes de D2; si no, techo DECIDE NICOLÁS | VPR172-06 |
| pasadas de §3.1 (b) | (no existía) | se informa con y sin ellas; si el veredicto cambia, DECIDE NICOLÁS | VPR172-02, VPR2-01 |
| SIN SUSTRATO de P2 en VIIRS 375 | V375-E §9.7 (b): CUMPLE | SIN PODER FUERA DE MUESTRA (fila 5 del §8.1) | el mismo nombre para los tres sensores; VPR2-02 |
| SIN SUSTRATO y BLOQUEA de P2 en VIIRS 750 | V750-A §6.2 pide «GANA o EMPATE (no PIERDE ni BLOQUEA)» y no nombra SIN SUSTRATO | se leen como en D-45 (`regla_signos_p2` de `evaluar_d25` blob `1dbabf65`): SIN SUSTRATO va a la fila 5 y BLOQUEA a la fila 4 | la regla de V750-A no dice qué hacer; VPR2-02 |
| curva de cenit CAE MÁS en la retrospectiva | informa (V375-E §9.7, fila (d)) | DECIDE NICOLÁS (§8.1 fila 4) | conservador: una caída peor que la de MIROVA no queda escondida; VPR2-13 |
| Tupungatito y NOAA-21 | en la población | Tupungatito desde el 2026-02-23 y fuera de R25; NOAA-21 `sin_info` | la referencia no los cubre |

---

## 6. Controles (si uno cae, no se lee el veredicto de ese sensor)

| control | qué tiene que dar | si falla |
|---|---|---|
| **C-via** | F26 y DM: 100 % de los records de VIA con `via_codigo_mirova` True, como MOD-D §8.6. R25: un record sin la marca (`sin_grilla`, `sin_mxd03`, `geo_distinta`) sale **de los dos brazos** a SIN DATO y se lista; si es una protegida OSF que K publica, **es candidata a veto (fila 4 del §8.1: DECIDE NICOLÁS, como toda candidata OSF)**; más de 10 % SIN DATO en una clase cae (el `UMBRAL_COBERTURA` de `leer_sombra_v375e.py` l. 85) | INDECIDIBLE en ese sensor y tramo; se arregla y se repite el trozo |
| **C-cobertura** (A108) | pasadas de VIA contra K por volcán, día y sensor, antes de mirar nada. Las que faltan en VIA por la regla de cobertura de la vía (`mirova_v750_codigo.py` l. 798 a 808: menos de 100 píxeles a 45 km o el más cercano a más de 5 km; hallazgo 171-01, descarte sin record) van a SIN DATO en los dos brazos. Una protegida SIN DATO que K publica: en F26 (tabla), fila 2 del §8.1 (NO SE SOSTIENE), como `leer_sombra_v375e.py` l. 573 del tag `s170-v375e-lector` (l. 612 en `s172-v375e-lector-resellado`); en R25 (OSF), candidata a veto, fila 4 (DECIDE NICOLÁS); VPR2-03. Más de 10 % SIN DATO en una clase que decide, cae. Toda alerta o bajo 1 MW de la tabla sin pasada nuestra a ±120 s se lista | trozo cortado por NASA (A64): se repite una vez con la misma ventana; un trozo que falla dos veces deja sus pasadas en SIN DATO, en la primera línea del resultado, y cuentan para el 10 % |
| **C-K** | K-gemelo contra K de disco en DM, Láscar y Chillán en F26 y tres días de cada otro volcán en F26: **misma publicación en todas las pasadas** y `pc.vrp_mw` a 0,001 MW, salvo pasadas nombradas con su causa escrita antes de leer F26: **a lo más 3 por sensor** (tope de R-15), cada una con el empate de `argsort` entre CPU (S152) mostrado en el record; si hacen falta más, C-K cae (VPR2-06). Sin tolerancia porcentual: el 1 % es del tamaño del efecto (en F26-V de 375, 1 % de 2.660 records son unas 27 pasadas contra los 48 bloques donde K yerra, §7; VPR2-12) | K de disco no sirve: INDECIDIBLE hasta correr K entero con el código del tag |
| **C-montaje** | en DM la vía reproduce, pasada por pasada, lo que midieron los A/B donde el código es el mismo: V de MOD-D fase 4 (máscara, VRP a 0,001 MW, clase), la vía de V375-E (lectura lejana) y el brazo de V750-B con la ROI elegida (banda de triangulación de V750-A §4.1). Antes de correr se lista `git diff` del código de la vía entre cada tag y el del despacho y se escriben las diferencias esperadas. **Una diferencia está explicada sólo si** (a) un hunk listado de ese `git diff` la reproduce al re-correr esa pasada con el código del tag de origen, o (b) la pasada cambia de gránulo (`otro_granulo`); nada más cuenta como explicación (VPR2-09). En DM, K de disco no publica tres protegidas de la tabla (Nevados de Chillán MODIS 2026-10-12 07:20, 2,18 MW, y 2026-10-15 01:05, 1,72 MW; Puyehue-Cordón Caulle VIIRS 750 NOAA-21 2026-10-10 05:54, 1,19 MW; `experiments/_s173_aud/vpr/contar_f26_DM_salida.txt` l. 12, 13 y 38; seguimiento S-A del segundo verificador): DM no se lee como «K publica todas» | cada diferencia se explica con (a) o (b) antes de leer F26 y R25; una no explicada deja todo INDECIDIBLE |
| **C-pareo** | Δt de los pares de R25 dentro de ±120 s y ninguna protegida OSF pareada a dos pasadas | se revisa el pareo; la ventana no se ensancha |
| **C-cenit** | en R25, \|cenit nuestro − `SatZen`\| ≤ 2° | la curva de R25 no se lee |
| **PLACEBO** | K × 1,2: P1 y P2 sin discordancias salvo las que explican los filtros del tablero que miran la magnitud (nota L7 de V750-A §7); en MODIS y VIIRS 375, M **la de D-28** (MEJORA sólo si d **y** d′ dan MEJORA, con `comparar_con_ganancia`) no da MEJORA; en VIIRS 750, el comparador de V750-A §6.2 separa la vía de K × 1,2. Con d sola el placebo puede dar MEJORA legítima cuando K está bajo MIROVA (con K/MIROVA 0,65, K × 1,2 = 0,78 da d = −0,079), por eso no se usa d sola (`experiments/_s157_prereg_d25/ADENDA_PLACEBO.md` l. 15 y 55; VPR2-04) | instrumento roto |
| **Nulo de runner** | K-gemelo contra K de disco: **B = 0** en P2 salvo las pasadas nombradas de C-K (con su mismo tope de 3 por sensor, R-15). «SIN SUSTRATO» o «EMPATE» no bastan: los da también un instrumento muerto. Control de que el nulo puede fallar: el mismo cálculo sobre K-gemelo contra PLACEBO tiene que dar B mayor que 0 o M distinta | idem |
| **Nulo del lector** | K contra K da 0 diferencias; una mutación que pierde una protegida da veto; 50 negativos con un cúmulo de cumbre inyectado suben P2 en 50 (MOD-D §8.5) | el lector no sale |
| **Controles de cenit** | los de V375-E §4 (pares a menos de 5° con razón doble que contiene 1; ganancia pareja que no la mueve; ganancia creciente con el cenit que la sube) | la curva no se lee |
| **Candado** | sha256 **con fin de línea LF** (contenido con `\r` quitado) de cada archivo del lector, de las referencias y de `frontend/index.html` contra el manifiesto del sello, **antes** de correr (lección S171; §11) | no se corre |

Preguntas del instrumento (GUIA §3): (1) si la vía no corriera, C-via da 0 %; si el lector estuviera roto, el nulo del
lector y el placebo lo ven; si K de disco no fuera K de hoy, C-K lo ve. (2) Si los artefactos estuvieran vacíos,
C-cobertura da 0 pasadas contra miles de K. C-via y C-cobertura se imprimen por trozo en el log del runner y otra vez en
la lectura (un vigilante ciego da verde).

---

## 7. Poder (antes de leer)

**Con qué se contó.**
- **F26 (tabla):** `experiments/_s172_prereg_retro/recalcular_s7_ref_congelada.py`, salida al lado
  (`experiments/_s172_prereg_retro/recalcular_s7_ref_congelada_salida.txt`), sobre un `git archive` de `origin/main` `47cdc446f29f…` (K de disco de ese commit), predicado de
  `frontend/index.html` (blob `b618b6cc…`, sha256 LF `260b4a19…`). Referencia que decide: la **congelada** del §4.1,
  consolidado de Mirova-v1 en `cb91eb50…` (sha256 LF `811c4c07e38e55dc768197c9eb9e6e5df3659c41c39aa8f43d8e408a611f7ef4`)
  y OCR en `cfc57c4d…` (sha256 LF `01c9478d614a59017348fc7f95ae4cffc359b314d5852cf2c6d13b7f831fba6b`), las copias de
  S165 (`experiments/_s165_regla_posicion/referencia_salida.txt`, mismo sha256), con las capas de historia y respaldo
  que agrega `cargar_referencia_unificada` de ese commit. El mismo script corre de control el snapshot de `origin/main`
  (consolidado blob `00feeebc…`, sha256 LF `c0f18b6a…`; OCR blob `741fea06…`, sha256 LF `d38f2d0c…`), que reproduce
  las cifras del segundo verificador (`experiments/_s173_aud/vpr/contar_f26_F26_salida.txt` y `_F26M_`): **las dos
  referencias dan las mismas cifras en F26** (3.476 filas nocturnas indexadas en las dos; difieren sólo en la capa de
  historia, fuera de F26: 37 filas contra 2.503). Reglas: tabla sola, noche por elevación solar, SN, lectura A,
  ±120 s, Tupungatito desde el 02-23. Control positivo: las tres pasadas MODIS de Láscar de S159 salen «K no publica»
  con bajo1, bajo1 y protegida.
- **R25 (OSF):** no depende de la tabla; cifras de `experiments/_s173_aud/vpr/contar_osf.py`
  (`contar_osf_vent_salida.txt`, segundo verificador) sobre el OSF `0863c240…` y K de `origin/main` `47cdc446f`; no se
  recalcularon en esta ronda (VPR2-14).

**P1 con «cero perdidas».** Cota superior al 95 % de la tasa de pérdida compatible con 0 de n (regla del tres). La cota
supone pasadas independientes, y en Láscar no lo son (noches casi consecutivas de un mismo régimen, la misma
dependencia que D-45 reconoce al sortear por bloque): **es un piso de la cota real**, no la cota (VPR2-14).

| tramo y sensor | referencia | protegidas | por volcán | cota con 0 perdidas | lo que K hace |
|---|---|---|---|---|---|
| F26-M | tabla congelada (= snapshot de `origin/main`) | 9 | Láscar 9 | 33 % | pierde 1 (Láscar 02-16 01:20, mirada por nombre, §3.1 b) |
| F26-V, VIIRS 375 | tabla congelada (= snapshot) | 26 | Láscar 26 | 11,5 % | pierde 0 |
| F26-V, VIIRS 750 | tabla congelada (= snapshot) | 30 | Láscar 29, Isluga 1 | 10 % | pierde 0 |
| R25, 1 km | OSF | 161 | Láscar 155, Planchón-Peteroa 6 | 1,9 % (sin Láscar: 6, 50 %) | pierde 0 con record (1 sin record a ±120 s) |
| R25, 375 m | OSF | 317 | Láscar 273, PCC 28, Planchón-Peteroa 14, Isluga 2 | 0,9 % (sin Láscar: 44, 6,8 %) | pierde 0 |
| R25, 750 m (5 MW o más) | OSF | 17 | Láscar 17 | 18 % | pierde 0 |

Consecuencias que se escriben ahora: casi toda la evidencia de P1 es Láscar; la única evidencia fuera de muestra sobre
otros volcanes es VIIRS 375 de 2025 (44 protegidas OSF de tres volcanes) y MODIS de 2025 (6, de Planchón-Peteroa). Como K publica todas las
del OSF, P1-OSF sólo puede encontrar que la vía pierde algo que K ve.

**P2 (signos por bloque, D-45).** Bloques noche-volcán donde K yerra en F26, con la tabla congelada (igual con el
snapshot; `experiments/_s172_prereg_retro/recalcular_s7_ref_congelada_salida.txt`): **MODIS (febrero) 6** de P2 (5 negativos publicados y la noche de Láscar del 02-11 con 2
bajo 1 MW perdidas), más el bloque de la protegida perdida del 02-16 (7 en total; los mismos ocho eventos que lista
`experiments/_s173_aud/vpr/contar_f26_F26M_bloques_modis.txt`), **VIIRS 375 48**, **VIIRS 750 18** (febrero y marzo).
Bajo 1 MW, misma referencia: 158 en 375 (tras SN), 25 en 750, 5 en MODIS de febrero. Para MODIS: con 6 bloques, GANA exige que la vía arregle 6 de 6 (p = 1/64) o 5 con el
sexto empatado (2/64); con un bloque en contra ya no llega. En el censo de MOD-D la vía arregló alrededor del 90 % de los
errores de K (neto −44, B 53): en febrero eso da B de 3 a 7. **Resultado esperado de MODIS: SIN SUSTRATO o EMPATE, o sea
SIN PODER** (§8). Sin las cuatro pasadas MODIS de §3.1 (b), F26-M queda con **4 bloques** (Puyehue-Cordón Caulle
02-01, 02-04, 02-07 y 02-28), todos negativos que K publica, y ninguno donde K pierde una alerta: con B de 4 o menos la
regla de signos da SIN SUSTRATO por construcción (`MAX_B_SIN_SUSTRATO_P2 = 4`, `evaluar_d25` blob `1dbabf65` l. 149,
según el segundo verificador, `experiments/_s173_aud/vpr/INFORME.md` §5; VPR2-01). VIIRS 375 tiene poder razonable;
VIIRS 750, poco.

Antes de leer, el sorteo de etiquetas dentro de cada estrato (volcán × tramo de cenit) sobre K contra K dice qué fracción
de barajados cumple «GANA o EMPATE» por azar (GUIA §3b fila 7).

Las cifras de F26 de esta sección ya están recalculadas con la referencia congelada (ver «Con qué se contó»). Si antes
del despacho se congela otra referencia o cambia el K de disco (otro commit de `origin/main`), se vuelve a correr el
mismo script y se listan aquí las cifras que cambien.

---

## 8. Veredictos y sus nombres (por sensor)

### 8.1 Tabla (primera fila que se cumpla, sobre el brazo de posición que decide)

| orden | condición | nombre del veredicto |
|---|---|---|
| 1 | algún control del §6 en rojo para ese sensor | **INDECIDIBLE (CONTROLES)** |
| 2 | en F26 la vía pierde una protegida de la tabla que K publica (incluida una SIN DATO de la tabla que K publica; una SIN DATO del OSF en R25 va a la fila 4, VPR2-03) | **NO SE SOSTIENE: PIERDE PROTEGIDA [volcán, hora]** |
| 3 | la regla del sensor da NO ADOPTAR o «no cumple» por P2 PIERDE (o, en 750 con V750-A sellado, por M fuera de banda) en F26 | **NO SE SOSTIENE: PEOR QUE K** |
| 4 | cualquiera de: la regla da DECIDE NICOLÁS o BLOQUEA; P1b con alguna; M EMPEORA; candidata a veto en P1-OSF; pérdida sólo OCR que K publica; la curva de la vía CAE MÁS QUE MIROVA; el veredicto cambia sin las pasadas de §3.1 (b); en 375, cercano y radiante dan veredictos distintos; en 750, V750-A no sellado a tiempo | **DECIDE NICOLÁS** (con la lista) |
| 5 | la regla da SIN SUSTRATO en F26 **o, en VIIRS 375 y 750, P2 contra K da SIN SUSTRATO aunque el código del §9.7 de V375-E lo mapee a CUMPLE** (en 750, SIN SUSTRATO y BLOQUEA se leen como en D-45, `regla_signos_p2`; §5.6), y ninguna condición de la fila 4 | **SIN PODER FUERA DE MUESTRA** |
| 6 | la regla da PROPONER ADOPCIÓN / cumple en F26, y P1-OSF sin candidatas | **NO SE CONTRADICE FUERA DE MUESTRA (alertas: [volcanes con protegidas medidas]; silencio: [volcanes con negativos limpios]; F26-V: NOAA-20 y Suomi NPP oblicuo)** |

La fila 4 va antes que la 5 para que una pérdida, un P1b o una curva que cae más que MIROVA nunca queden bajo «sin poder»
(VPR172-03). El nombre de la fila 6 lo arma el lector con los conteos por volcán, y no promete más que esto: en febrero y
marzo de 2026 y en 2025, en los volcanes que el nombre lista, la vía no perdió una protegida que K publica, no se
equivocó más que K en lo débil y su magnitud pasó la regla de su sensor. **No** dice «igual a MIROVA», ni nada de los
volcanes sin alertas fuera de muestra, ni del sistema en noviembre, ni de los 34. Si el nombre de alertas dice sólo
«Láscar», así queda escrito.

**Por qué no se exige un mínimo de volcanes con protegidas para la fila 6** (el verificador lo propuso): cualquier mínimo
sería un número inventado (A115), y con los datos que hay (§7) sólo VIIRS 375 tendría más de un volcán. En vez de un
umbral, el alcance va en el nombre del veredicto y la decisión sobre si basta queda en ti (R-11).

### 8.2 Qué hace cada veredicto, por sensor (corrige «los tres sensores o ninguno»)

La sombra de los 34 ya está aprobada y no publica: esta prueba no la abre ni la cierra. Lo que sí toca, por sensor:

| veredicto del sensor | para la Compuerta B (publicar los 34) y la decisión D2/D6 del plan |
|---|---|
| NO SE CONTRADICE | ese sensor suma evidencia retrospectiva al lado de su sombra; el alcance (Láscar, etc.) va con ella a la Compuerta B |
| SIN PODER | **no posterga nada**: la paridad de ese sensor se sigue apoyando en su A/B dentro de muestra (rotulado) y en su sombra; esta prueba no agrega ni quita |
| DECIDE NICOLÁS | decides con la lista; mientras tanto, como SIN PODER |
| NO SE SOSTIENE | la vía de ese sensor no avanza hacia producción ni hacia los 34 hasta un A/B nuevo con la lista en la mano; los 34 publicarían ese sensor con K sólo si aceptas K como «igual a MIROVA» en él (D6 del plan), o se espera |
| INDECIDIBLE | se arregla el instrumento y se relee; no se re-corre a ciegas |

La regla del plan «los 34 con los tres sensores o con ninguno» (un sensor apagado se lee como silencio) vale para
**publicar**, y se mantiene en la Compuerta B. Aplicada a esta prueba la hacía casi inalcanzable, porque MODIS sale
probablemente SIN PODER (§7), y una compuerta que no se puede abrir sólo posterga sin medir nada.

Ningún resultado de esta prueba cambia lo que publica producción ni reemplaza la parada de una sombra.

---

## 9. Predicciones (para poder fallar)

1. VIIRS 375 (cercano): P1 sin pérdidas que vetan en F26; P2 GANA o EMPATE; razón de la vía en [0,9; 1,1]; curva
   REPRODUCE o NO RESUELTO; K/MIROVA alrededor de 0,6 a 0,7. Radiante, el mismo veredicto.
2. VIIRS 750: P1 sin pérdidas en F26; razón de la vía en [0,9; 1,1]; K bajo 0,8. P2 con poco poder.
3. MODIS (febrero): SIN PODER; la vía publica la protegida de 02-16 que K pierde; R25 sin candidatas en 1 km.
4. Verano: menos publicaciones de K en negativos limpios de volcanes nevados que en invierno (A69); si la vía gana menos
   que dentro de muestra, es esperable.
5. En R25 la razón de K por cenit cae (Spearman negativo fuera del barajado) y la de la vía no cae más que la de MIROVA.

---

## 10. Perfiles, workflow, trozos y costo

### 10.1 Perfiles

**`extends` resuelve un solo nivel**: `pipeline/profile.py` l. 46 a 67 (`origin/main`). Los dos perfiles extienden
`mirova_equivalent` directamente y repiten los flags.

**Riesgo de herencia (VR172-02).** Si producción enciende la vía de MODIS (PR de S172) o MxD03, los perfiles que
extienden `mirova_equivalent` los heredan. Por eso todo flag que define los brazos va escrito:
- `_s172_retro_paquete.yaml`: el de la Tarea 0.2 del plan más `enable_modis_geo_mxd03: false`,
  `enable_modis_crater_sin_dato: false` y `enable_modis_dist_desde_crater: false` en `thresholds:` (l. 923 a 925 de
  `profile.py`). Carpeta `_s172_retro_paquete`.
- `_s172_retro_k.yaml`: lo mismo con las tres vías en `false`. Carpeta `_s172_retro_k`.
- Prueba: los dos resuelven esos seis flags al valor escrito aunque `mirova_equivalent` los cambie (padre mutado en un
  directorio temporal). Roja antes, verde después.
- Ninguno marca régimen en el lector de V375-E (perfiles nuevos, plan H9): se comprueba con su batería antes del merge.

### 10.2 Workflow

`reproc-retro-paquete.yml` según la Tarea 0.2 del plan (`pyproj` instalado, que es justo lo que le falta al NRT según el
bloqueante G5 de la mini auditoría de MODIS; sólo `EARTHDATA_TOKEN` con corte si viene vacío; sin job `merge`; artifacts
de 30 días; `"on":` entre comillas; `ubuntu-24.04`; grupo propio; `controles_via.py` por trozo), más:
- **Trozos de 20 días, y de 10 para Chillán.** En el reproceso de K (run 39125546355, trozos de ~36 días) la mediana fue
  80 min, el p95 158 y el máximo 172 contra un paso de 170, y los **6 fallos fueron todos de Chillán**, 5 de ellos
  cortados a 171,4 a 171,7 min: su tasa real es al menos 4,76 min por volcán-día, contra 1,76 a 2,64 de los otros diez
  (`costo_run_salida.txt`). Con 10 días y factor 1,25, Chillán queda en ~60 a 75 min.
- El workflow rehúsa cualquier perfil que no empiece por `_s172_retro_`.

### 10.3 Despachos (de a uno, cada uno desde un tag, después de V750-B)

| despacho | perfil | volcanes y ventanas | jobs | cuándo |
|---|---|---|---|---|
| D1 humo | `_s172_retro_paquete` | Láscar, tres días sueltos (2025-06-15, 2026-02-10, 2026-10-05) | 3 | tras el merge del perfil y el workflow |
| D2 tanda 1 | `_s172_retro_paquete` | 11 volcanes en F26 (Tupungatito desde 02-23) y DM | 47 | el día del merge de `roi_v750` o el siguiente; antes, V750-A sellado o no (§5.1) |
| D3 control K | `_s172_retro_k` | DM entero; Láscar y Chillán en F26 enteros; tres días de F26 de cada uno de los otros 9 | 30 | justo después de D2 |
| D4 tanda 2 | `_s172_retro_paquete` | 10 volcanes (sin Tupungatito) en R25 | 176 | justo después de D3, mejor fuera de 01 a 12 UTC |

Conteo de jobs: D2 = 9 volcanes × (3 + 1) + Chillán (6 + 2) + Tupungatito (2 + 1) = 47; D3 = 12 (DM, Chillán en 2) + 3
(Láscar) + 6 (Chillán) + 9 = 30; D4 = 9 × 16 + 32 (Chillán) = 176, bajo el tope de 256 por matriz. Tags `s172-retro-dN`
sobre el `main` que contiene perfiles, workflow y `roi_v750` (lección S152). MODIS sólo corre en Linux: todo en el
runner. `max-parallel: 6` (con NRT 8, sombra 4 y experimental 4 serían 22, sobre el tope de 20 si el plan es Free, SIN
DATO: si coinciden, bajar a 4).

### 10.4 Costo

Tasa de K medida: 2,39 min de runner por volcán-día con sobrecarga (run 39125546355: 254,2 h, 176 jobs de reproceso; el run tiene 178 en total, probablemente 2 de armado, seguimiento S-D
del segundo verificador, `experiments/_s173_aud/vpr/run_39125546355.json`; 580 días × 11,
pared 32,3 h). Factor de la vía 1,06 a 1,25 (SIN DATO para VIIRS; `experiments/_s172_capacidad_nrt/INFORME.md` §4 acota
sólo MODIS; lo miden D1 y la sombra). Chillán a su tasa propia, de 4,76 min por volcán-día o más.

| despacho | volcán-día | horas de runner | pared con 6 en paralelo |
|---|---|---|---|
| D1 | 3 | < 0,5 | < 1 h |
| D2 | 803 | 36 a 44 (Chillán incluido a su tasa) | 6,5 a 8 h |
| D3 | 321 | 13 a 16 (K, sin factor) | 3 a 4 h |
| D4 | 3.200 | 150 a 180 (Chillán incluido) | 24 a 29 h |
| total | 4.327 | 197 a 237 | 34 a 41 h |

Ninguna tanda cruza la rotación del token del **2026-11-27** (vence 2026-12-07 18:03).

**Calendario (UTC, estimado):** 11-02 a 11-05 sello, lector, perfiles y workflow; 11-03 V750-B (~2 h); ~11-04 a 11-06
lectura de V750-B y merge de `roi_v750`; D1 ese día; D2 y D3 ~11-06 a 11-07; D4 ~11-07 a 11-09; lectura, verificador e
informe ~11-10 a 11-12.

**Alternativa para adelantar MODIS y VIIRS 375 (R-4):** un perfil con `sensors: {viirs_750: false}` sobre F26 y DM
apenas termine V750-B, y VIIRS 750 después. Apagar un sensor salta su proceso pero no su descarga
(`scripts/run_pipeline.py` l. 217 a 235), así que suma 30 a 40 h de runner. R25, siempre en un despacho.

---

## 11. Candado (sin esto no se despacha)

- Manifiesto con sha256 de: `leer_retro.py` y lo que importa (`evaluar_f4.py` del candado de MOD-D, `evaluar.py` de
  V375-E con sha256 LF `2126b743…`, el analizador de V750-A si se aplica, `evaluar_d25.py` blob `1dbabf65`,
  `scripts/clase_mirova.py`, `scripts/banco_paridad.py`, `scripts/referencia_mirova_unificada.py`), las referencias
  congeladas, el OSF (`0863c240…`), `frontend/index.html` del tag, los dos perfiles y, si se aplica como anexo, el
  texto de V750-A en `aa5583646` (§5.1).
- **Todo sha256 del manifiesto, y el de este documento, se calcula sobre el contenido normalizado a LF** (`tr -d '\r' <
  archivo | sha256sum`), como ya hace el lector de V375-E (`2126b743…`). Con `core.autocrlf` el mismo contenido da otro
  sha256 en disco (la tabla consolidada: `ab1a208c…` en el worktree, `c0f18b6a…` por `git show`, mismo blob
  `00feeebc…`; seguimiento S-B del segundo verificador). El sha256 LF de este archivo en la ronda 3 queda en el commit
  que la sube; el del sello va en el mensaje del commit y en el tag del sello, no dentro del archivo (no puede
  contenerse a sí mismo).
- El lector con TDD (rojo antes de verde, anotado en el commit), batería sintética que cubra cada fila del §8.1 y cada
  regla del §5.6, mutaciones atrapadas por aserción con control de caída, y verificador limpio de otro modelo sobre el
  lector y sobre este documento.
- `git diff <commit del sello> -- PREREGISTRO_RETRO_PAQUETE.md` vacío al leer, y su sha256 LF igual al del tag del
  sello; lo agregado después va rotulado *post hoc*.
- Cifras del §7 recalculadas sobre `origin/main` exportado con la referencia congelada y escritas con el commit de K y
  el sha256 LF de la referencia: hecho para F26 (commit `47cdc446f`, `811c4c07…`, `01c9478d…`); se repite si cambia
  la referencia o el commit de K antes del despacho, y el script y su salida entran al manifiesto.
- Excepciones nombradas de C-K escritas antes de leer F26, con su tope (R-15).

---

## 12. Qué decide Nicolás (con recomendación)

**Contestadas el 2026-11-02 (servidor 15:42 UTC): R-1 a R-15, «sí» las quince** (Nicolás, ante la lista de
pendientes: «en el resto haz lo que recomiendes»; las quince recomendaciones son «Sí»). Falta la frase de sello.

Cada fila se contesta con una sola palabra, «sí» o «no», y «sí» acepta la recomendación de esa fila. Un «sí a todo»
acepta las quince recomendaciones (ronda 3: R-2, R-3, R-6, R-8, R-11 y R-12 reescritas para que «sí» tenga una sola
lectura, VPR2-08; las otras ocho llevadas a la misma forma «¿Aceptas…?», para que ninguna recomendación sea «no»; R-15
nueva, VPR2-06).

| # | pregunta | recomendación | por qué |
|---|---|---|---|
| R-1 | ¿Aceptas que la protegida OSF se defina con la distancia del píxel más caliente, y que `Max_Dist` sólo se informe? | **Sí** | `Max_Dist` mide al píxel más lejano: una cola larga sacaría un cúmulo de cráter |
| R-2 | ¿Aceptas usar K de disco con el control ampliado D3 (~13 a 16 h) en vez de re-correr K entero (~180 h)? | **Sí** | dos mediciones previas de K re-corrido = publicado; D3 cubre Chillán, donde cambió el código; si C-K cae, se re-corre K entero igual (§6) |
| R-3 | ¿Aceptas que, si V750-A no eligió posición antes de D2, en VIIRS 750 decida radiante y cercano y pico sólo informen? | **Sí** | es lo que hace hoy la vía |
| R-4 | ¿Aceptas despachar la tanda 1 entera, sin partirla por sensor? | **Sí** | partirla adelanta MODIS y VIIRS 375 3 a 4 días a cambio de 30 a 40 h y un despacho más; «no» quiere decir partirla (§10.4, alternativa) |
| R-5 | ¿Aceptas que una pérdida contra el OSF no vete sola y lleve el sensor a DECIDE NICOLÁS? | **Sí** | no es el NRT y está filtrado (A105) |
| R-6 | ¿Aceptas que «a la par de MIROVA» se diga sólo con la lectura B del §5.4 (ninguna protegida perdida que K publica, tasa en negativos limpios no mayor que la de K, razón en [0,8; 1,25]), siempre con la lista de volcanes? | **Sí** | único modo con números ya existentes (A115) |
| R-7 | ¿Aceptas que la banda [0,9; 1,1] de V750-A decida en F26-V si V750-A está sellado? | **Sí** | cambiarla al leer otra ventana sería A95 |
| R-8 | ¿Aceptas que en MODIS decida febrero, leído con y sin las cuatro pasadas MODIS de §3.1 (b), y que marzo sea sólo control? | **Sí** | marzo es tramo C de MOD-D y lo tocó la V2 de K; febrero está expuesto por nombre |
| R-9 | ¿Aceptas que Tupungatito entre a F26 desde el 02-23 y quede fuera de R25? | **Sí** | la referencia no lo cubre |
| R-10 | ¿Aceptas que la noche del operador (§5.5) sólo informe y no decida? | **Sí** | las reglas y el criterio son por pasada y sensor |
| R-11 | ¿Aceptas que un «NO SE CONTRADICE» con alertas sólo de Láscar cuente como evidencia de ese sensor en la Compuerta B, con su alcance escrito y junto con su sombra? | **Sí** | no hay más alertas fuera de muestra; inventar un mínimo no agrega información. Ese veredicto no prueba nada sobre los volcanes de señal débil (§1) |
| R-12 | ¿Aceptas despachar D2 aunque V750-A no esté sellado, con techo DECIDE NICOLÁS en VIIRS 750? | **Sí** | MODIS y 375 no dependen de V750-A; la lectura de 750 queda para cuando se selle. «No» quiere decir esperar el sello de V750-A |
| R-13 | ¿Aceptas que en VIIRS 375, si cercano y radiante dan veredictos distintos, el sensor vaya a DECIDE NICOLÁS con los dos veredictos? | **Sí** | lo que publica el record hoy es radiante; adoptar cercano pide un cambio de código que esta prueba no prueba |
| R-14 | ¿Aceptas compuertas por sensor (§8.2) en vez de «los tres o ninguno» para esta prueba, dejando «los tres o ninguno» en la Compuerta B? | **Sí** | una compuerta inalcanzable posterga sin medir |
| R-15 | ¿Aceptas un tope de **a lo más 3 pasadas por sensor** como excepciones nombradas de C-K y del nulo de runner, cada una con el empate de `argsort` mostrado en el record, y que C-K caiga si hacen falta más? | **Sí** | un control con excepciones sin tope no puede fallar (A110, A116; VPR2-06). El 3 lo propuso el segundo verificador como ejemplo y no sale de una medición (A115): por eso lo decides tú; «no» deja la pregunta abierta y C-K sin tope no se puede sellar |

---

## 13. Premisas del encargo y del plan que no se sostienen al leer

1. Las copias de los pre-registros en `main` y `loop/activo` son viejas: V375-E sellado sólo en los tags
   `s168-v375e-cuerpo-sellado` y `s170-v375e-lector`; V750-B sellado en `s167-v750b-adenda3-sellada`; V750-A en BORRADOR
   en `aa5583646`, sin verificador limpio (su §11). Hay que citar tags.
2. El OSF de 750 tiene piso de 5,05 MW.
3. NOAA-21 sin referencia en F26 ni en el OSF.
4. Conteos de F26 del plan (34 y 30): mezclaban día y noche; con SN y noche son 26 y 30, casi todo Láscar.
5. Trozos de 37 días no alcanzan, y Chillán necesita 10 (§10.2).
6. La prueba de perfil del plan no ve la herencia de MxD03 (§10.1).
7. La vía descarta pasadas sin record (171-01): sólo C-cobertura las ve.
8. **La Compuerta A del plan ya no es lo que esta prueba decide**: Nicolás aprobó la sombra de los 34 con las vías el
   2026-11-02 (`tasks/LOOP_OBJETIVOS.md`, entrada de las 01:24 UTC, l. 589 a 597 de `origin/loop/activo` `4be4b2e32`), y
   la rama `claude/s172-sombra-34` ya la tiene (entrada de las 01:50). Esta prueba pasa a informar la Compuerta B y la
   decisión de detector por sensor (§8.2).
9. «Fuera de muestra» en la ronda 1 se leía como «nadie lo miró»; febrero sí se miró por nombre (§3.1).

---

## 14. Lo que este pre-registro no hace

No corre nada ni crea perfiles o workflow (Tarea 0.2 del plan, con tag `pre-s172-retro-paquete` y frase de merge). No
toca `pipeline/`, `nrt.yml`, `volcanoes.yaml`, `grillas_mirova.yaml` ni la sombra. No sella el texto de V750-A. No mide
el día, ni Chillán en erupción, ni los 34. No adopta nada.

---

## 15. Hallazgos de los verificadores y su tratamiento

**Primer verificador** (ronda 2; Sonnet 5.5, SELLABLE CON CAMBIOS):

| hallazgo | grav. | tratamiento |
|---|---|---|
| VPR172-01 P1 fuera de muestra es Láscar | 4 | §0 lo dice primero; §7 tabla por volcán con «sin Láscar»; §5.2 y §5.4 por volcán; fila 6 del §8.1 renombrada «NO SE CONTRADICE FUERA DE MUESTRA» con el alcance armado por el lector; §8.2 y R-11. No se fija un mínimo de volcanes (sería inventado, A115): razón escrita en §8.1 |
| VPR172-02 «ninguna regla lo miró» falso para diagnósticos | 3 | §3.1 inventario de tres tipos; lectura con y sin las pasadas de (b); cambio de veredicto lleva a DECIDE NICOLÁS (§8.1 fila 4); R-8 |
| VPR172-03 orden de filas 4 y 5 | 3 | DECIDE NICOLÁS sube sobre SIN PODER (§8.1) |
| VPR172-04 C-via 99 % y asimetría | 3 | F26 y DM 100 % como MOD-D; R25 SIN DATO simétrico en los dos brazos con veto y corte de 10 %; desviación en §5.6 |
| VPR172-05 nulo y C-K que no pueden fallar | 3 | nulo con B = 0 salvo pasadas nombradas y control de que puede fallar (contra PLACEBO); C-K sin 1 %, ampliado a Chillán F26 entero y tres días por volcán (D3) |
| VPR172-06 V750-A sin verificador | 3 | no se copia ni se sella aquí; se aplica sólo si V750-A se sella antes de D2; si no, techo DECIDE NICOLÁS (§5.1, R-12) |
| VPR172-07 F26-V contra A119(b), casi sólo NOAA-20 | 3 | §3.3: desviación declarada, composición por satélite y cenit, rótulo «NOAA-20 y Suomi NPP oblicuo», curva por satélite, noche limpia exige fila en todas las pasadas |
| VPR172-08 cercano decide, el record publica radiante | 3 | radiante se lee con la misma regla al lado; si difieren, DECIDE NICOLÁS (§5.1, R-13) |
| VPR172-09 MODIS casi seguro SIN PODER; «tres o ninguno» inalcanzable | 2 | §0 y §7 lo anticipan; §8.2 compuertas por sensor; SIN PODER no posterga; «tres o ninguno» queda para la Compuerta B (R-14) |
| VPR172-10 diferencias no declaradas con las reglas selladas | 2 | tabla §5.6 |
| VPR172-11 fallos de Chillán censurados | 2 | trozos de 10 días para Chillán; costo con su tasa propia (§10.2, §10.4) |
| VPR172-12 análogo de lejana mal elegido | 2 | lejana OSF = `class` 1 fuera del radio (49 de Chillán); las 13 `class` 0 dentro del radio como ambiguas (§4.2) |
| VPR172-13 razón del OSF truncada | 2 | la razón de R25 es sólo cota, no decide y no se compara con F26 (§4.3) |
| VPR172-14 cifras desactualizadas | 1 | cifras del verificador en §3.2, §4.2 y §7 (9 / 26 / 30; bajo 1 MW 158 / 25 / 5; NOAA-21 desde 04-03; 627 y 3.200 volcán-día; `Dayflag`); se recalculan antes del sello |
| VPR172-15 encabezado | 1 | encabezado con horas del servidor y commit de cada ronda |
| S-1 checkout local atrasado | 2 | todo recálculo sobre `git archive` de `origin/main` (§2, §4.1, §7) |
| S-2 NOAA-21 en R25 sólo cuesta | 1 | declarado (§3.2); no se puede saltar sin tocar el código |
| S-3 K publica todas las protegidas OSF | 2 | P1-OSF rotulado como control de «no pierde las evidentes» (§4.2, §7) |
| S-4 trozo de Chillán que falla dos veces | 2 | sus pasadas a SIN DATO en la primera línea y cuentan para el 10 % (§6) |
| S-5 nada sobre las grillas de los 34 | 2 | §0 y §8.1 lo dicen; queda para la Compuerta B |
| S-6 hito de NOAA-21 en el script | 1 | no se corrige aquí (fuera de alcance); se usa la medida del 04-03 |

**Segundo verificador** (ronda 3; `experiments/_s173_aud/vpr/INFORME.md`, Fable 5.1, SELLABLE CON CAMBIOS; sus §3 bis
con los 14 cambios de texto):

| hallazgo | grav. | tratamiento |
|---|---|---|
| VPR2-01 inventario (b) incompleto (Lastarria MODIS 02-24 07:05 y siete pasadas de 2025) | 3 | §3.1 (b): Lastarria agregada como cuarta pasada MODIS («la cuarta es un negativo que K publica»; «exactamente» quitado) y viñeta de 2025; lectura con y sin (b) extendida a R25; §7: sin (b) quedan 4 bloques (Puyehue 02-01, 02-04, 02-07, 02-28) y la regla da SIN SUSTRATO por construcción; R-8 dice «cuatro» |
| VPR2-02 SIN SUSTRATO de P2 en 375 cumple en §9.7 y cae en la fila 5 | 2 | §8.1 fila 5 con el texto propuesto; dos filas nuevas en §5.6 (375: CUMPLE pasa a SIN PODER; 750: SIN SUSTRATO y BLOQUEA como en D-45, `regla_signos_p2`) |
| VPR2-03 «veta» con dos significados | 2 | C-cobertura: F26 fila 2, R25 candidata a veto (fila 4); C-via R25: «candidata a veto (fila 4)»; fila 2 del §8.1 precisa que la SIN DATO es de la tabla; cita de `leer_sombra_v375e.py` con la línea de cada tag (573 y 612) |
| VPR2-04 placebo con d solo da MEJORA | 2 | §6 PLACEBO: M de D-28 (d y d′, `comparar_con_ganancia`) en MODIS y 375; en 750, el comparador de V750-A §6.2 separa la vía de K × 1,2; ejemplo aritmético escrito |
| VPR2-05 MODIS OSF 161, no 162 | 2 | §4.2 (161; 160 de 161; las cuatro diurnas con 0, tres de 1 MW o más, con sus horas), §5.2 (6 en 1 km), §7 (fila R25 1 km: 161, sin Láscar 6, 50 %; «MODIS de 2025 (6)»); cifras de `contar_osf_vent_salida.txt` |
| VPR2-06 excepciones de C-K y del nulo sin tope | 2 | §6 C-K y nulo: tope de a lo más 3 pasadas por sensor con el empate mostrado; si hacen falta más, C-K cae. El número 3 es una decisión: **R-15**, recomendación sí |
| VPR2-07 texto de V750-A sin commit ni líneas | 2 | §5.1 fila VIIRS 750: `aa5583646`, §6 l. 217 a 243, §6 bis l. 174 a 196, §6 ter l. 197 a 216; diff si se sella en otro commit; §11 lo agrega al manifiesto |
| VPR2-08 seis R-n no se contestan con «sí» | 2 | R-2, R-3, R-6, R-8, R-11 y R-12 reescritas como «¿Aceptas …?» con recomendación «Sí»; en R-11 la frase de los volcanes débiles pasó a «por qué»; las otras ocho llevadas a la misma forma (ninguna recomendación queda en «no», para que un «sí a todo» no se lea al revés en R-4, R-5 y R-10); nota al inicio del §12 |
| VPR2-09 C-montaje sin criterio de «explicada» | 2 | §6 C-montaje: explicada sólo por (a) un hunk listado del `git diff` que la reproduce al re-correr con el código del tag de origen, o (b) `otro_granulo` |
| VPR2-10 marzo omite la V2 de K; falta D25 | 1 | §3.1: fila de D25 y frase «Marzo de 2026 lo tocan MOD-D y la V2 de K (control), sólo en MODIS» |
| VPR2-11 composición por satélite no se reproduce | 1 | §3.3: cifras del segundo verificador con las reglas escritas (790 / 111; 162 / 702; 895; 844 / 49; 198 / 656), `contar_f26_F26_salida.txt`; después, conteos y cenit recalculados con la tabla congelada (`recalcular_s7_ref_congelada_salida.txt`): conteos iguales, cenit nuevos (47,7 / 44,3 / 42,5 en vez de 47,4 / 44,9 / 42,6) |
| VPR2-12 dos citas sin localizar | 1 | §6 C-K: quitada «V375-E l. 66 a 68», el 27 derivado del 1 % de 2.660 y los 48 bloques del §7; §1: «0,996 a 0,998» con l. 28 |
| VPR2-13 curva de cenit incompleta y desviación no declarada | 1 | §5.3 con los seis nombres (NULO SESGADO, 8 noches en la lectura o en el nulo); §5.6: fila «CAE MÁS en retrospectiva: informa en V375-E, aquí DECIDE NICOLÁS, conservador» |
| VPR2-14 regla del tres con pasadas dependientes; cifras sin sha | 1 | §7: la cota es un piso bajo independencia que en Láscar no se cumple; párrafo «Con qué se contó» con commit `47cdc446f`, blobs y sha256 LF de lo contado; las cifras de F26 recalculadas por el autor con la referencia congelada (`recalcular_s7_ref_congelada.py`, con control que reproduce al segundo verificador): iguales; cada cifra dice su referencia; R25 sigue con el OSF del segundo verificador |
| S-A K de disco en DM no publica tres protegidas | 2 | declarado en §6 C-montaje con las tres pasadas y `contar_f26_DM_salida.txt` l. 12, 13 y 38 |
| S-B sha256 con CRLF | 1 | §11 y candado del §6: todo sha256 sobre el contenido normalizado a LF; el de este documento va en el commit y el tag del sello |
| S-C prompt con CRLF | 1 | mismo patrón que S-B; sin cambio en el texto |
| S-D 178 jobs en el run | 1 | §10.4: 176 de reproceso, 178 en total (`run_39125546355.json`, `n_jobs`) |
| S-E disco D: bajo | 1 | sin cambio en el texto (operativo) |

---

## Dudas abiertas (cortas)

1. ¿V750-A se sella antes de D2? Define si VIIRS 750 puede salir de DECIDE NICOLÁS (R-12).
2. ¿El lector de la sombra de VIIRS 750 marca régimen con perfiles nuevos? (plan §14, SIN DATO).
3. ¿El fetch de 2025 encuentra MxD03 todos los días? Si falta en más de 10 % de alguna clase, MODIS de R25 cae.
4. ¿Qué referencia congelada: la de MOD-D fase 4 o una más nueva? Para F26 no cambia nada: la de MOD-D fase 4 y el
   snapshot de `origin/main` del 2026-11-02 dan las mismas cifras (§7). Una más nueva se mide con el mismo script.
5. Plan de la cuenta de GitHub (tope de 20 jobs): SIN DATO.
6. Definición de `Dayflag` y `Satellite` en el paper: ya no decide nada aquí, pero conviene dejarla leída.
