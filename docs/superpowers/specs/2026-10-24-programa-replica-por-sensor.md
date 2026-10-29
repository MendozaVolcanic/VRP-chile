# Programa de investigación de la réplica de MIROVA, por sensor (S162, 2026-10-24)

Pedido de Nicolás (2026-10-24): «más que sólo los frentes deberían haber planes para continuar los estudios y
experimentos para alcanzar los objetivos después de la información nueva que salió de la fórmula de VIIRS 750 que
encontramos»; «cada plan puede ir en sesiones diferentes o hijas»; «cada una con su loop si es que se puede».

Borrador de un agente planificador (Opus) que leyó el código de MIROVA, las auditorías S158 y S158 R2, los frentes S159
y los informes de S162; revisado por la sesión coordinadora (S162). Rutas relativas a la raíz del repo; entre corchetes
la rama cuando el archivo no está en `loop/activo`. Lo no medido va como SOSPECHA o SIN DATO. **Nada de esto se adopta
sin pre-registro, sello de Nicolás, verificador con contexto limpio, tag defensivo y su sí (A45).**

Actualización de la coordinadora sobre el borrador: CM162 (cúmulos por matriz) ya tiene verificador
(`experiments/_s162_vuelta2/VERIFICADOR_CUMULOS_MATRIZ.md`): CONFIRMADO EN PARTE, efecto más chico (7 a 13 de 290
publicaciones V750 en K, 1 protegida cruza 1 MW), y es **una sola divergencia con el doble conteo: D17 sin de-solape ni
remuestreo**. Pegar fragmentos no es neutro (un negativo limpio de PCC sube de 0,447 a 3,03 MW).

> ⚠️ **S167, 2026-10-28 (A113): buena parte de este programa quedó vieja.** Las fases 0 a 3 están hechas o casi, y las
> tres vías «código MIROVA» ya están en `main`, apagadas. **El estado vigente y el camino a la adopción (PD4) de cada
> sensor están en el §12**, que se agregó al final. Cada pasaje que cayó lleva una marca al inicio con qué cayó y la
> evidencia; el texto viejo se conserva por historia. Insumo: un resumen de sólo lectura con evidencia por experimento
> (S167), del que la coordinadora comprobó por su cuenta los PR, V750-C, B2 de V375 y MOD-C. La bitácora
> (`tasks/LOOP_OBJETIVOS.md` §6) se cita por entrada (sesión y vuelta), no por línea, porque sus líneas corren.

## 1. Diagnóstico en una pantalla

Criterio de victoria: `docs/MISSION.md:59-103` (ninguna protegida perdida en lectura A; suma de errores bajo 1 MW;
recall, negativos limpios y razón de magnitud por sensor y por tramo A119).

