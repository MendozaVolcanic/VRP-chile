# Verificador con contexto limpio del evaluador de D25 sobre K (S157, tarea 1.29)

**Veredicto global: PARCIAL.** La aritmética del instrumento está bien (mediana ponderada, bootstrap por bloques,
percentil, estratos, P1, P1b, P2 por pasada, SN y original, cableado, cobertura, versión). Pero tal como está hoy el
evaluador no puede despacharse: (1) con el modo de calibración que el propio código llama sellado no pasa su control
positivo del candado; (2) un estrato de M INDECIDIBLE convierte un NO CUMPLE por P2 en INDECIDIBLE; (3) la mutación
del corte de 40° que el candado exige atrapar no la atrapa el caso que se escribió para eso; (4) los estratos que
deciden están dominados por un volcán (Chillán en V1, Láscar en V2), dependencia que ni los bloques noche-volcán ni la
calibración pueden ver por construcción.

Alcance: worktree `D:\vrp-trabajo\s157-prereg-d25`, rama `s157-prereg-d25` (HEAD 085972efb, archivos del evaluador
sin commitear). No edité ningún archivo existente. Mis scripts y su salida están en esta carpeta; los temporales en
`D:\vrp-trabajo\temporales\verif_eval\`. Todo con `PYTHONDONTWRITEBYTECODE=1`.

| script | qué hace | salida |
|---|---|---|
| `v1_unidades.py` | funciones puras del evaluador importadas, sin copiar | `v1_salida.txt` |
| `v2_casos.py` | casos de punta a punta con la maquinaria de `probar_evaluar_d25.py` (importada) y copias mutadas del evaluador en temporales | `v2_salida.txt` |
| `v3_snpp_hito.py` | exclusión de Suomi NPP contra el hito del 2026-10-09; pasadas sin cenit | `v3_salida.txt` |
| `v4_estratos_reales.py` | composición de los estratos reales y tres nulos de calibración sobre los pares de `calibracion_previa.py` | `v4_salida.txt` |

Línea base: `probar_salida.txt` termina en `RESUMEN: 20 de 20 casos OK` (corrida del autor, árbol sin tocar por mí
durante esa corrida salvo la creación de esta carpeta).

---

## Hallazgos (por gravedad, 1 = más grave)

### H1 (gravedad 1). Con la calibración «sellada» el evaluador no pasa su propio control positivo; las pruebas pasan sólo con un modo que el texto no autoriza, y los dos textos para el sello no dicen lo mismo

- **Dónde.** `evaluar_d25.py:76` (`CALIB_MODO = "ambos"`), `:355`; `probar_evaluar_d25.py:182` (`mej = ["--calibracion", "mejora"]`) usado en todos los casos de magnitud (`:217`, `:223`, `:229`, `:234`, `:238`, `:242`). `PREREGISTRO.md:180` y `:256` («MEJORA o EMPEORA en 5 % o menos») contra `RESUMEN_SELLO.md` («falsas mejoras en 5 % o menos»).
- **Qué pasa.** El candado (§7) exige: «positivo de M (magnitud de VIIRS 750 de D llevada hacia MIROVA a la mitad de distancia en log: MEJORA)». Con el modo sellado ese caso da INDECIDIBLE. El caso `sellada` sólo se imprime, no se asierta.
- **Cómo se ve** (`D:\vrp-trabajo\temporales\s157d25\prueba\sellada.txt`, corrida del autor):
  ```
  VIIRS750|z<=40  decide n 19 noches 18 | ... d -0.086 [-0.213, -0.049] | nulo MEJORA 0.010 EMPEORA 0.045 MAL CALIBRADA | poder None -> INDECIDIBLE
  VIIRS750|z>40   decide n 18 noches 10 | ... d -0.254 [-0.392, -0.191] | nulo MEJORA 0.030 EMPEORA 0.050 MAL CALIBRADA | poder None -> INDECIDIBLE
  == VEREDICTO DE LA VENTANA V1 ...: INDECIDIBLE
  ```
  Ojo: en este caso todos los pares tienen e = a/2 < a (D a mitad de camino), así que el nulo sellado es simétrico y
  el EMPEORA no viene del sesgo «K ya calza con MIROVA»: viene del ruido binomial alrededor del nivel nominal (H5).
- **Estado del sello.** En el repo `PREREGISTRO.md` sigue rotulado «BORRADOR v2 PARA EL SELLO» (línea 3) y no hay
  commit de sello; el evaluador llama «texto sellado» al modo `ambos`. SOSPECHA: no puedo ver si Nicolás selló, ni
  sobre cuál de los dos textos. Si selló leyendo `RESUMEN_SELLO.md`, lo que aprobó es el modo `mejora`.
- **Reproducir.** `grep -n "sellada\|mejora750" probar_salida.txt`; leer `...\prueba\sellada.txt` líneas 30-31.
- **Confianza.** Alta.
- **Cambio propuesto.** Antes del despacho, adenda con «sí» de Nicolás que fije UNA calibración (ver H5 para cuál) y
  que la escriba igual en `PREREGISTRO.md` y `RESUMEN_SELLO.md`; que el caso positivo del candado corra con el modo
  que decide y lo asierte; que `CALIB_MODO` por defecto sea el adoptado.

### H2 (gravedad 2). Un estrato de M INDECIDIBLE (por calibración) esconde un P2 PIERDE: NO CUMPLE pasa a INDECIDIBLE

- **Dónde.** `evaluar_d25.py:388-393`: el `if "INDECIDIBLE" in p1 + p2 + list(m.values())` va antes que `if "PIERDE" in p2`.
- **Qué pasa.** §8 d: «P1 VETADO, o P2 PIERDE en algún sensor y ventana: NO CUMPLE». En F/K el único INDECIDIBLE de
  ese orden venía de los controles (todo o nada); acá M agrega un INDECIDIBLE por estrato que no dice nada sobre P2.
  Con el modo `ambos` y 5 de 8 estratos mal calibrados en los datos reales (`calibracion_previa_salida.txt`), un P2
  PIERDE real terminaría en «repetición dirigida» en vez de «no se adopta».
- **Cómo se ve.**
  `v1_salida.txt`: `V1d global_ventana(P2 PIERDE, un estrato de M INDECIDIBLE): ('INDECIDIBLE', False, False)` y
  `global_ventana(P2 PIERDE, M todo NEUTRO): ('NO CUMPLE (suma de errores)', False, False)`.
  De punta a punta, `v2_salida.txt` (D con VIIRS 750 a mitad de camino y 30 negativos publicados):
  ```
  B masc sellada (ambos): P2 V375 PIERDE | M V750 {... 'INDECIDIBLE', ... 'INDECIDIBLE'} | estado INDECIDIBLE
  B masc mejora: P2 V375 PIERDE | M V750 {... 'MEJORA', ... 'MEJORA'} | estado NO CUMPLE (suma de errores)
  ```
- **Confianza.** Alta.
- **Cambio propuesto.** Orden: controles generales, VETADO, PIERDE, luego INDECIDIBLE de P1 y de M. Un INDECIDIBLE de
  M bloquea CUMPLE y SIN EFECTO, nunca un NO CUMPLE ya ganado. Prueba con nombre para esto (hoy no hay).

### H3 (gravedad 2). La mutación del corte de 40° a 50° no la atrapa el caso «corte»

- **Dónde.** `probar_evaluar_d25.py:241-245`.
- **Qué pasa.** El caso mueve a mitad de camino los pares sin kernel con cenit de 40 a 50°. Con el corte en 50 esos
  23 pares entran a un estrato de 65 donde los otros 42 tienen d = 0 exacto: la mediana sigue en 0 y el veredicto es
  el mismo. El candado §7 pide «mutación del corte de 40° a 50° cae por una prueba con nombre».
- **Cómo se ve** (`v2_salida.txt`, copia del evaluador con `CORTE_CENIT = 50.0`):
  ```
  A corte_mut (CORTE 50): estado SIN EFECTO | M sin_kernel z<=40 NEUTRO (n 65, d mediana +0.0000, ic [0.0, 0.0]) | n movidos 40-50° 23
     el caso 'corte' de las pruebas PASA (no la ve) con la mutación
  ```
  La corrida del autor lo confirma con la suite entera: `corte_50 NO ATRAPADA (20 de 20 OK)` (`mutaciones_salida.txt`).
- **Confianza.** Alta para el caso «corte».
- **Cambio propuesto.** Prueba de unidad directa: `estrato("Isluga|VIIRS375|...", 45.0) == ("VIIRS375|sin_kernel|z>40", "bloquea")`
  y `estrato(..., 40.0)` en `z<=40`; o un caso de punta a punta donde los pares de 40 a 50° sean mayoría del estrato.

### H4 (gravedad 2). Los estratos que deciden los domina un volcán; la dependencia entre noches de un mismo volcán no la absorben los bloques ni la puede ver la calibración

- **Dónde.** Diseño (`PREREGISTRO.md:157`, bloques noche-volcán) e implementación fiel (`evaluar_d25.py:342`, `:352`, `:354`).
- **Qué pasa.** El bloque es noche-volcán. Un efecto de D25 que depende del volcán (lo que la tarea 1.14 midió:
  ×1,72 Isluga, ×2,37 Tupungatito) es el mismo en todas las noches de ese volcán, así que esas noches no son
  independientes para la pregunta «D queda más cerca de MIROVA». La calibración sortea el signo por noche-volcán, de
  modo que por construcción no puede detectar esta dependencia. Con el signo sorteado por volcán, la misma regla da
  MEJORA o EMPEORA en 13 a 55 % de las repeticiones.
- **Cómo se ve** (`v4_salida.txt`, pares reales de K, efecto del probe):
  ```
  V1 VIIRS750|z<=40  n 29 bloques 27 volcanes 5 (mayor NevadosDeChillan 13 = 45 %) | simétrico MEJORA 0.030 EMPEORA 0.020 | simétrico signo por volcán MEJORA 0.135 EMPEORA 0.140
  V1 VIIRS750|z>40   n 23 bloques 14 volcanes 4 (mayor NevadosDeChillan 19 = 83 %) | simétrico MEJORA 0.055 EMPEORA 0.035 | simétrico signo por volcán MEJORA 0.545 EMPEORA 0.455
  V1 VIIRS375|sin_kernel|z<=40 n 103 bloques 82 volcanes 4 (mayor Isluga 44 = 43 %) | ... signo por volcán MEJORA 0.365 EMPEORA 0.280
  V2 VIIRS750|z<=40  n 64 bloques 64 volcanes 4 (mayor Lascar 41 = 64 %) | ... signo por volcán MEJORA 0.545 EMPEORA 0.455
  V2 VIIRS750|z>40   n 27 bloques 22 volcanes 3 (mayor Lascar 24 = 89 %) | ... signo por volcán MEJORA 0.535 EMPEORA 0.465
  ```
  Consecuencia: «MEJORA en cada ventana» puede cumplirse con Chillán en V1 y Láscar en V2 y nada más, que es justo
  la forma en que la regla de §8 d (H9 del verificador anterior) quería evitar un CUMPLE por un estrato cualquiera.
- **Límite.** El efecto usado es constante (×1,09 y ×1,14, como en `calibracion_previa.py`); con el efecto real del
  A/B los números cambian. La composición por volcán no cambia.
- **Confianza.** Alta en la composición; media en la magnitud del sesgo.
- **Cambio propuesto (decisión de Nicolás).** Informar M por volcán en la primera línea del veredicto y exigir para
  CUMPLE que la mediana de d por volcán sea negativa en al menos dos volcanes del estrato (o en la mayoría), o un
  bootstrap por volcán como sensibilidad. Si no, decirlo como límite en §9.

### H5 (gravedad 2). La calibración: el diagnóstico del autor es correcto, pero el modo «mejora» deja dos errores sin control y el nulo sellado subestima los falsos MEJORA

Respuesta a la pregunta 3, por partes:

1. **El diagnóstico es correcto, y tiene dos causas, no una.**
   - Ruido binomial con el tope igual al nivel nominal de dos colas: una regla PERFECTA (5 % de falsos) se declara mal
     calibrada en 42 % de las veces (`v1_salida.txt`: `V1g regla con tasa real de falsos 0.050: P(más de 10 de 200) = 0.417`;
     con 2,5 %, la cola de una sola dirección, `0.013`). Esto solo ya explica el INDECIDIBLE del caso `sellada` (H1),
     donde no hay ningún par cerca de MIROVA.
   - Sesgo del nulo sellado: si |log(K/M)| < e, cambiar el signo de log(D/K) aleja de MIROVA en las dos direcciones,
     así que el nulo tiene mediana de d mayor que 0 y su EMPEORA no es un falso. Sintético con 40 bloques
     (`V1h razón K/MIROVA 1.0: nulo sellado ... EMPEORA 0.185 | nulo simétrico ... EMPEORA 0.025`); real, estratos con
     kernel de V1 y V2: `sellado ... EMPEORA 0.160` y `0.180` contra `simétrico ... 0.025` (`v4_salida.txt`).
2. **El sorteo por bloque es una implementación legítima del propósito declarado** («por ejemplo porque los bloques de
   noche no alcanzan a absorber la dependencia», `PREREGISTRO.md:181`): con el signo por par el nulo no tiene
   dependencia dentro de la noche y la calibración queda ciega a eso. Medido (`v2_salida.txt`, línea F, la misma
   prueba de unidad de `probar_evaluar_d25.py:310-320`):
   `signo por par: boot por pasada 0.025, por bloques 0.040 | signo por bloque: por pasada 0.235, por bloques 0.045`.
   Con signo por par la prueba de unidad no distingue (0,025 contra 0,040). PERO el texto no dice la unidad del
   sorteo y el encabezado del evaluador (`evaluar_d25.py:4-5`) exige cambiar el pre-registro en el mismo commit;
   `git status` muestra `PREREGISTRO.md` sin modificar. Debe ir en la adenda.
3. **Lo que el modo «mejora» deja sin control.**
   - En el estrato que sólo **bloquea** (VIIRS 375 sin kernel, > 40°) la única decisión es EMPEORA, y el modo
     `mejora` calibra la cola que ahí no cuenta (`evaluar_d25.py:355`). Ahí la decisión queda sin calibrar, y además
     un falso MEJORA alto lo pone INDECIDIBLE aunque un MEJORA no cuente.
   - En los estratos que deciden, un EMPEORA lleva a «NO CUMPLE (M empeora)» (H6) sin calibración. Es un error
     conservador, pero cierra un A/B de 30 h.
   - El nulo sellado está sesgado hacia d > 0, así que su tasa de MEJORA **subestima** la de un nulo de mediana 0. Sobre
     los pares reales: V1 VIIRS 750 > 40°, `sellado MEJORA 0.015` contra `simétrico MEJORA 0.055` (sobre el tope del 5 %);
     V1 VIIRS 750 ≤ 40°, `0.010` contra `0.030` (`v4_salida.txt`).
- **Cambio propuesto (para la adenda).** Calibrar con el nulo **simétrico**: el signo de d (no el de log D/K) sorteado
  por bloque, que tiene mediana 0 por construcción y deja las dos colas comparables. Medir cada cola por separado y
  con el tope por cola (2,5 % nominal, tope 5 % de 200, que con una regla perfecta falla 1,3 % de las veces). Cola
  que se exige según el estrato: las dos donde decide, sólo EMPEORA donde bloquea.
- **Confianza.** Alta en el diagnóstico y en los tres huecos; la propuesta es mía y es decisión de Nicolás.

### H6 (gravedad 3). «M EMPEORA» sin mejora es NO CUMPLE por invención, y la combinación de ventanas es asimétrica

- **Dónde.** `evaluar_d25.py:398-399` y `:616-620`.
- **Qué pasa.** §8 d no tiene fila para «EMPEORA sin MEJORA»; el estrato que bloquea dice «un EMPEORA bloquea CUMPLE»
  (`PREREGISTRO.md:167`), no «NO CUMPLE». El código crea «NO CUMPLE (M empeora)», que `combinar` trata como «malo» y
  devuelve antes de llegar a la rama `:619-620`, que quería «DECIDE NICOLAS» cuando hay mejora en alguna ventana. El
  mismo par mejora/empeora da distinto según caiga en una ventana o en dos.
- **Cómo se ve** (`v1_salida.txt`):
  ```
  V1e combinar(v1_mejora, v2_empeora) -> NO CUMPLE (M empeora)
  V1e combinar(v1_mixto, v2_mejora) -> DECIDE NICOLAS (M empeora en alguna ventana)
  ```
- **Confianza.** Alta.
- **Cambio propuesto.** Que la adenda diga qué es un EMPEORA solo (¿NO CUMPLE o decide Nicolás?) y que `combinar`
  trate igual el par mejora/empeora dentro y entre ventanas; prueba con nombre para los dos casos.

### H7 (gravedad 3). PENDIENTE DE REPETICIÓN sin vía para resolverse

- **Dónde.** `evaluar_d25.py:298-299` y `:390-391`; `main()` no tiene `--repeticion` (F/K sí: `evaluar_fk.py:543-570`).
- **Qué pasa.** §5 P1: «en V2, PENDIENTE DE REPETICIÓN (repetición dirigida de F/K, tope dos)». F/K reevalúa con los
  jobs repetidos y clasifica la pérdida como neta o ruido confirmado; este evaluador no puede leer una repetición, así
  que una pérdida en V2 queda PENDIENTE para siempre o se resuelve a mano.
- **Confianza.** Alta.
- **Cambio propuesto.** Portar `--repeticion` de F/K (misma semántica) con su caso de prueba.

### H8 (gravedad 3). La huella de D25 prueba que el flag se leyó, no que la palanca actuó

- **Dónde.** `evaluar_d25.py:497-503`; la clave la escriben `pipeline/process_viirs.py:2242-2244` y
  `pipeline/process_viirs_mod.py:1503-1505` en TODO record con el flag encendido, haya corrido o no el bloque de D25.
- **Qué pasa.** Si D25 no llegara a actuar (el defecto de A118: el flag llega a un consumidor y no a otro), D tendría
  la huella, la magnitud idéntica a K, M NEUTRO en todo y el veredicto sería «SIN EFECTO», que se lee como «D25 no mueve
  la magnitud sobre K». Lo muestra el propio caso `nulo` (D = K más la huella): `estado SIN EFECTO`, controles OK.
- **Falso rojo: no.** Comprobé que `calculate_vrp` sólo deja de producir record por `return None` tempranos
  (`process_viirs.py:810`, `process_viirs_mod.py:496/542/569`) y que no hay otro camino que cree records
  (`scripts/run_pipeline.py:235-337`, sólo `calculate_vrp` y `store.append_record`); `store.py` no filtra claves. Un
  record de D con cúmulo y sin la huella no puede salir de un D bien cableado.
- **Confianza.** Alta.
- **Cambio propuesto.** Control «la palanca actuó», por sensor: `diag_L_bg_vecinos_w_m2_sr_um` no nulo en los records
  de D con píxeles alertados del bloque contextual, y al menos un par con magnitud de D distinta de K; si falla, M de
  ese sensor INDECIDIBLE, no SIN EFECTO.

### H9 (gravedad 3). Reglas del pre-registro sin caso de prueba

Leído de la lista de casos de `probar_evaluar_d25.py:7-33` y de lo que cada caso asierta:
- Cobertura del control contra histórico y producción (`cortos`): ningún caso la ejercita, y las pruebas arman los
  brazos con la MISMA copia unida que usa `claves_cobertura` como referencia, así que no puede fallar dentro de la
  suite. El control funciona (`v2_salida.txt`: `C cob: quitadas 23 de 115 pasadas VIIRS 375 de Lascar en los tres brazos -> cobertura_ok False, estado INDECIDIBLE`), pero nada lo vigila.
- Paridad de cobertura entre brazos (`mal`), versión del producto, referencia congelada alterada, `triggered_test1`,
  `PROFILE_NAME`/`DATA_SUBDIR`, huella en K o K' (rama `elif huella`): sin caso. La versión funciona
  (`D version: ... -> version_ok False, estado INDECIDIBLE`).
- «Manda la más estricta» entre original y SN (`res["mejora"] = all`, `res["empeora"] = any`, `peor`): sin caso que
  dé veredictos distintos con las dos reglas.
- Ruido de V2 desde V1 (`--ruido-de`): `v2_nulo` lo pasa, pero ningún caso depende de su valor.
- Orden de `global_ventana` (H2), EMPEORA en `combinar` (H6), P4 con protegida movida (A61): sin caso.
- Bootstrap por bloques y signo por bloque DENTRO de `contar` (ver mutaciones).
- **Cambio propuesto.** Una prueba de unidad de `contar` con una tabla sintética (pares duplicados por noche) cubre
  de una vez bloques, signo, mínimos, estratos y orden; y casos de punta a punta para cobertura corta y versión.

### H10 (gravedad 4). P2 por noche sin veredicto ni aviso

- **Dónde.** `evaluar_d25.py:322-325`.
- **Qué pasa.** §5: P2 «se informa también por noche-volcán (A94), y si discrepan se dice en la primera línea del
  veredicto». El código sólo cuenta noches con error en K y en D; no da GANA/EMPATE/PIERDE por noche ni marca la
  discrepancia en el estado.
- **Confianza.** Alta. **Cambio.** Veredicto por noche con la misma regla y sufijo en el estado si difiere.

### H11 (gravedad 4). Lo que §5 manda informar y no se informa

- Bandas de #869 (< 30°, 30 a 50°, ≥ 50°): `PREREGISTRO.md:150` «que se informan además». No aparecen en el evaluador.
- Chillán «cada sensor y tramo»: `evaluar_d25.py:605-607` imprime sólo por sensor.
- P5: faltan las publicaciones «destapadas» por los filtros del tablero y `diag_bg_vecinos_n_sin_vecinos`
  (`PREREGISTRO.md:159`); lo de `:561-564` es una aproximación de las apagadas.
- Pares que salen de M: sólo el conteo (`:336`), sin la lista con su volcán.
- **Confianza.** Alta. Ninguno decide.

### H12 (gravedad 4). Control positivo de la calibración: no es el del texto, y su resultado no tiene lugar fijo

- **Dónde.** `evaluar_d25.py:172-174`, `:368`.
- **Qué pasa.** (a) El texto pide «signo fijo hacia MIROVA»; el código además topa el paso en min(e, a) para no
  pasarse, lo que regala poder: un par con K = 1, M = 1,5 y D = 3 da `d literal +0.125 | d con tope -0.176`
  (`v1_salida.txt`, V1i). (b) Es una sola evaluación determinista, no «más del 80 % de las repeticiones». (c) §5 lo
  trata como informativo y §7.5 lo pone entre los controles cuyo fallo deja INDECIDIBLE; el código lo informa. (d) Con
  e = 0 en todo el estrato devuelve `poder False`, que se imprime como «sin poder» cuando lo que pasa es que D = K.
- **Cambio propuesto.** Sin tope (literal), y que la adenda diga si decide o informa.

### H13 (gravedad 4). La prueba de unidad de calibración pasa por un pelo

- `probar_salida.txt`: `calibracion OK falsos MEJORA por pasada 0.235, por bloques 0.045`. El tope es 0,05: una
  repetición de margen en 200, con una semilla fija (`rng = default_rng(7)`). Cualquier cambio inocuo del orden de
  sorteo puede dejarla roja por azar. Además 0,045 en una cola con nominal 0,025 dice que el bootstrap por bloques con
  15 bloques es anticonservador, que es justo lo que la calibración tendría que señalar.
- **Cambio propuesto.** Asertar contra el tope por cola de H5 con más bloques o más repeticiones, y asertar el
  contraste (por pasada >> por bloques) más que el valor absoluto.

### H14 (gravedad 5). La exclusión de Suomi NPP no mira la fecha del hito

- `evaluar_fk.py:333-335` (`ocr_snpp`), reusada en `evaluar_d25.py:288` y `:333`, excluye en toda V1 (hasta el
  2026-10-18), mientras §4 dice que no deciden sólo las de antes del 2026-10-09. F/K terminaba el 2026-10-08, así que
  ahí no importaba. Hoy no hay casos después del hito (`v3_salida.txt`: `('VIIRS375', 'antes_o_igual_2026-10-09') 9`,
  `('VIIRS750', 'antes_o_igual_2026-10-09') 2`, ninguna después), así que es latente; `sustrato_k.py` tiene la misma
  omisión, y por eso los 31/29 del §4 son coherentes con el evaluador.

### H15 (gravedad 5). `peor()` deja como estado de la ventana «MEJORA» frente a «SIN EFECTO»

- `evaluar_d25.py:409-410`: los estados fuera de `ORDEN` valen 3, así que `peor(['MEJORA', 'SIN EFECTO']) = MEJORA`
  (`v1_salida.txt`, V1f). El estado impreso puede decir MEJORA con `res["mejora"] = False`. `combinar` usa los flags,
  así que el veredicto combinado sale bien; el texto de la ventana engaña.

### H16 (gravedad 5). P1b se pierde en `combinar` si el final no es CUMPLE

- `evaluar_d25.py:627-628`: `combinar(v1_p1b, v2_sin) -> SIN EFECTO (decide Nicolas)` sin mencionar P1b
  (`v1_salida.txt`). Ya decide Nicolás, pero sin la lista a la vista.

---

## Mutaciones (pregunta 5)

Salida del autor (`mutaciones_salida.txt`, terminada durante esta verificación), con la línea base en 20 de 20, de
modo que «ATRAPADA» quiere decir que la mutación hizo fallar una aserción:

```
corte_50               NO ATRAPADA (20 de 20 OK)          esperado: corte
sin_bloqueo            NO ATRAPADA (20 de 20 OK)          esperado: bloq_mejora
calib_por_par          NO ATRAPADA (20 de 20 OK)          esperado: (ninguno: la unidad prueba la función, no su uso)
boot_por_pasada        ATRAPADA por ['mejora750']         esperado: (ninguno esperado)
mejora_lo              ATRAPADA por ['mejora750', 'empeora750', 'bloq_mejora', 'calibracion'] esperado: nulo
ATRAPADAS por aserción: 15 de 18 | caídas (no cuentan): 0 | no atrapadas: 3
```

- **`corte_50`**: hueco real (H3), y mi corrida dirigida dice por qué.
- **`sin_bloqueo`**: mutante EQUIVALENTE, no hueco de las pruebas, pero revela un defecto (H17): el `modo` que devuelve
  `estrato()` se descarta (`evaluar_d25.py:340` lo asigna y `:344` lo pisa con el de `ESTRATOS`). Hay dos tablas de
  modo y la que el docstring presenta como la regla no se usa.
- **`calib_por_par`**: hueco, como el autor esperaba. ¿Es serio? Medio: con el signo por par la calibración pierde
  la capacidad de ver la dependencia dentro de la noche (línea F de `v2_salida.txt`: 0,025 con bootstrap por pasada),
  así que la mutación vuelve verde un estrato mal calibrado. En los datos reales la mayoría de los bloques tiene uno o
  dos pares (`v4_salida.txt`: 103 pares en 82 bloques, 64 en 64), salvo VIIRS 750 > 40° de V1 (23 en 14), justamente
  el de Chillán. Se cierra con la prueba de `contar` de H9.
- **`boot_por_pasada`**: la atrapa `mejora750`, pero por la razón indirecta: el bootstrap por pasada contra un nulo con
  signo por bloque sale mal calibrado y el estrato queda INDECIDIBLE. No hay caso que pruebe que el intervalo de la
  DECISIÓN es por bloques (que es lo que H9 del verificador anterior pidió). Frágil: depende del nivel de la
  calibración en ese caso, que está a una o dos repeticiones del tope (H13).
- **`mejora_lo`**: la atrapan otros casos, no `nulo` (en el nulo d = 0 exacto, así que `lo < 0` no se cumple nunca). Bien
  atrapada, mal atribuida.

**Mutaciones importantes que faltan** (cada una correspondería a una regla sin caso, H9): orden de `global_ventana`
(PIERDE antes que INDECIDIBLE de M, H2); `res["mejora"] = any` y `res["empeora"] = all` (manda la más estricta); quitar
la regla SN; `ruido = 0` en V1 o ignorar `--ruido-de` en V2; quitar `cortos` de la cobertura; quitar `version_ok`;
quitar `referencia_ok`; quitar el chequeo de huella en K y K' (`elif huella`); quitar `triggered_test1`; percentil
5/95 en lugar de 2,5/97,5; `N_MIN_NOCHES = 1`; dejar entrar a M los pares que cambian de publicación (`salen`) o los
de etiqueta distinta de `pos`; `KERNEL = set()`; la rama A61 de P4. Por lectura de la lista de casos, ninguna de esas
mutaciones haría fallar una aserción hoy salvo, quizás, la de huella en K (ningún caso le pone huella a K: SOSPECHA
de que tampoco).

### H17 (gravedad 4). Dos tablas de modo para los estratos; la de `estrato()` es código muerto

- `evaluar_d25.py:91-102` devuelve `(nombre, modo)`; `:340` guarda el modo y `:344` lo reemplaza por el de `ESTRATOS`
  (`:105-107`). Mutar la regla de `estrato()` (la que lleva el comentario del sello §8 a) no cambia nada:
  `sin_bloqueo NO ATRAPADA (20 de 20 OK)`. Si alguien corrige el modo en un lugar y no en el otro, nadie se entera.
- **Cambio propuesto.** Una sola fuente (derivar `ESTRATOS` o usar el modo de `estrato()`), con una aserción de
  coherencia.

---

## VERIFICADO LIMPIO

- **Mediana ponderada exacta**: `V1a mediana ponderada: 0 de 300 casos distintos de np.median(np.repeat)` (con empates
  forzados, incluido total par).
- **Bootstrap por bloques**: pares del mismo bloque con igual conteo y suma de conteos por réplica igual al número de
  bloques (`V1b ... True | ... [3] (n bloques 3)`); 10.000 réplicas, semilla 157 (`evaluar_d25.py:68`).
- **Percentil**: 2,5 y 97,5 de las medianas de las réplicas, MEJORA con hi < 0 y EMPEORA con lo > 0
  (`V1c regla_m: MEJORA [-0.3000, -0.0500] | np.percentile ... [-0.3000, -0.0500]`).
- **d por par** = |log10(D/M)| − |log10(K/M)| (`:150-151`), igual al §5.
- **Estratos** (`:91-107`): VIIRS 750 decide en los dos tramos; VIIRS 375 sin kernel decide con ≤ 40° y bloquea sobre
  40°; con kernel informa. La lista de kernel se lee de `volcanoes.yaml` y coincide con §1:
  `['PuyehueCordonCaulle', 'Villarrica', 'Chaiten', 'PlanchonPeteroa', 'Lastarria']`. El bloqueo actúa y es necesario:
  sin él el caso pasa a MEJORA (`H bloq_mut: M sin_kernel z>40 MEJORA, estado MEJORA`). Sin pasadas sin cenit en V1
  (`v3_salida.txt`: `{} de 4576`).
- **Mínimos** 5 pares y 3 noches (`:348`).
- **P1 sin las protegidas sólo OCR de Suomi NPP** en V1: la exclusión decide (`G snpp: original P1 V375 CUMPLE | sin la exclusión P1 V375 VETADO`);
  la ventana de prueba trae 7 (`E snpp: ... 66, de ellas sólo OCR de Suomi NPP 7`), así que el caso `snpp` no es vacío.
- **P1 ruidosa con el gemelo, P1b, P2 por pasada con ruido de pasadas discordantes y fracción de V1 en V2**: iguales a
  F/K (`evaluar_fk.py:338-369`, `:612-623`), con las claves de `ruido_frac` coherentes entre V1 y V2 (`:315`, `:317`, `:537`).
- **SN y original**: se calculan las dos, con la misma lógica de reetiquetado que F/K (`:530-533`), y `estado` es el
  peor, `mejora` exige las dos y `empeora` cualquiera (`:539-541`).
- **ALERTA_SIN_GEOMETRIA_OCR** no es alerta (`scripts/banco_paridad.py:196-203`), así que no entra a M ni a P1; se
  lista aparte (`:575-578`).
- **Cableado declarado = perfiles**: resolviendo `pipeline.profile` con cada `VRP_PROFILE`, los tres brazos dan
  exactamente `DECLARADO` (K y K' con D25 apagado, D con los dos flags; `VRP_BG_NEIGHBOR_MAX_HALF_PX 3`,
  `SENSOR_MODIS false` en los tres), y el workflow escribe esas claves en `FLAGS_BRAZO`
  (`.github/workflows/reproc-s146-ab-sin-test1.yml:146`). Una clave ausente da `None != valor` y rompe (no hay verde
  silencioso).
- **Huella sin falso rojo**: ver H8.
- **MODIS**: se cuenta en los brazos (`:208-210`) y no entra a cobertura (`:230`, `:235`); caso `modis` en verde.
- **Cobertura y versión pueden fallar** (C y D de `v2_salida.txt`).
- **Sin falso rojo por pasadas diurnas**: producción y el histórico con K son sólo nocturnos (horas UTC de VIIRS entre
  4 y 7 en Lascar y Chillán, abril a octubre), como los brazos (`scripts/run_pipeline.py:446`, `nighttime_only = not args.no_night_filter`, y el workflow no pasa
  `--no-night-filter`).
- **Referencia de V2**: `_congelado_v2/MANIFIESTO.json` trae `capas` (`consolidado_filas_perdidas.csv`,
  `respaldo_20260408.csv`), así que `referencia_ok` no cae por falta de capas.
- **Línea base de las pruebas**: `RESUMEN: 20 de 20 casos OK`.
- **No se modificó `evaluar_fk.py`**: `git status` no lo lista.
