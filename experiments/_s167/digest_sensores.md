# Digest por sensor para actualizar el programa de la réplica (S167, sólo lectura)

Hora del servidor al leer: Wed, 28 Oct 2026 13:03:55 GMT (`gh api -i`). Refs: `origin/loop/activo` `0b41534a7` (S167
vuelta 2), `origin/main` `ba61c330f`. Programa leído entero: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md`
(219 líneas, último cambio `72928820b`).

Convención: CERRADO, SELLADO, BORRADOR, CORRIENDO, NO EMPEZADO, DESCARTADO. SIN DATO = nadie lo midió; SIN VERIFICAR =
lo dice una sola fuente y yo no lo comprobé. «Bitácora» = `tasks/LOOP_OBJETIVOS.md` §6 en `loop/activo`. **Cito la
bitácora por entrada (sesión y vuelta, o fecha y hora del título), no por línea**: la coordinadora la escribe mientras
leo y los números de línea corrieron 20 en una hora.

## 0. Lo que cambió desde el traspaso S167 (comprobado hoy)

- **V750-A: los arreglos VP-01 a VP-03 ya están en el remoto**: `claude/s162-viirs750-2-918174` = `5c45c0c07`
  (2026-10-28 13:00 UTC), sobre `58d62bd8f`, 5 archivos de `experiments/_s162_v750a/`. Agrega E74 a E76 y M81 a M85.
  Medidor sobre los 16 escenarios nuevos: 22 de 23 atrapadas por aserción; M82 SIN DATO (bitácora S167 v2). El medidor
  completo empieza cuando termine la batería de identidad. Total de escenarios: la bitácora dice 74; el archivo de
  pruebas tiene identificadores E1 a E76 (no reconcilié).
- **W6** (run 40681454167) a las 13:04 UTC: 6 jobs `success`, 3 `in_progress`, 13 `queued`.
- **MOD-D fase 4**: `claude/s166-modd-f4` sigue en `ff03538dd`. Ahí la batería da 53 de 53
  (`probar_evaluar_f4_salida.txt`), pero `mutar_evaluar_f4_salida.txt` es la corrida vieja (46 de 46 sobre 40
  escenarios). Las mutaciones M47 a M67 sobre 53 escenarios no están commiteadas.

## 1. Estado por experimento

### 1a. VIIRS 750

| exp. | estado hoy | resultado medido | evidencia |
|---|---|---|---|
| V750-C ablación del oráculo | CERRADO, verificado (Fable 5.1) | **Dos piezas, no una**: en las 38 cumbres dentro de la caja sensible calla la interpolación lineal (vecino más cercano recupera 23, en la celda de K); en las 22 fuera (Tupungatito 17, PCC 4, Láscar 1) calla primero la ROI. Magnitud: fondo del código 0,999 contra fondo de anillo 0,458 (K 0,510). La caja por defecto pierde 7 protegidas, todas de PCC. El remuestreo nativo sigue sin brazo (lo mide N0/N1 dentro de V750-B) | `experiments/_s162_v750c/INFORME.md:16-40`; `verificador/VERIFICADOR_V750C.md:89`; bitácora S162 2026-10-24 ~16:20 |
| V750-F O2 en MATLAB | CERRADO | MATLAB R2026b: Etna exacto al OSF, detección = Octave 311/311; ningún modelo viejo de `fillmissing2` era MATLAB. Regla identificada (Delaunay con desempate simbólico, x = fila): 166/166 VRP, 84/84 fondos, confirmada con implementación independiente. Portada a la vía, y fuera de la envolvente la vía deja NaN como MATLAB | bitácora S163 v2, v6, v8; `pipeline/mirova_v750_codigo.py:550` en main |
| V750-B ROI por volcán | SELLADO (D-48, `1af6c3cd8`, tag `s162-v750b-sellado`); adenda 1 confirmada (D-48); **adenda 2 SELLADA por Nicolás** (sobre `739edff39`, anexada en `609fa1c88`, tag `s162-v750b-adenda2-sellada`). NO DESPACHADO: va el 2026-11-03 | Brazos B0, B1, B2, B3, B4, B5, K y N0/N1 de diagnóstico. Ensayo 2026-10-27 (hasta 10-26): 5.841 objetivos, 0 sin gránulo, más 20 `far_ref` | `PREREGISTRO_V750B.md` del tag, l. 1-32, 58-100, 136-160, 345-490; bitácora S162 2026-10-24 ~18:25, S163 ~04:40, S166 v1, v3, v4 |
| Vía «código MIROVA» V750 (fase 3) | EN MAIN, APAGADA (#907, merge `cff07d173`, tag `pre-s164-merge-907`) | Flag apagado: 6.143/6.143 records iguales; equivalencia local roja a verde en 1.020 casos + 10 recortes. **Usa `roi_v750: def` en los 11 volcanes** | bitácora S164 v3; `pipeline/grillas_mirova.yaml:24-40` en main |
| V750-A paquete contra K | BORRADOR (sin sello) | Sin datos. Analizador verificado dos vueltas (`verificador/`, `verificador_v2/`); medidor previo 62 de 62; agregado de posición verificado LISTO CON CAMBIOS (VP-01 a VP-03), arreglos en `5c45c0c07`. Faltan: medidor completo y el verificador de `equivalencia_v750a.py` que pide su propio §11 | `5c45c0c07:experiments/_s162_v750a/PREREGISTRO_V750A.md` §3, §6 bis, §11; `verificador_posicion/INFORME.md:21-33`; bitácora S165 v3, S166 v7, S167 v2 |
| V750-D cúmulos por matriz | NO EMPEZADO (espera V750-A) | Verificador S162: 7 a 13 de 290 publicaciones, 1 protegida cruza 1 MW | `experiments/_s162_vuelta2/VERIFICADOR_CUMULOS_MATRIZ.md` |
| V750-E diurno con el código | NO EMPEZADO. Lo que corre es el A/B diurno **sobre K** (D-10, §1d) | En ese A/B un ADOPTAR de VIIRS 750 va siempre a DECIDE NICOLÁS, porque en 750 manda el código | `origin/main:experiments/_s163_diurno_k/PREREGISTRO.md` §6.3 |

### 1b. VIIRS 375

| exp. | estado hoy | resultado medido | evidencia |
|---|---|---|---|
| V375-A higiene de la etiqueta | CERRADO | #903: `resumir_pasadas` (la tabla manda), `es_protegida`, `protegida_de_crater` al lado de la lectura A. Sobre las 81 protegidas: 70 de cráter; las 11 que no, todas `ocr_snpp_antes_del_hito`. Las funciones viejas de `clase_mirova.py` no cambian (evaluadores sellados) | PR #903; `experiments/_s162_instrumento/T4_T6_INFORME.md:15-32`; bitácora S163 ~04:20 «V375-A cableado» |
| V375-B negativos (D-36) | CERRADO: «SILENCIO ACOTADO BAJO K», verificado | Primer lote: 4 de 389, NO RESUELTO. B2 (run 40131572769): el port publica 6 de 1.165 noches limpias nuevas (0,52 % [0,24; 1,12]), todas de 1 píxel y 0,01 a 0,04 MW; cota 2,48 % (estricta 2,65 %) contra 3,85 % de K | `experiments/_s162_v375/b2/resultado_run40131572769/INFORME.md:11`; bitácora S162 2026-10-24 ~19:30 y ~22:45 |
| V375-C ROI | CERRADO; PD1 = **C13 en todos** (D-48, S164) | C13 en el cráter: recall bajo 1 MW de 0,69 a 0,95 [0,92; 0,98], P2 contra K GANA, negativos 2,03 %, M 0,999 | `experiments/_s162_v375/resultado_run40116289866/INFORME.md`; bitácora S162 ~19:30, S164 v4 |
| V375-D números propios | DESCARTADO | Con la vara de MATLAB la magnitud de C no cambia (C13 0,999) | bitácora S163 v8 y «O2-375 cerrado» |
| Vía «código MIROVA» V375 (fase 3) | EN MAIN, APAGADA (#921, merge `bd711db63`) | Flag apagado: 6.143/6.143 records idénticos. Equivalencia con el port: **NO EQUIVALENTE** en 8 pasadas (4 protegidas: Isluga 06-17, 09-28, 10-03; Láscar 10-01), todas por la regla de posición; VRP sobre 4 px: 40 de 329 fuera con la vara vieja | bitácora S165 v8, v11; `PREREGISTRO_E.md` §8.3 en el tag |
| V375-E paquete contra K | **Adenda 2 SELLADA** (`67838f2a5`, tag `s166-v375e-adenda2-sellada`, N-3 aplicado, vara nueva del paso 1 aceptada). **El cuerpo (§1 a §7, con la adenda 1) sigue BORRADOR** según el encabezado del propio tag. Corrida FAR NO DESPACHADA (espera W6) | Sin lectura de P. Batería 140/140 (S166, árbol LF); nulo 83/84 en CRLF y 82/84 en LF (según el autor). Línea base medida antes: razón doble K/MIROVA por cenit 0,766 [0,722; 0,861], 215 noches, «CAE MAS QUE MIROVA». K publica 122 de las 330 lejanas. Con radiante, Isluga 06-17 y Láscar 10-01 (NOAA-21) siguen vetando el §5.4 (a) aun con N-3 | `PREREGISTRO_E.md` del tag l. 1-31, §8.4, §8.5, §8.11, §8.13; bitácora S166 v19, v22 |
| V375-F Chillán sobre 3 MW | NO EMPEZADO | | programa l. 108 |

### 1c. MODIS

| exp. | estado hoy | resultado medido | evidencia |
|---|---|---|---|
| MOD-A cita de MOD03 | CERRADO (#902) | Coppola 2026 p. 4: MOD03 es insumo también en el NRT; el método del remuestreo sigue SIN LOCALIZAR | PR #902; programa l. 202-204 |
| MOD-B MxD03 sobre K | CERRADO: «CUMPLE SIN DAÑO», verificado (Fable alto) | 5.465/5.465 pasadas; P1 0 de 48; P2 bajo 35° EMPATE; MxD03 más cerca del cráter por 0,73 km; M neutro en la mediana, pero 17 de 79 alertas cambian más de 10 %. A61 de las 48: 0,15 a 0,89 km del cráter, ninguna a otro objeto. Runner real ~15 h, no 47. **#920 en main con tres flags APAGADOS**, más #922 (V165-03). Probe 40584157486: 18/18 iguales al brazo X encendido y 18/18 a K apagado | bitácora S162 2026-10-24 ~21:00 y ~21:25, 2026-10-25 ~03:10, S165 v9, v12; `experiments/_s162_mxd03/resultado/INFORME.md` |
| MOD-C negativos del port | CERRADO: INDECIDIBLE, verificado | 2 de 390 neg_resto (0,51 %): Láscar 2026-05-11 07:55 (calor real, candidata al experimental, MEJ-7) y Llaima 2026-07-24 01:05 (artefacto de gradiente, SOSPECHA fuerte). ΔE −18,1 [−44,4; +40,1]. El «gana contra K» pasó al censo de MOD-D | bitácora S162 ~18:50, ~19:05, ~19:15; `experiments/_s162_modis_negativos/` |
| MOD-E bow tie (D28) | CERRADO, verificado | Ablación real con los 403 recortes nativos de MOD-C: el método A no abre huecos y las 11 protegidas siguen; la regla de filas de borde mataría Chillán 2026-10-01 08:35, descartada. Efecto de D28 en la magnitud SIN DATO. Entra a MOD-D sólo como brazo informativo PM-sin_dup | bitácora S162 ~17:00, ~20:15 |
| MOD-D censo | CERRADO: DECIDE NICOLÁS verificado; **Nicolás lo aprobó como CANDIDATO** (2026-10-26) | 5.465/5.465. PM: P1 0, P1b 1 (Láscar 2026-04-25 07:35: 0,973, y 1,1124 con la regla de MATLAB), P2 GANA neto −41 (S_K 49, S_PM 8, 50 bloques), M MEJORA (n 78). PM-geo5 VETADO (3), PM-b21 VETADO (28). Chillán SIN RESOLVER (6 de 7, p 8/128). 20 protegidas pasan de K < 1 a PM ≥ 1 MW | `9ea9a1786:experiments/_s162_modis_paquete/censo/evaluar_censo_salida.txt` (rama `claude/s162-modis-2-0dd578`; **la carpeta `censo/` no está en main**); bitácora S164 v13, v14, v16 |
| Vía «código MIROVA» MODIS (fase 3) | EN MAIN, APAGADA (#919, merge `d94f25191`) | Detección igual al port en 5.321/5.321 grillas del censo; arnés S142 idéntico byte a byte; **el camino desde el HDF no se pudo medir** (pyhdf en Windows) | bitácora S165 v3 a v6 |
| MOD-D fase 4 (V contra K, tres posiciones) | BORRADOR (`ff03538dd`). Verificador limpio: «sellar CON CAMBIOS CHICOS»; VF4-01 a VF4-12 arreglados; mutaciones finales sin commitear | Sin datos. Predicción escrita: PROPONER ADOPCIÓN con V. Población C (5.465) + E (2026-10-17 a 10-26, días con HEAD 200); referencia posterior a D-39; decide la tabla sola | `ff03538dd:experiments/_s166_modd_f4/PREREGISTRO_MODD_F4.md` §2, §4, §5, §7, §10 a §13 bis; `verificador/INFORME.md:1-30` |

### 1d. A/B diurno sobre K (D-10, tarea 1.32, issue #813 abierto)

| qué | estado | evidencia |
|---|---|---|
| Pre-registro | SELLADO por Nicolás (`68687d2d4`, tag `s163-diurno-k-sellado`; código `s163-diurno-k-codigo` sobre el mismo commit), PR #916; adenda 1 (días con hueco de NASA, regla (b')), PR #917 | bitácora S164 v17, v20, v22 |
| W1 (Láscar, 03-01 a 03-20) | terminada; informativa: DECIDE NICOLÁS CON M4 con (b') | bitácora S164 v19, v22 |
| W2 a W5 | terminadas, cobertura nocturna pareja (2.154, 1.429, 2.266 y 2.386 por brazo; 0 faltan) | bitácora S165 v1, S165 v7, S166 v6, S166 v17 |
| W6 (10-01 a 10-14) | CORRIENDO (40681454167) | `gh run view` hoy |
| Lectura de W2 a W6 | NO HECHA (`dias_excluidos_nasa.py` + `evaluar_con_exclusion.py --opcion-e e-ii`, verificador limpio de otro modelo, veredicto a Nicolás) | `tasks/BLOQUE_ARRANQUE_S167.md:105-108` |

Lo que pesa para el programa: un ADOPTAR de VIIRS 750 da DECIDE NICOLÁS; un sensor que adopta solo pide un flag por
sensor (A45); MODIS diurno no entra (pre-registro diurno §6.3 y §9).

## 2. Fases del §7 y arreglos del §8

| fase | estado | dónde |
|---|---|---|
| 0: instrumento, V375-A, MOD-A | **HECHA** (cada PR con prueba roja, mutaciones y verificador) | #902 a #905 (mergeados 2026-10-26 entre 02:31 y 02:43 UTC), #909, #914 |
| 1: V750-C, V750-F, MOD-E y despacho de sólo lectura | **HECHA salvo V750-B**. V375-B, V375-C y MOD-C corrieron por separado el 2026-10-24; no hubo despacho combinado | runs 40116289866, 40131572769, 40120713181 |
| PD1 | VIIRS 375 decidida (C13 en todos, D-48). VIIRS 750 **pendiente de V750-B**. MODIS: la caja es la «física» del censo, fija en `FAMILIAS["MODIS"]`; MOD-D f4 §3 no la mide | bitácora S164 v4; `pipeline/mirova_v750_codigo.py:100-115` |
| 2: V375-D, MOD-B | HECHA: V375-D descartado; MOD-B CUMPLE SIN DAÑO; MxD03 dentro del paquete (D-48) | §1b, §1c |
| 3: vías en `pipeline/` detrás de flag | **HECHA en los tres sensores, apagadas**: V750 #907, MODIS #919, V375 #921; MxD03 #920 y #922. #920 a #922 no cambian records (12 MODIS del NRT; bit a bit 40683093630 VERDE, control ROJO, con detecciones reales) | bitácora S166 v8, v14, v21 |
| PD3 (la vía reproduce al oráculo) | En parte. V750: local sí, runner pendiente (V750-A §4.1). MODIS: grillas del censo sí, desde el HDF pendiente (MOD-D f4 §8.2). V375: NO EQUIVALENTE por la regla de posición; la adenda 2 §8.6 lo vuelve a medir brazo por brazo al leer | §1 |
| 4: V750-A, V375-E, MOD-D | NO EMPEZADA en datos: tres pre-registros (V375-E con sólo la adenda 2 sellada; V750-A y MOD-D f4 en borrador) | §1 |
| 5: V750-E, V375-F, V750-D | NO EMPEZADA (el diurno sobre K corre aparte) | §1 |

| §8 | qué | estado |
|---|---|---|
| intro | «Existe R2.1 en #889» | **#889 cerrado** y reemplazado por **#909**, mergeado 2026-10-26 10:30 UTC (tag `pre-s163-merge-909`; toca `pipeline/fetch.py` y `scripts/run_pipeline.py`) |
| 1 | cobertura contra la referencia | HECHO, #904 (`scripts/evaluador_comun.py`: INVALIDO si una protegida falta en todos los brazos y el control la tiene, o si un volcán-sensor-día con pasadas de MIROVA tiene 0 records) |
| 2 | «no observado» | HECHO, #904 (`no_observado` fuera del denominador); la causa de cada ausencia en #914 |
| 3 | placebo y d′ en un evaluador común | HECHO, #905 (equivale a `evaluar_d25.py` en 250 casos); línea base sobre producción en #914 (P2 calibrado, 4,09 % y 3,11 %; BLOQUEA sale en 40,3 % sin efecto) |
| 4 | una sola definición de alerta | EN PARTE, #903: funciones nuevas por pasada; `alerta_protegida` y `pasadas_protegidas` siguen para los evaluadores sellados |
| 5 | P1b en dos direcciones y RUTINA | HECHO, #904 |
| 6 | estratificación por cenit y régimen (1.35) | HECHO, #914 (informa; por tramo, el placebo da SIN SUSTRATO en 75 de 78 filas) |

Abiertos que dejó #914 (cuerpo del PR): si un hueco de NASA invalida un A/B (aplicado después con D-48: se declara y se
excluye en todos los brazos), `--cobertura-json` en `nrt.yml` (sin hacer), ruido entre runners (sólo con un brazo gemelo).

## 3. Lo que falta para PD4, por sensor

**VIIRS 750**
1. 2026-11-03: generar `objetivos_v750b.json` (`--hasta 2026-11-02`) y la lista suplementaria, commitear con sus sha256 y
   despachar desde el tag con los tres cambios de la adenda 2 (§7 de la adenda). Consultar el cese de Suomi NPP en CMR.
2. Lectura: `separar_resultados_v750b.py`, `adenda1/leer_v750b.py` sobre `sellado/` (decide la ROI),
   `leer_posicion_v750b.py` (informa), N0/N1 (confirma V750-C). Si gana B2 o B4, paso DN-2. Esto cierra PD1 de 750.
3. La vía usa `roi_v750: def` en los 11 volcanes, que es la caja que pierde las protegidas de PCC. Cambiarla es tocar
   `pipeline/grillas_mirova.yaml` (A45), salvo que V750-A mida P en local sobre las grillas que guarda V750-B.
4. V750-A: medidor completo, verificador de `equivalencia_v750a.py`, incorporar la ROI de V750-B, sello (§b 2 de S167:
   después del medidor completo).
5. Run de V750-A (K, Kgeo, identidad P = O desde el gránulo; P, P-def, P-sinfiltro y O en local si alcanzan las grillas
   de V750-B), lectura y verificador limpio.
6. Sombra desde el 2026-11-03, 4 semanas o más: **no existe perfil de sombra** en `pipeline/profiles/` (A45 aparte).
7. Si la posición elegida no es radiante: PR a `procesar_grilla`, que comparten los tres sensores (A45).
8. PD4 por A45. Si V750-A no se adopta, V750-D pasa a A/B propio.

**VIIRS 375**
1. Despachar la corrida FAR después de W6 (`probe-s166-v375e-far.yml`, 14 trozos, 350 pasadas, ~2,5 h) y contar en el log
   que procesó lo pedido (A108).
2. Lectura local con `leer_posicion_v375e.py` sobre S159, S162, S162b y FAR: controles C1 a C7, equivalencia por brazo
   (§8.6), regla de posición, y después el §5 con el brazo elegido.
3. Aclarar si el cuerpo del pre-registro (§1 a §7, donde vive la regla de adopción §5.4) necesita sello propio: el tag
   dice que sigue en borrador.
4. Riesgo escrito antes de medir: con radiante, Isluga 06-17 y Láscar 10-01 (NOAA-21) vetan el §5.4 (a) aun con N-3.
5. Sombra desde el 2026-11-03 (30 noches o 40 alertas): perfil sin crear (A45).
6. PD4 por A45; si gana cercano o pico, el PR compartido del punto 7 de VIIRS 750. Después, V375-F.

**MODIS**
1. MOD-D fase 4: commitear las mutaciones sobre 53 escenarios, verificador corto de los arreglos VF4, sello de Nicolás
   con las 8 decisiones del §12 (§b 1 de S167).
2. Candado del §11: `poblacion_f4.json` (con HEAD 200 de los días de E), `probe_f4.py`, `identidad_f4.py`, externos,
   workflow, humo de ~25 pasadas (incluye Láscar 2026-04-25 07:35 y Chillán 2026-10-25 07:20), tag y verificador.
3. Despacho en tres tandas (~14 h de runner, cota alta), lectura y verificador. Identidad en rojo: no se lee el resto.
4. Sombra de 28 noches desde el 2026-11-03 o desde el sí (§12.6): perfil y su suma al NRT piden un sí aparte.
5. PD4 por A45 (encender `ENABLE_MODIS_CODIGO_MIROVA`; la vía lee su propio MxD03; los tres flags de #920 van aparte).

**Diurno**: W6, lectura de W2 a W6 con la adenda 1, verificador, veredicto a Nicolás; #813 se decide con eso.

## 4. Frases del programa que hoy son falsas o viejas

| línea | frase | qué la contradice |
|---|---|---|
| 24-26 | recall y magnitud «(K)» | Son de #864 y S159. #915 (2026-10-26): recall MODIS 62,5 % (n 16), V750 74,0 % (n 50), PCC V750 0,375×, Chillán bajo 0,7× en los tres sensores (bitácora S164 v15). Chillán MODIS en la población congelada: K/MIROVA 0,635 (n 7), no 0,485 (bitácora S162 ~17:15) |
| 27 | V375: «negativos 0,9 % con cota honesta de 8,5 %» | B2: 0,52 % [0,24; 1,12], cota 2,48 % |
| 27 | MODIS: «el "GANA" contra K NO RESUELTO (neg_resto 0 de 37, cota 9,4 %)» | MOD-C: 2 de 390, INDECIDIBLE; censo de MOD-D: P2 GANA, neto −41 |
| 40-42 | «Qué pieza las calla es SIN DATO: de ahí V750-C» | V750-C: interpolación lineal (dentro de la caja) y ROI (fuera) |
| 45-46 | «pierde 6 protegidas de Cordón Caulle» | V750-C cuenta 7, todas de PCC, sobre su población (`_s162_v750c/INFORME.md:26`); el 6 es del censo del oráculo. No reconcilié |
| 48 | cita `tasks/LOOP_OBJETIVOS.md:1121-1122` | La cita corrió: el texto «MIROVA 0,503, oráculo 0,517, K 0,239» está hoy en la entrada de S159 «gemelo de D25 medido; oblicuo y prompting entregados» (l. 2762 a las 13:05 UTC). Mejor citar por entrada (A101) |
| 55-57 | 12-oct «rescatados de LAADS o excluido» | V750-B y V375-E eligieron excluido |
| 64 | «2 A/B a la vez» | Práctica vigente: despachos uno a la vez dentro del cupo de 20 jobs, con el NRT usando 11 (`BLOQUE_ARRANQUE_S167.md:124`) |
| 68 | V750-C «(primero; 0 runs, sólo lectura, sin sello)» | Cerrado y verificado el 2026-10-24 |
| 75-77 | V750-F: «Nicolás corre ... en MATLAB Online (~15 min)» | Lo corrió la coordinadora S163 en el Chrome de Nicolás; regla identificada y portada |
| 78-82 | V750-B «combinable con V375-B, V375-C y MOD-C»; «5.746 pasadas, 79 protegidas, 177 alertas bajo 1 MW» | Los otros tres corrieron aparte; V750-B va el 2026-11-03. Ensayos: 5.841 objetivos + 20 `far_ref` (adenda 2 §6); 279 alertas y 103 protegidas en el ensayo hasta 10-25 (bloque S165 §a). Brazos reales: B0 a B5, K, N0/N1 |
| 83-88 | V750-A: brazos K, P, P-def, P-sinfiltro, Kgeo; «Sello y A45 para la implementación» | Brazos de hoy: además K×1,2, O, P-cercano y P-pico. La implementación ya está en main (#907) antes del sello |
| 97-100 | V375-A «primero, 0 runs»; «arreglo de `clase_mirova.py:65-75`» | Hecho en #903 con funciones nuevas; las viejas no se tocaron |
| 101-103 | V375-B «con 0 en 400 la cota baja a ~0,95 %»; V375-C «cajas de 13, 14 y 21» | B2 cerrado; C13 elegida |
| 104-105 | V375-D «sólo si B o C lo exigen» | Descartado (S163) |
| 112-113 | MOD-A «(trivial)» como pendiente | #902; la marca está en l. 202-204, pero el ítem de l. 112 sigue escrito como pendiente |
| 114-116 | MOD-B «~47 h de runner. Sello, tag y despacho» | Corrido (~15 h), CUMPLE SIN DAÑO, #920 en main apagado |
| 117 | MOD-C como pendiente | INDECIDIBLE, pasado al censo de MOD-D |
| 118-119 | MOD-D «brazos K, PM, PM sin MxD03»; «el déficit de Chillán (0,485) se juzga aquí» | Censo hecho (CANDIDATO); fase 4 con K, V, V-cercano, V-pico, placebo y V-grilla. Chillán quedó SIN RESOLVER en el censo |
| 120 | MOD-E «ablación local sobre las grillas del port» | Hecha con recortes nativos reales de MOD-C |
| 133 | fase 1, «un despacho de sólo lectura con V750-B, V375-B, V375-C y MOD-C» | No hubo despacho combinado |
| 135 | fase 3, «V750 primero», después de PD1 y PD2 | Las tres vías entraron a main antes de PD1 de VIIRS 750 |
| 151 | «338 en VIIRS 375 y 19 en VIIRS 750» | Conteos del verificador de S165 sobre la copia de hoy. Con insumos congelados y los mismos cortes: 330 en V375 (329 `far_tabla`; `PREREGISTRO_E.md` §8.4) y 20 en V750 (adenda 2 de V750-B §6) |
| 153-154 | «La distancia de MIROVA calza mejor con el píxel pico que con el centroide» | Matizada: H2 del verificador de S165 (`pico_ref` gana 56 a 3 y calza a media celda en 20 de 59; el centroide en 12 de 39) y VF4-12 del verificador de MOD-D f4 (la comparación ganadora es pico contra cercano). Sigue siendo SOSPECHA |
| 159 | «Existe R2.1 en #889 (borrador ...)» | #889 cerrado; #909 mergeado |
| 160-169 | «Falta:» ítems 1 a 6 | Hechos en #903, #904, #905 y #914 (tabla del §2) |
| 164-165 | «hoy sólo en `evaluar_d25.py`; MODIS no tiene evaluador» | El evaluador común (#904, #905) sirve a VIIRS y MODIS |
| 171-188 | §9 como decisiones abiertas | Aplicadas con D-48 el 2026-10-24 (bitácora S162 ~16:30), salvo el correo a Coppola (en espera por Nicolás), el tope de cordura de `store.py` (ítem 13, sin hacer) y el diurno (ítem 14), que corre sobre K antes del paquete |
| 175-176 | ítem 3, «equivalencia + censo + sombra en vez de tres A/B retrospectivos» | MOD-D f4 es un A/B retrospectivo completo (~14 h) más sombra; V750-A y V375-E también traen lectura retrospectiva |
| 210-219 | sesiones hijas; «la coordinadora (S162)»; `tasks/LOOP_INSTRUMENTO.md`, `LOOP_VIIRS750.md`, `LOOP_MODIS.md` | Coordinadora hoy: S167. Instrumento y VIIRS 375 cerraron (S162, S164); MODIS pasó por loop-modis-2, modd-fase3 y MOD-D fase 4; VIIRS 750 sigue como Loop VIIRS 750 2. En `loop/activo` y `main` sólo existen `LOOP_OBJETIVOS.md` y `LOOP_VIIRS375.md`; `LOOP_VIIRS750.md` vive en `5c45c0c07` y `LOOP_MODIS.md` en `e15e50153` |

Ajuste ya pedido y nunca escrito en el spec (bitácora S163 v13): «O2 cerrado y vara M = regla exacta de MATLAB en los tres
paquetes; V375-D fuera; D17 como pieza central de los paquetes».

## 5. Decisiones de Nicolás desde S162 que tocan el programa

| fecha | palabras (textuales donde la bitácora las trae) | efecto | fuente |
|---|---|---|---|
| 2026-10-24 | «más que sólo los frentes deberían haber planes ...»; «Sí, abre las cuatro sesiones hijas [...] cada una con su loop» | nacen el programa y las cuatro hijas | bitácora S162 ~15:45 y ~16:30 |
| 2026-10-24 | **D-48**: «sobre las decisiones mías haz lo que tú recomiendes» | aplicadas las 14 del §9; D25 NO SE ADOPTA; sellos D-48 de MOD-D, V750-B, V375-B/C, B2; más tarde PD1 de 375 | bitácora S162 ~16:30 |
| 2026-10-24 | «si esas sesiones y loops necesitan iniciar otras también lo tienen permitido» | las hijas abren sesiones | bitácora S162 ~16:40 |
| 2026-10-25 | «haz tú lo de MATLAB; el correo a Coppola aún no lo enviaremos; el resto haz lo que recomiendes» | O2 lo corre la coordinadora; correo en espera | bitácora S162 2026-10-25 «O2 sin sesión de MathWorks» |
| 2026-10-26 | «sí a mergear, sí a rebasar si es lo que recomiendas; borra los temporales que ya no tengan uso; el correo a Coppola aún no» | #900 a #906, #901, #898 | bitácora S163 v4 |
| 2026-10-26 | «¿no tienes que hacer esto mismo para los otros sensores? ... continúa con todo lo que falte ...» | O2 en MODIS y V375 | bitácora S163 v3 |
| 2026-10-26 | «continúa con todo lo que recomiendes apruebo los últimos 3 puntos» | cableado de la vía V750 (A45) y #909 | bitácora S163 v11 |
| 2026-10-26 | «Apruebo MOD-D como CANDIDATO: lleva la vía a pipeline/ con la regla de MATLAB, flag apagado, tag defensivo antes del primer edit.» | fase 3 de MODIS | bitácora S164 v16 |
| 2026-10-26 | «Sello el pre-registro diurno 68687d2d4 con las seis recomendaciones (e-ii en el caso e).» | A/B diurno sobre K | bitácora S164 v17 |
| 2026-10-27 | «Apruebo el merge de #919 ...», «... #920 ...», «... #921 ...», «... #922 ...», cada una con su sha y «Mergéalo tú.» | vías de MODIS y V375, y MxD03, en main apagadas | bitácora S165 v6, v9, v11, v14 |
| 2026-10-27 | «Sí: mide primero, sin tocar pipeline/, cuántas pasadas cambian con la regla "cercano" ...» | medición S165 de la posición | bitácora S165 v10 |
| 2026-10-27 | «Sí: no fijes la regla todavía; mídela como brazo (radiante, cercano y pico) en los A/B de cada sensor contra lo que publica MIROVA.» | ya escrita en el programa §7 | bitácora S165 v13 |
| 2026-10-27 | «Sello la adenda 2 de V750-B (...) commit 4dbd88dce). Pide antes una pasada corta del verificador sobre los 13 cambios.»; después «Lo que tú recomiendes» | sello pasa a `739edff39`; §b 3 (pérdida aceptada de PCC V750 10-10); **§b 5: no se enciende ninguna vía ni flag por ahora** | bitácora S166 v1, v3 |
| 2026-10-28 | «has lo que recomiendes y lo que nos ayude mas a lograr los objetivos, si algo nos esta confundiendo entonces no nos sirve mucho» | las alertas sólo OCR de Suomi NPP anteriores al 2026-10-09 se informan aparte; el «mismo objeto» salió de #924 | bitácora S166 v11, v12 |
| 2026-10-28 | «continua con todo lo que recomiendes, si lo mandas a papelara recuerda borrarlo de ahi tambien» | sello de la adenda 2 de V375-E con la vara nueva del paso 1 y N-3 | bitácora S166 v19; `PREREGISTRO_E.md` del tag, l. 9-15 |
| 2026-10-28 | «Apruebo los dos» | #923 y #924 | bitácora S166 v20 |

Aplicadas por la coordinadora bajo D-48, sin palabras nuevas de Nicolás: PD1 de 375 = C13 en todos (S164 v4); la regla de
los tres grupos para las protegidas SNPP (S163 v1); el punto (b) del candado de MOD-D (S163 ~05:45); la regla (b') de
huecos de NASA del diurno (S164 v20).

## 6. No verificado en esta lectura

- Batería de V375-E 140/140 y nulo 82/84 en LF: lo dicen S166 y el autor; no lo corrí.
- Si el cuerpo de `PREREGISTRO_E.md` necesita un sello propio, o si el de la adenda 2 alcanza.
- `tasks/LOOP_MODIS.md` posterior a `e15e50153` y el estado real de las mutaciones finales de MOD-D f4.
- El 6 contra 7 de protegidas de PCC con la caja por defecto (poblaciones distintas).
- Si la tarea 1.11 (cronología OVDAS) sigue bloqueando el perfil experimental (§6 del programa): no la busqué.
- Ningún evaluador re-corrido: las cifras de W1 a W5, del censo y de B2 salen de la bitácora o de los archivos de salida.