> ⚠️ **S167 (A113)**: las cifras de esta tabla son de S159 y de la ventana de #864. Cayeron o cambiaron: el «0,9 % con
> cota de 8,5 %» de VIIRS 375 (V375-B2, run 40131572769: 6 de 1.165 noches limpias nuevas, 0,52 % [0,24; 1,12], cota
> 2,48 %, `experiments/_s162_v375/b2/resultado_run40131572769/INFORME.md`); el «GANA NO RESUELTO» de MODIS (MOD-C
> INDECIDIBLE con 2 de 390, y el censo de MOD-D da P2 GANA, neto −41, bitácora S164 v13 a v16); y la fila «Lo que
> falla hoy» de VIIRS 750, donde V750-C ya dijo qué calla las cumbres (§3). El audit del 2026-10-26 (#915) da recall
> MODIS 62,5 % (n 16) y VIIRS 750 74,0 % (n 50). Lo vigente, en el §12.

| | VIIRS 750 | VIIRS 375 | MODIS |
|---|---|---|---|
| Recall (K) | 72,9 % (n 48, 2026-08-24 a 10-23), fuera de banda (`experiments/_s161_estado_864/INFORME.md:29`); en el censo abr-oct K publica 77 de 78 protegidas y deja sin publicar 65 de 175 alertas bajo 1 MW ([s159-pruebas] `experiments/_s159/oraculo_censo/02_analizar_salida.txt`) | 96,8 % (n 93, ventana de #864) | 66,7 % (n 12); en la muestra del port K publica 48 de 50 protegidas y 32 de 42 bajo 1 MW (`experiments/_s159/portes/INFORME.md:66-68`) |
| Negativos limpios publicados (K) | 54 de 5.353 (1,01 %) | 3,7 %; 3,85 % ponderado en la muestra del port | 0,76 % (39 de 5.132) |
| Magnitud K/MIROVA | 0,510 [0,370; 0,733] n 115 ([s159-pruebas] `experiments/_s159/n/INFORME.md:156`); 0,178 sobre 50°, 0,163 Chillán sobre 50° (`experiments/_s159/oblicuo_paquete/INFORME.md:47,57`) | 0,651 [0,436; 0,848] (`portes/INFORME.md:110`); Chillán 0,65, Tupungatito 0,448 | 0,516 [0,311; 0,729] n 80; Chillán 0,485 n 7 |
| Mejor candidato medido | el código entero de MIROVA (port validado contra Octave en 791 de 791 escenas, `experiments/_s159/o1/INFORME.md:9-15`), remuestreado a la grilla GEO con la caja sensible (O-sens): 0 protegidas perdidas y 1 ganada, 15 negativos contra 54, ΔE −90; razón 0,999 [0,978; 1,007] | el mismo código con bandas I y grilla de 134 celdas: razón 1,000 [0,966; 1,019] n 61; negativos 0,9 % con cota honesta de 8,5 % | el mismo código (B22, MxD03, grilla 51 × 51): 50 de 50 protegidas, razón 1,006; el «GANA» contra K NO RESUELTO (neg_resto 0 de 37, cota 9,4 %) |
| Lo que falla hoy | detección y magnitud: cumbres en 0 MW, fragmentos oblicuos, modo de un píxel, fondo de anillo | magnitud (fondo y conteo); detección débil de Cordón Caulle y Tupungatito según la ROI | magnitud, geolocalización, cumbre nevada vista de lado (Chillán) |

### Lo nuevo que cambia la estrategia

1. **Las palancas sueltas sobre K quedan descartadas como camino a la paridad**: el fondo y la suma del código sobre
   K encienden de más (ΔE +12, `n/INFORME.md:265-272`); quitar la compuerta de 3 K no cambia ninguna publicación (0 de
   391, `n/INFORME.md:27-30`); D25 actúa como ganancia pareja (`lectura_s162/README.md`). El código entero en la grilla
   de MIROVA reproduce la magnitud al centésimo en los tres sensores. **El programa pasa de «probar palancas» a
   «adoptar el paquete del código por sensor, con brazos de diagnóstico adentro».**
2. **D25 sale del programa de la réplica**: MIROVA dilata el hueco, interpola con `fillmissing2`, suma todo y no
   recorta (`MIROVA_VIIRS750_VRP.m:63-85`); D25 en V750 publica el 100 % de las cumbres que K deja en 0 MW sin
   seleccionar (`experiments/_s162_vuelta1/VERIFICADOR_ENCENDIDAS.md`).
3. ⚠️ **S167 (A113)**: el «SIN DATO» del final ya tiene respuesta. V750-C (`experiments/_s162_v750c/INFORME.md`,
   corrección del verificador Fable 5.1) dice que son **dos piezas**: dentro de la caja sensible calla la interpolación
   lineal (el vecino más cercano recupera 23 de 38, en la celda de K) y fuera de ella (Tupungatito 17, PCC 4, Láscar 1)
   calla primero la ROI. El remuestreo nativo sigue sin brazo propio (lo mide N0/N1 dentro de V750-B). Texto original:
   **Las cumbres de 0 MW no las calla la compuerta**: el código de MIROVA, sin compuerta, tampoco las detecta (1 de
   60 con caja por defecto, 4 de 60 con la sensible, `n/INFORME.md:256,273-274`). Qué pieza las calla es SIN DATO: de
   ahí V750-C.
4. **D17 (remuestreo) deja de competir y pasa a ser pieza obligatoria**: con la grilla GEO el oráculo da 0,999 (±2 %)
   y 0,996 sobre 50°; MIROVA no agrupa, publica la unión. Los cúmulos por matriz (CM162) quedan subsumidos.
5. ⚠️ **S167 (A113)**: V750-C cuenta **7** protegidas perdidas con la caja por defecto, todas de PCC, sobre su propia
   población; el 6 de abajo es del censo del oráculo. Las dos cifras no se reconciliaron (poblaciones distintas). Y la
   vía de `main` usa hoy esa caja (`roi_v750: def` en los 11 volcanes, `pipeline/grillas_mirova.yaml`). Texto original:
   **La ROI por volcán es el mayor riesgo para las protegidas**: con la caja por defecto el paquete V750 pierde 6
   protegidas de Cordón Caulle (`oraculo_censo/INFORME.md:89-102`).
6. **No se busca aplanar la curva con el cenit sino reproducir la de MIROVA**, que también cae (más oblicua sobre
   menos oblicua de la misma noche: MIROVA 0,503, oráculo 0,517, K 0,239; `tasks/LOOP_OBJETIVOS.md:1121-1122`).
   ⚠️ **S167 (A113, A101)**: la cita de línea corrió; esas cifras están en la entrada «2026-10-21 (S159, dueña del
   loop): negativo con cráter, código OSF, verificador del oblicuo; guía y censo del oráculo lanzados» de la bitácora.
7. **El instrumento tiene un hueco que ningún control veía** (12-oct: 44 pasadas ausentes en todos los brazos, una
   protegida de 8,44 MW; `experiments/_s162_vuelta2/RECORD_FALTANTE_CHILLAN_12OCT.md`).
8. **Suomi NPP cesa el 2026-11-02 13:00 UTC**: toda ventana posterior es otro régimen.

## 2. Reglas comunes a todos los experimentos

> ⚠️ **S167 (A113)**: dos puntos cambiaron. (1) El 12-oct: V750-B y V375-E eligieron **excluirlo** en todos los
> brazos, no rescatar gránulos de LAADS. (2) La escala: la práctica vigente es **un despacho a la vez dentro del cupo de
> 20 jobs** (el NRT usa 11), siempre desde un tag (`tasks/BLOQUE_ARRANQUE_S167.md` §f). Se agrega una regla común
> decidida en S166: **las protegidas sólo OCR de Suomi NPP anteriores al 2026-10-09 se informan aparte y no deciden**,
> igual en el audit semanal (#924) y en los pre-registros (N-3 en V375-E). El resto de la sección sigue vigente.

- **Ventanas (A119, A104)**: **T**, tabla sola, decide: VIIRS 2026-04-01 a 06-12, MODIS desde 2026-03-01. **O**, tabla
  más OCR: 2026-06-13 a 2026-11-02 12:59 UTC, sin el 13 ni el 17-20 de octubre (D-29); el 12-oct sólo con los gránulos
  rescatados de LAADS o excluido en todos los brazos; siempre se informa la tabla sola al lado. **P**, prospectiva
  desde el 2026-11-03, sin Suomi NPP, confirmatoria.
- **Cortes**: #535 se informa por tramo aunque no separe brazos; adopción de K (2026-10-18 09:57 UTC) y cese de Suomi
  NPP para producción y sombra; TIF de MIROVA congelados desde 2026-09-22.
- **Métricas**: P1 veto de protegidas (lectura A, regla SN); P1b cruces de 1 MW **en las dos direcciones**; P2 suma
  bajo 1 MW por prueba de signos por bloque noche-volcán (D-45); M con comparador de ganancia pareja (D-28/D-30/D-32);
  placebo K × 1,2 obligatorio; todo por tramos de 10° de cenit, por volcán y por canal.
- **Escala**: 5 agentes y 2 A/B a la vez en todo el proyecto. Referencia congelada por hash.

## 3. VIIRS 750 (manda el código, decisión del 2026-10-21)

> ⚠️ **S167 (A113)**: estado de cada punto, con evidencia en el §12.1. **V750-C CERRADO** y verificado (dos piezas:
> interpolación y ROI). **V750-F CERRADO**: lo corrió la coordinadora S163 en la cuenta de MATLAB Online que Nicolás
> activó; la regla de `fillmissing2` quedó identificada (166 de 166 VRP) y portada a la vía. **V750-B SELLADO** (adenda
> 1 informativa; adenda 2 sellada por Nicolás el 2026-10-28, tag `s162-v750b-adenda2-sellada`), sin despachar: sale el
> 2026-11-03 **solo**, no combinado; sus brazos reales son B0 a B5, K y N0/N1. En el ensayo hasta el 2026-10-26 eran
> 5.841 objetivos más 20 lejanas (`far_ref`); al 2026-11-02 serán unos 6.000 (§9 de su pre-registro), no los 5.746 de
> abajo. **V750-A en BORRADOR**: la
> implementación ya está en `main` (#907, apagada) antes del sello, y sus brazos son hoy K, K × 1,2, O, P, P-def,
> P-sinfiltro, Kgeo, P-cercano y P-pico. V750-D y V750-E sin empezar. Texto original:

- **V750-C, ablación del oráculo** (primero; 0 runs, sólo lectura, sin sello). Hipótesis: el remuestreo a la grilla
  fija reparte el exceso de una cumbre tibia y la calla. Brazos dentro del oráculo sobre las grillas de N
  (`D:\vrp-trabajo\temporales\s159_n\run_39682867040\s159-n-chunk-*\grilla_*.npz`, 206 MB; que traigan la ventana
  nativa es SOSPECHA fuerte): O completo; O sin remuestreo; O con 8 vecinos; O sin recalcular la regresión del segundo
  pase; O con compuerta; O con recorte; O con K1 −0,8 y mínimo 0,010. Métrica: cuántas de las 55 cumbres en 0 MW y de
  los 6 negativos de F detecta cada brazo, razón en las 145 alertas, máscaras contra O. Decide si D17 es condición del
  paquete o si hay un paquete «sin remuestreo» para la detección.
- **V750-F, `fillmissing2` en MATLAB (O2)**: Nicolás corre `experiments/_s159/o1/o2_paquete/` en MATLAB Online (~15
  min). Cierra la banda de 1,82× en alertas de 1 píxel (`o1/INFORME.md:24-45`). No bloquea la publicación; sí M en 1
  píxel.
- **V750-B, ROI de MIROVA por volcán**. Hipótesis: en Cordón Caulle el calor está en el lacolito a 4,6-10,5 km del
  centro, en Tupungatito el cráter a 4,79 km NW del centro del TIF; MIROVA ajusta las ROI por volcán (el `.m` lo dice).
  Brazos: O-def, O-sens, caja 7 × 7 en el cráter del yaml, círculo `inner_radius_km` como caja sensible, O-sens sólo en
  PCC y Tupungatito. Ventanas T y O. Sustrato: 5.746 pasadas, 79 protegidas, 177 alertas bajo 1 MW, 5.476 negativos.
  1 run de sólo lectura, combinable con V375-B, V375-C y MOD-C. Necesita pre-registro y el sí para despachar.
- **V750-A, el paquete del código contra K** (adopción). Vía de proceso alternativa detrás de flag: port como
  procesador V750 + remuestreo con la regla GEO (centros `X0 ± 25.000` m, paso 750, `experiments/_s159/geo/INFORME.md:16-20`)
  + la ROI de V750-B, sin modo de un píxel ni tope D9 (N-5: el tope recorta una erupción real). Brazos: K, P, P-def,
  P-sinfiltro (publica todo lo que detecta), Kgeo (K con agrupación geográfica y huellas deduplicadas, diagnóstico de
  CM162). Métricas de §2 más identidad P contra oráculo pasada por pasada. Predicción: censo O-sens ΔE −90, 0
  protegidas perdidas. Sello y A45 para la implementación, el pre-registro y el despacho.
- **V750-D, cúmulos por matriz (CM162)**: verificado; se cierra como subsumido si V750-A se adopta; si no, A/B propio
  de Kgeo con PCC 2026-06-11 06:18 como caso de costo. Sonda L1B de fila/columna/`Bowtie_Deleted` en Chillán
  2026-10-14 06:18 como seguimiento (necesita el sí para despachar).
- **V750-E, rama diurna (D-10)**: 3 protegidas diurnas de Chillán sin record; después del paquete nocturno.
- **No es palanca**: el escalón de 50° del OSF (es del archivo, SOSPECHA fuerte).

## 4. VIIRS 375 (se traslada la estructura, no los números)

> ⚠️ **S167 (A113)**: estado de cada punto, con evidencia en el §12.2. **V375-A CERRADO** (#903: funciones nuevas al
> lado de la lectura A; las viejas de `clase_mirova.py` no se tocaron porque las usan evaluadores sellados). **V375-B
> CERRADO**, SILENCIO ACOTADO BAJO K (B2). **V375-C CERRADO** y PD1 decidida: C13 en todos (D-48, S164). **V375-D
> DESCARTADO** (con la vara de MATLAB la magnitud de C no cambia). **V375-E**: la vía está en `main` (#921, apagada) y
> sólo su **adenda 2 está sellada** (tag `s166-v375e-adenda2-sellada`); el cuerpo del pre-registro (§1 a §7, donde vive
> la regla de adopción §5.4) **sigue en borrador** según su propio encabezado. V375-F sin empezar. Texto original:

- **V375-A, higiene de la etiqueta de protegida** (primero, 0 runs): 5 de las 6 protegidas que «pierde» el port son
  alertas sólo OCR de Suomi NPP con fuentes a 9-24 km (`portes/INFORME.md:137-157`); con la tabla sola el port pierde 0
  de 29. Regla de «protegida de cráter» informada al lado de la lectura A, sin reemplazarla; arreglo de
  `scripts/clase_mirova.py:65-75` (cuenta FALSO_POSITIVO como protegida).
- **V375-B, negativos del port en neg_resto (D-36)**: 300 a 400 noches de 3.348; con 0 en 400 la cota baja a ~0,95 %.
  Pre-registro y sí; mismo despacho que V750-B.
- **V375-C, ROI en VIIRS 375**: brazos de V750-B con caja de 13, 14 y 21 celdas; 952 alertas bajo 1 MW.
- **V375-D, números propios de 375** (sólo si B o C lo exigen): conjunto cerrado de candidatos, elegido en T y validado
  en O (A115).
- **V375-E, paquete V375 contra K**: curva de razón por cenit comparada contra la de MIROVA, no contra 1 (la del port en
  375 es SIN DATO).
- **V375-F, Chillán sobre 3 MW** (port 0,939, n 6): después de V375-E.

## 5. MODIS (se traslada la estructura, no los números)

> ⚠️ **S167 (A113)**: ningún punto de esta sección sigue pendiente como está escrito; evidencia en el §12.3.
> **MOD-A CERRADO** (#902). **MOD-B CERRADO**, CUMPLE SIN DAÑO, con ~15 h de runner y no 47; MxD03 está en `main` con
> tres flags apagados (#920, más el aviso «sin dato» de #922) y el probe 40584157486 da 18 de 18 iguales en los dos
> sentidos. **MOD-C CERRADO**: INDECIDIBLE (2 de 390), y la pregunta pasó al censo de MOD-D. **MOD-E**: la ablación
> está hecha con los recortes nativos reales de MOD-C (no con las grillas del port; el método A no abre huecos), pero
> el efecto de D28 sobre la magnitud sigue SIN DATO y **D28 queda fuera de MOD-D fase 4** hasta localizar el método de
> MIROVA (`PREREGISTRO_MODD_F4.md` l. 82 y §14).
> **MOD-D**: el censo está hecho y Nicolás lo aprobó como CANDIDATO (2026-10-26); la vía está en `main`, apagada (#919);
> el pre-registro de la fase 4 (brazos K, V, V-cercano, V-pico, placebo y V-grilla) está en borrador en la rama
> `claude/s166-modd-f4`. Chillán quedó SIN RESOLVER en el censo (6 de 7, p 8/128), y su razón sobre la población
> congelada es 0,635 (n 7), no 0,485. Texto original:

- **MOD-A, la cita de MOD03** (trivial): renderizar la p. 4 de
  `documentacion/Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf` y citarla (P1 y P3 discrepan).
- **MOD-B, MxD03 sobre K (D-19, tarea 1.30)**: pre-registro v2 en `experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md`;
  M midió 2,85 km de corrimiento y 12 de 63 publicaciones cambian sobre 40°; con la geolocalización de 5 km el código
  pierde 3 protegidas. ~47 h de runner. Sello, tag y despacho.
- **MOD-C, negativos del port MODIS (D-36)**: 5.093 noches en neg_resto; mismo despacho.
- **MOD-D, paquete MODIS contra K**: brazos K, PM (port con D33 corregido), PM sin MxD03. El déficit de Chillán (0,485)
  se juzga aquí. MODIS sólo corre en Linux.
- **MOD-E, bow tie de MODIS (D28)**: ablación local sobre las grillas del port (`D:\vrp-trabajo\temporales\s159_portes\`).

## 6. Perfil experimental (no se mide contra MIROVA)

Candidatas de S162: las cumbres tibias de 1 píxel que el 750 de MIROVA calla y su 375 alerta en la misma pasada; el
lacolito de Cordón Caulle; la magnitud en geometría nativa. Se validan contra OVDAS y SWIR (A115); bloqueadas por la
tarea 1.11 (cronología OVDAS de Nicolás).

## 7. Fases y puntos de decisión

> ⚠️ **S167 (A113)**: la tabla se mantiene como plan, pero el avance real es otro (§12): fase 0 **hecha salvo el ítem 4
> del §8** (en parte); fase 2 **hecha**; fase 1
> hecha **salvo V750-B** (sin despacho combinado: V375-B, V375-C y MOD-C corrieron por separado el 2026-10-24); PD1
> decidida en VIIRS 375 (C13) y **pendiente en VIIRS 750** hasta leer V750-B; fase 3 **hecha en los tres sensores**,
> con las vías apagadas, y **entró antes de PD1 de VIIRS 750** (la vía V750 lleva la caja por defecto). PD3 en parte:
> V750 local sí y en runner pendiente; MODIS sobre las grillas del censo sí y desde el HDF pendiente; V375 NO
> EQUIVALENTE por dos causas: la regla de posición (8 pasadas) y el fondo sobre 4 píxeles (40 de 329 con la vara
> vieja; la vara nueva del paso 1, §8.6 b de V375-E, lo resuelve). Fase 4 sin datos todavía.

| fase | qué | punto de decisión |
|---|---|---|
| 0 | instrumento (§8), V375-A, MOD-A | PD0: cada arreglo con prueba roja y mutaciones; sin eso no se despacha ningún A/B |
| 1 | V750-C, V750-F (Nicolás), MOD-E, y un despacho de sólo lectura con V750-B, V375-B, V375-C y MOD-C | PD1: piezas obligatorias, caja por volcán, silencio de los ports |
| 2 | V375-D si hace falta; MOD-B | PD2: números de 375; MxD03 sola o en el paquete |
| 3 | vía de proceso «código MIROVA» en `pipeline/` detrás de flag (A45), V750 primero; prueba de equivalencia contra el oráculo | PD3: la vía reproduce al oráculo pasada por pasada |
| 4 | paquetes V750-A, V375-E, MOD-D (A/B o sombra) | PD4: adopción por A45 |
| 5 | V750-E diurno, V375-F, V750-D si V750-A no se adopta | |

Combinar en un brazo lo que el `.m` acopla (remuestreo, Test 1 como alerta, 3 × 3 con central, umbrales, sin
compuerta, segundo pase con regresión, fondo sin recorte, suma, sin modo de un píxel ni D9); la atribución pieza a
pieza va en la ablación local. Aislar lo separable con riesgo propio sobre las protegidas: ROI, filtro de publicación,
geolocalización MODIS, D33, diurno, agrupación.

**Regla de posición del record (decisión de Nicolás, 2026-10-27, S165).** Sus palabras: «Sí: no fijes la regla
todavía; mídela como brazo (radiante, cercano y pico) en los A/B de cada sensor contra lo que publica MIROVA».
- Los A/B de fase 4 (V750-A, V375-E y MOD-D) llevan tres brazos de posición sobre la misma detección:
  - **radiante**: centroide del cúmulo de la alertada más radiante, lo que hace hoy `procesar_grilla`;
  - **cercano**: el alertado más cercano al cráter;
  - **pico**: el píxel de mayor radiancia.
- ⚠️ **S167 (A113)**: el «338 y 19» de abajo es el conteo del verificador de S165 sobre la copia del día. Con los
  insumos congelados de cada pre-registro son **330 en VIIRS 375** (329 de la tabla, `PREREGISTRO_E.md` §8.4) y **20 en
  VIIRS 750** (adenda 2 de V750-B, §6). Y la frase del píxel pico quedó matizada: el pico calza a media celda en 20 de
  59 contra 12 de 39 del centroide (H2 del verificador de S165), y el verificador de MOD-D fase 4 (VF4-12) nota que la
  comparación ganadora es pico contra cercano. Sigue siendo SOSPECHA. Hoy los tres brazos están cableados en V750-B
  (adenda 2 sellada), V375-E (adenda 2 sellada, con N-3), V750-A y MOD-D fase 4 (borradores). Texto original:
- La vara es lo que publica MIROVA. Cuentan también las pasadas en que MIROVA publicó una fuente lejana
  (`FALSO_POSITIVO` de la tabla), que la medición de S165 no pudo mirar en VIIRS (338 en VIIRS 375 y 19 en VIIRS 750).
- Evidencia: `experiments/_s165_regla_posicion/INFORME.md` y `verificador/INFORME.md`. «Cercano» cambia 8 de 2.012
  pasadas en VIIRS 375 (4 protegidas), 1 de 5.321 en MODIS (una publicación de más) y 1 a 2 de 5.640 en VIIRS 750.
  La distancia de MIROVA calza mejor con el píxel pico que con el centroide.
- Si un pre-registro ya está sellado, los brazos entran por adenda, antes de ver los datos.

## 8. Arreglos del instrumento antes de cualquier A/B nuevo

> ⚠️ **S167 (A113)**: casi todo hecho. #889 se cerró y lo reemplazó **#909** (mergeado el 2026-10-26, tag
> `pre-s163-merge-909`). Ítems: 1 cobertura contra la referencia, **hecho** (#904, `scripts/evaluador_comun.py`); 2 «no
> observado», **hecho** (#904; la causa de cada ausencia en #914); 3 placebo y d′ en un evaluador común, **hecho** (#905,
> sirve también a MODIS; línea base en #914); 4 una sola definición de alerta, **en parte** (#903 agregó las funciones
> por pasada; `alerta_protegida` y `pasadas_protegidas` quedan para los evaluadores sellados); 5 P1b y RUTINA,
> **hecho** (#904); 6 estratificación por cenit y régimen, **hecho** (#914). Quedan abiertos de #914: `--cobertura-json`
> en `nrt.yml` y el ruido entre runners. Texto original:

Existe R2.1 en #889 (borrador, toca `pipeline/fetch.py` y `scripts/run_pipeline.py`: A45). Falta:
1. **Cobertura contra la referencia de MIROVA**: para cada brazo y producción, pasadas de la referencia sin record a
   ±120 s por volcán, sensor y día; una protegida sin record en todos los brazos que producción sí tiene, o un día con
   pasadas de MIROVA y cero records, es falla de cobertura antes de leer el veredicto. Va en el evaluador (sin A45).
2. **«No observado» como estado propio** (volcán fuera del gránulo, escenas inválidas), fuera del denominador.
3. **Placebo de ganancia y comparador d′ en un evaluador común** (hoy sólo en `evaluar_d25.py`; MODIS no tiene
   evaluador), con los placebos de D-44.
4. **Una sola definición de alerta** en `scripts/clase_mirova.py` (canal, SN, ±120 s, distancia compatible, fuente
   lejana, arreglo de FALSO_POSITIVO).
5. **P1b en las dos direcciones** y conteo de publicaciones sobre pasadas RUTINA (VE162-03).
6. **Estratificación automática por cenit y régimen** (tarea 1.35).

## 9. Decisiones para Nicolás (con recomendación)

> ⚠️ **S167 (A113)**: estas 14 decisiones ya están tomadas. Nicolás las delegó el 2026-10-24 («sobre las decisiones
> mías haz lo que tú recomiendes», D-48; bitácora S162 ~16:30) y se aplicaron. Excepciones: el correo a Coppola sigue
> en espera por decisión suya del 2026-10-25; el tope de cordura de `store.py` (13) está sin hacer; el diurno (14)
> corre hoy **sobre K** (D-10), antes del paquete; y dos no se cumplieron como estaban escritas: la 8 (V375-B y MOD-C
> corrieron aparte, no en el despacho de V750-B) y la 11 (la vía V750 entró a `pipeline/` antes de PD1 de VIIRS 750). El punto 3 (equivalencia + censo + sombra «en vez de» A/B
> retrospectivos) no se cumplió así: los tres pre-registros de fase 4 traen lectura retrospectiva, y MOD-D fase 4 es
> un A/B completo (~14 h). Las decisiones abiertas hoy están en el §12.5. Texto original:

1. D25: no adoptar, cerrar como «no es el fondo de MIROVA» (sí).
2. Pasar de palancas sueltas a un paquete por sensor con brazos de diagnóstico (sí).
3. Validar el paquete con equivalencia + censo + sombra prospectiva desde el 2026-11-03 en vez de tres A/B
   retrospectivos (sí; la alternativa clásica cuesta ~3 runs de ~12 h por sensor).
4. Etiqueta de protegida de cráter informada al lado; decide la lectura A (no cambiar la vara sin medir).
5. Filtro de publicación del paquete: mantener el predicado de cumbre y medir P-sinfiltro.
6. ROI de Cordón Caulle y Tupungatito: medirla y enviar el correo ya redactado a Coppola
   (`docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`).
7. Correr O2 en MATLAB Online (15 min, tú).
8. D-36: lote de 300 a 400 negativos en VIIRS 375 y MODIS, en el mismo despacho que V750-B.
9. MxD03: sellar el pre-registro v2 y correrlo; adoptarla dentro del paquete MODIS salvo que se atrase más de un mes.
10. #889: mergear con tag y sí, más la cobertura contra la referencia en un PR del evaluador.
11. Vía de proceso «código MIROVA» en `pipeline/` detrás de flag, con el remuestreo GEO, después de PD1.
12. Tope D9 fuera del paquete, medido.
13. Tope de cordura de `store.py` (R2-7) aparte, con tag y sí.
14. Diurno (D-10) después del paquete nocturno.

## 10. Qué no reabrir y qué cierres quedan rebajados

**Vigentes**: K (#850; conectiva `max` confirmada por el código, B22 por el port); lectura A, regla SN y corte de
1 MW; el fondo del código sobre K enciende de más; la compuerta sola no cambia la publicación; negativo limpio con
cráter refutado; pareo MODIS ±120 s; escalón de 50° por zonas de agregación refutado; K1 casi no decide (3 de 791);
COB; tareas 1.9 y 1.13; D-29.

**Rebajados (cada uno pide su marca A113)**: tarea 1.8 «el modo de un píxel no se toca» (midió publicaciones, no
magnitud); tarea 1.14 «D25 es la palanca que más mueve» y las tareas 1.29 y 1.33; AUDIT_S158 §0.1 «la brecha entera es
el fondo» (Etna, N = 1); AUDIT_S158 §0.3 sobre la compuerta; AUDIT_S158_R2 §2 «el port es vara a pocos por ciento»
(sólo con 2 o más píxeles); D-13 y la «cobertura PAREJA» de los A/B; D17 «consecuencia NO» y la tarea 1.36; el radio de
20 km de PCC (condicionado a V750-B); la tarea 1.7 (caja 5 × 5, medida con `_interp_geo`); F5-09 (ahora con
mecanismo, verificado como D17); «MIROVA usa MOD03» (en disputa hasta MOD-A). ⚠️ **S162, 2026-10-25 (A113)**: MOD-A resuelto en el PR #902 (Coppola
2026 Sci Data p. 4, con p. 3 y p. 6): MOD03 es insumo también en el NRT; el método del remuestreo sigue SIN LOCALIZAR.
D35 queda registrada en el PR #906 con el veredicto de MxD03 (CUMPLE SIN DAÑO).

## 11. Sesiones hijas (cada una con su loop)

> ⚠️ **S167 (A113)**: la tabla es la de S162. Las sesiones de instrumento y de VIIRS 375 cerraron (S162 y S164); MODIS
> pasó por Loop MODIS 2, la fase 3 y ahora «MOD-D fase 4»; VIIRS 375 sigue en «V375-E fase 4»; VIIRS 750 sigue en «Loop
> VIIRS 750 2». La coordinadora hoy es S167, no S162. En `loop/activo` sólo existen `LOOP_OBJETIVOS.md` y
> `LOOP_VIIRS375.md`; `LOOP_VIIRS750.md` vive en la rama de Loop VIIRS 750 2 y `LOOP_MODIS.md` en `e15e50153`. Las
> reglas entre loops siguen vigentes, salvo el «tope de 2 A/B»: hoy es un despacho a la vez (§2). Texto original:

| sesión | alcance | cola y bitácora propia |
|---|---|---|
| Instrumento | §8, V375-A, MOD-A | `tasks/LOOP_INSTRUMENTO.md` |
| VIIRS 750 | V750-C, V750-B (diseño del despacho combinado), V750-A, V750-D, V750-E | `tasks/LOOP_VIIRS750.md` |
| VIIRS 375 | V375-B a V375-F | `tasks/LOOP_VIIRS375.md` |
| MODIS | MOD-B a MOD-E | `tasks/LOOP_MODIS.md` |

Reglas entre loops: cada sesión en su worktree y su rama, sin tocar archivos de otra; nadie escribe en
`tasks/LOOP_OBJETIVOS.md` salvo la coordinadora (S162); **todo despacho a GitHub Actions se pide a la coordinadora**
(grupo de un solo pendiente, tope de 2 A/B); el despacho combinado de la fase 1 lo arma la coordinadora con los brazos
que entreguen VIIRS 750, VIIRS 375 y MODIS; nada en producción sin sello, verificador, tag y sí; parada si C: o D:
bajan de 3 GB.

## 12. Estado al 2026-10-28 y camino a la adopción (PD4), por sensor (S167)

Agregado por la coordinadora S167 a pedido de Nicolás («revisa el estado del plan de los 3 sensores y adaptalos o
actualizalos segun los nuevos resultados»). Reemplaza como estado vigente a las tablas de §1, §3 a §5, §7 y §8, que
quedan como historia con sus marcas. Lo no medido va como SOSPECHA o SIN DATO.

### 12.0 Lo que vale para los tres sensores

- **Las tres vías «código MIROVA» y MxD03 están en `main`, apagadas**: V750 (#907), MODIS (#919), V375 (#921), MxD03
  con tres flags (#920) y su aviso «sin dato» (#922). El único flag de estas familias encendido en producción es
  `ENABLE_MODIS_B22_PRIMARY` (K, desde #850).
- **#920 a #922 no cambian ningún record.** NRT: 12 records MODIS reescritos con el código nuevo, mismos campos, 0 con la
  vía (`experiments/_s166/nrt_campos_s166.py`). Bit a bit del run 40683093630 (día 2026-10-26, cuatro volcanes, mismo
  runner): VERDE en VIIRS 375 y 750, 44 records por lado, con control ROJO y detecciones reales en los dos lados
  (`experiments/_s166/bitabit_40683093630/`). No se repite.
- **Regla de posición como tres brazos** (radiante, cercano, pico; decisión de Nicolás del 2026-10-27, §7). Cableada en
  V750-B (adenda 2 sellada), V375-E (adenda 2 sellada) y en los borradores de V750-A y MOD-D fase 4. **Cada
  pre-registro elige su brazo por sensor** con su propia regla, escrita antes de ver los datos (V375-E §8.5, MOD-D
  fase 4 §6 bis, V750-A §6 bis). `procesar_grilla` sigue con «radiante» y es compartida por los tres sensores: si un
  sensor elige otra posición, hace falta un parámetro por sensor en esa función, y es un PR a `pipeline/` (A45).
- **Protegidas sólo OCR de Suomi NPP anteriores al 2026-10-09**: se informan aparte y no deciden (decisión de Nicolás,
  S166). Aplicada en el audit semanal (#924) y en V375-E (regla N-3). **Falta en V750-B**, que está sellado y es el
  primero que se lee (en la ventana O decide tabla más OCR, l. 106 de su pre-registro), y en V750-A. MOD-D no la
  necesita: MODIS no tiene canal de Suomi NPP.
- **El «mismo objeto» en la magnitud por noche queda ABIERTO.** El corte por `inner_radius_km` no sirve en PCC (radio
  20 km) y excluir las noches de Suomi NPP OCR escondía una bandera real de Chillán (bitácora S166 v12). Se retoma sólo
  con un criterio medido contra la referencia (A115).
- **Suomi NPP cesa el 2026-11-02 13:00 UTC.** Toda ventana posterior es otro régimen (ventana P del §2).
- **No existe ningún perfil de sombra** en `pipeline/profiles/`, y los tres pre-registros de fase 4 piden sombra
  prospectiva. Crearlo y sumarlo al NRT es A45 aparte, y pesa en el tiempo del NRT (50 min por job, A15).
- **A/B diurno sobre K (D-10, #813)**: W1 a W5 con cobertura pareja; W6 despachado (run 40681454167, en curso el
  2026-10-28). Su lectura con la
  adenda 1 decide el diurno de VIIRS 375; en VIIRS 750 un ADOPTAR va a DECIDE NICOLÁS porque ahí manda el código; MODIS
  diurno no entra.

### 12.1 VIIRS 750

**Cerrado**: V750-C (dos piezas: interpolación lineal dentro de la caja, ROI fuera; `experiments/_s162_v750c/INFORME.md`
con su verificador), V750-F (regla de `fillmissing2` identificada y portada, bitácora S163 v2, v6, v8), fase 3 (#907).
**Sellado sin datos**: V750-B con adendas 1 y 2. **Borrador**: V750-A (`5c45c0c07` en la rama de Loop VIIRS 750 2).

Lo que falta para PD4, en orden:
0. **Antes del 2026-11-03**: si Nicolás lo aprueba (§12.5), una adenda 3 corta de V750-B que aplique N-3, escrita
   antes de ver datos, con su verificador.
1. **2026-11-03**: objetivos de V750-B (`--hasta 2026-11-02`), lista suplementaria, sha256, tag y despacho desde el
   tag con los tres cambios de la adenda 2; consulta C-06 del cese de Suomi NPP en CMR.
2. Lectura de V750-B con sus lectores sellados (decide la ROI; N0/N1 confirma V750-C) y verificador limpio. **Esto
   cierra PD1 de VIIRS 750.**
3. Llevar la ROI elegida a la vía: hoy `pipeline/grillas_mirova.yaml` tiene `roi_v750: def` en los 11 volcanes, la caja
   que pierde las protegidas de PCC (A45).
4. V750-A: medidor completo de mutaciones (M1 a M85 sobre todos los escenarios; parte cuando termine la batería de
   identidad), verificador de `equivalencia_v750a.py` (lo pide su §11), agregar N-3, incorporar la ROI de V750-B,
   verificador limpio y sello. Su sello depende del resultado de V750-B (su encabezado lo dice).
5. Run de V750-A, lectura y verificador; PD3 en runner (identidad P contra el oráculo desde el gránulo).
6. Sombra prospectiva (perfil por crear, A45) y PD4 por A45. Si V750-A no se adopta, V750-D pasa a A/B propio.

**Es el sensor más lejos de PD4**: depende de V750-B, que recién sale el 2026-11-03.

### 12.2 VIIRS 375

**Cerrado**: V375-A (#903), V375-B (SILENCIO ACOTADO BAJO K), V375-C (C13 en todos, PD1 decidida), V375-D (descartado),
fase 3 (#921). **Sellado**: sólo la adenda 2 de V375-E (`67838f2a5`, tag `s166-v375e-adenda2-sellada`, con N-3 y la
vara nueva del paso 1). **En borrador**: el cuerpo de `PREREGISTRO_E.md` (§1 a §7, con la regla de adopción §5.4).

Lo que falta para PD4, en orden:
1. Despachar la corrida de pasadas lejanas (§8.8, desde el tag, rama de disparo `s166-v375e-far-disparo`, 14 trozos,
   ~2,5 h) **después de W6**, y contar en el log que procesó lo pedido (A108).
2. **Sellar el cuerpo del pre-registro** antes de leer: hoy su encabezado dice que sólo la adenda 2 está sellada, y el
   §5.4 es el que decide la adopción (decisión abierta, §12.5).
3. Lectura local con `leer_posicion_v375e.py` sobre las poblaciones S159, S162, S162b y la corrida lejana: controles C1
   a C7, equivalencia por brazo (§8.6), regla de posición y después el §5 con el brazo elegido; verificador limpio.
4. Riesgo escrito antes de medir: con «radiante», Isluga 2026-06-17 y Láscar 2026-10-01 (NOAA-21) vetan el §5.4 (a)
   aun con N-3. Si gana «cercano» o «pico», es el PR compartido a `procesar_grilla` (§12.0).
5. Sombra (30 noches o 40 alertas; perfil por crear, A45) y PD4 por A45. Después, V375-F.

**Es el sensor más cerca de PD4**: tiene sellada la parte nueva y no necesita un run largo, sólo la corrida lejana
(~2,5 h) y la lectura.

### 12.3 MODIS

**Cerrado**: MOD-A (#902), MOD-B (CUMPLE SIN DAÑO; MxD03 en `main` apagada, #920 y #922), MOD-C (INDECIDIBLE, pasado al
censo), la ablación de MOD-E (el efecto de D28 en la magnitud sigue SIN DATO y D28 queda fuera de la fase 4), censo
de MOD-D (Nicolás lo aprobó como CANDIDATO el 2026-10-26), fase 3 (#919). **Borrador**: el pre-registro de MOD-D fase
4 (rama `claude/s166-modd-f4`, `ff03538dd`; verificador limpio «sellar con cambios chicos», arreglos VF4-01 a VF4-12
hechos). Su §13 commiteado dice todavía 40 escenarios y 46 de 46 mutaciones; la batería de 53 y sus mutaciones
finales están SIN VERIFICAR (no commiteadas al 2026-10-28 13:30 UTC).

Lo que falta para PD4, en orden:
1. Commitear las mutaciones finales con el §13 al día, verificador corto de los arreglos VF4 y sello de Nicolás con
   las 8 decisiones de su §12 (§b 1 del bloque S167).
2. Candado del §11 (población con HEAD 200 en los días de la ventana E, probe, identidad, workflow, humo de ~25 pasadas
   que incluye Láscar 2026-04-25 07:35 y Chillán 2026-10-25 07:20), tag y verificador.
3. Despacho en tres tandas (~14 h de runner, cota alta), lectura y verificador. Si la identidad sale roja, no se lee
   el resto. PD3 desde el HDF se mide aquí (en Windows no se pudo, pyhdf).
4. Sombra de 28 noches (perfil por crear, A45) y PD4 por A45: encender `ENABLE_MODIS_CODIGO_MIROVA`; los tres flags de
   MxD03 van aparte.

**Es el segundo más cerca de PD4**: le faltan el sello, el candado de siete piezas y unas 14 h de runner. Chillán
(cumbre nevada vista de lado) se juzga en este A/B: en el censo quedó SIN RESOLVER.

### 12.4 Orden entre sensores

VIIRS 375 primero (parte nueva sellada; corrida lejana de ~2,5 h y lectura), MODIS después (sello, candado y ~14 h de
runner), VIIRS 750 al final (espera V750-B, que sale el 2026-11-03). Ninguno depende del otro, así que pueden avanzar
en paralelo; el orden es el de los despachos, que van de a uno dentro del cupo de 20 jobs: W6 del diurno, la corrida
lejana de V375-E, V750-B el 2026-11-03 y MOD-D fase 4 cuando tenga sello y candado. La posición se elige **por sensor**
con la regla de cada pre-registro; la implementación en `procesar_grilla` lleva un parámetro por sensor (§12.0).

### 12.5 Decisiones abiertas para Nicolás (con recomendación)

**DECIDIDAS el 2026-10-29 (~13:00 UTC)**: Nicolás, en el chat de la coordinadora S167, ante la pregunta «¿Apruebas las
siete recomendaciones y revisar primero las 13 diurnas?»: «Sí a todo». Quedan aprobadas las siete tal como están
escritas abajo, con sus condiciones (los sellos de MOD-D fase 4 y del cuerpo de V375-E, después de su verificador
corto; el perfil de sombra se prepara en un PR con tag y se enciende con otro sí; la adenda 3 de V750-B antes del
despacho), y para el A/B diurno (#813) se clasifican primero, sólo lectura, las 13 publicaciones diurnas que caen en
pasadas que MIROVA no lista.

1. **Sello de MOD-D fase 4**: sellar cuando sus mutaciones salgan atrapadas por aserción y un verificador corto
   revise los arreglos VF4. *Recomendación: sí, en esas condiciones.*
2. **Sello de V750-A**: espera el medidor completo de mutaciones, el verificador de `equivalencia_v750a.py` y el
   resultado de V750-B (la ROI). *Recomendación: esperar.*
3. **Sello del cuerpo de V375-E** (§1 a §7), hoy en borrador mientras su adenda 2 está sellada. *Recomendación:
   sellarlo antes de leer, tras un verificador corto que compruebe que el cuerpo y la adenda 2 no se contradicen (sobre
   todo el §5.4 con N-3 y los brazos de posición).*
4. **Perfil de sombra**: ninguno existe y los tres pre-registros lo piden desde el 2026-11-03 (28 a 30 noches o 4
   semanas). Postergarlo hasta después de cada A/B suma unas 4 semanas a cada PD4. *Recomendación: medir ahora el
   costo en el tiempo del NRT y preparar un solo perfil aislado con las tres vías encendidas, en un PR con tag, para
   encenderlo con su sí desde el 2026-11-03; nada de eso toca lo que publica producción.*
5. **N-3 en V750-B**: V750-B está sellado sin la regla de las protegidas sólo OCR de Suomi NPP, que Nicolás pidió tratar
   igual en el audit y en los pre-registros. *Recomendación: una adenda 3 corta antes del despacho del 2026-11-03,
   escrita antes de ver datos, con verificador; y lo mismo en V750-A antes de su sello.*
6. **Regla de posición**: cada pre-registro la elige por sensor. *Recomendación: respetar eso y, al implementar, un
   parámetro por sensor en `procesar_grilla` (A45), en vez de esperar a leer los tres.*
7. **El «mismo objeto» de la magnitud**: *Recomendación: dejarlo abierto hasta tener un criterio medido.*

⚠️ **S167, verificador limpio (Sonnet) de esta sección**: LISTO CON CAMBIOS, 8 hallazgos de gravedad 2 o 3 y 6 de
gravedad 1, todos aplicados (orden entre sensores, posición por sensor, sombra, MOD-E, N-3 en V750-B, §9, V750-A y
V375). Informe en el scratchpad de S167, copiado a `experiments/_s167/verificador_programa/INFORME.md`.
