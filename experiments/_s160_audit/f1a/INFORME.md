# F1a. Metrología del instrumento con que se adoptó K y de los bancos compartidos

> **Estado: TERMINADO.**
> Hora del servidor al empezar: `Thu, 22 Oct 2026 03:11:55 GMT` (`experiments/_s160_audit/insumos/hora_servidor.txt`);
> `date -u` de la máquina al arrancar: 2026-10-22 03:18 UTC.
> Commit auditado: `origin/main` = `d516b9d8c0fad5b0ca458b9fb57cdf5e6f75f956`. Worktree de trabajo
> `C:\vrp-trabajo\s159-pruebas` en `60762a939` (sello de F1a): `git diff --stat d516b9d8c` sale vacío para
> `experiments/_s151_prereg_fk_11/`, `experiments/_s153_fk_v2/`, `scripts/banco_paridad.py`, `scripts/clase_mirova.py`,
> `frontend/index.html`, `scripts/referencia_mirova_unificada.py`, `scripts/auto_audit_weekly.py`,
> `scripts/calidad_referencia_mirova.py`, `scripts/libro_de_cuentas.py`, `experiments/_s146_ab_sin_test1/evaluar.py`,
> `experiments/_s149_prereg_invierno/armar_tabla.py`, `experiments/_s151_ab_diurno/unir_intentos.py`, `volcanoes.yaml`
> y `pipeline/` (medido en esta sesión). Los evaluadores se corrieron desde el worktree con `--produccion` apuntando a la
> copia de datos de `main` en `D:\vrp-trabajo\temporales\s160_audit\main\data\mirova_equivalent`.
> Modelo y esfuerzo: Fable 5.1, `high` (el del plan §F1).
> CARPETA: `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f1a\` (scripts y salidas en `salidas\`);
> datos extraídos en `D:\vrp-trabajo\temporales\s160_audit\f1a\`.
>
> **Semilla sellada antes de correr el barajado de R7 (§11.2b): 160.** Barajados: 1.000. Intervalo: Wilson al 95 %.
>
> Referencias usadas, con sha256 (crudo, tal como está en disco; LF donde se dice LF):
> - tabla sola de `main`: `latest_consolidado.csv` = `bc1522c24c924cb5…`;
>   OCR de `main`: `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` = `94679246acbd0db5…`;
>   consolidado del snapshot de `main` = `2e2c268e8811cdc1…`.
> - congelado V1 del pre-registro (`experiments/_s151_prereg_fk_11/_congelado_v1/`, Mirova-v1@`c5944c6`, LF):
>   consolidado `891dd298b6ef461e…`, OCR `ba9ca692c4a49a0d…` (iguales a su `MANIFIESTO.json`).
> - congelado V2 (`_congelado_v2/`, LF): consolidado `a4a411a6b88d8fc3…`, OCR `bf56d5abe6ec463a…`.
> El instrumento de K decide contra el congelado del pre-registro, no contra la copia de `main`; las dos versiones de la
> referencia que pide el plan (§11.2.1) se obtienen con el mismo congelado, sacando el OCR (`--solo-tabla si`).

## Qué NO miré

- No abrí `experiments/_s157_prereg_d25/` más allá de `evaluar_d25.py` (sólo para localizar la métrica M del control
  positivo de R6) ni PR #890 ni ningún resultado de D25.
- No audité el código del scraper Mirova-v1 (otra sesión); sólo cómo lo consume VRP.
- No reprocesé L1B ni despaché workflows. Las llamadas a la API de GitHub fueron 9 (tope 10): 2 para el run V1
  (intentos y artefactos), 2 para bajar `s146ab-todo` de V1, 2 para V2a, 2 para bajar el de V2a, 1 para el issue #864.
- No miré los instrumentos de prioridad B y C (F1b).

## En una pantalla

1. **El instrumento de K podía decir CUMPLE sin efecto real.** El control C0 copiado como candidato, con el único
   cambio de poner `triggered_test1 = False` (ninguna ganancia, ningún desplazamiento), recibe **CUMPLE en V1 y en
   V2, lecturas A y B**. Mecanismo: la tolerancia de P2 es 0 (el gemelo dio 0 pasadas discordantes y V2 hereda ese
   0), así que GANA con una sola pasada de margen, y el predicado del tablero (`isSummitDetection`,
   `frontend/index.html:1612`) deja de publicar 21 records de C0 cuando ese flag no está. Hallazgo 161, gravedad 5
   por la regla del plan (sostiene producción); **K real supera ese margen 10 a 20 veces** (P2 10 contra 114, 37 contra
   734, 26 contra 331 en V1), así que la adopción no se explica por esto.
2. **La referencia cambia el veredicto.** Con la tabla sola, K CUMPLE en V1 y V2; con tabla y OCR en V2 queda
   PENDIENTE DE REPETICIÓN por Lastarria VIIRS 375 2026-04-18 04:42 (1,29 MW, sólo OCR), repetición que no se corrió.
   La regla lo preveía (§4.2: «se miran, no deciden»), pero el plan §11.2.1 lo manda como hallazgo (162, gravedad 3).
3. **Los datos de la adopción no están en el repo**: la rama de V1 es despareja; la unión evaluada se rehace con la
   rama más el artefacto (vence 2027-01-14) y reproduce `v1.json` y `v2.json` exactos (163, gravedad 3).
4. **Lo que sí resiste**: el barajado de etiquetas (R7: 0 de 1.000 cumplen, Wilson [0; 0,0038], OK, aunque todo el rechazo lo pone el veto P1 y no la suma P2, hallazgo 164); el veto rechaza el desplazamiento sin
   información (NO CUMPLE); la reimplementación independiente de `etiquetar` y de la alerta protegida da **0
   diferencias en protegidas A y B** sobre 16.843 pasadas y todas las diferencias de etiqueta (86 en V1, 212 en V2)
   se explican por filas diurnas de MIROVA que `banco_paridad` aparta antes de armar la noche; el punto 11.1.2 del
   plan (OCR protegida con tabla en FALSO_POSITIVO) da 0 casos; K gana la suma en los 66 estratos sensor por volcán.
5. Los dos controles positivos del plan salieron con instrumento propio: el placebo de ganancia 1,2 da MEJORA en la
   métrica M de D25 (y 1,1 también) y el gemelo de D25 es identidad bit a bit (0 de 4.610), mientras el gemelo de F/K
   V1 en otro job difiere en 2.216 records sin cambiar ninguna publicación.

## Bitácora de lo medido (orden cronológico)

1. **Los datos con que se adoptó K no están en el repo.** La rama `origin/s146-ab/38639658446` (V1) trae el intento 1
   con `cobertura.txt` = «COBERTURA DESPAREJA» (F faltan 39, K 22, gemelo 493 y sin Villarrica). La unión de intentos
   que evaluó S153 (`union_2766`, 44 archivos) vivía en `C:\Users\nmend\AppData\Local\Temp\claude\v1_38639658446\` y
   ya no existe. El run tiene 3 intentos (`run_attempt` 3, API); el artefacto `s146ab-todo` (intento 3, vence
   2027-01-14) también es despareja sola (K faltan 18, gemelo 15). La unión del intento 1 (rama) con el 3 (artefacto)
   con `experiments/_s153_fk_v2/unir_ventana.py` da cobertura pareja y **reproduce `v1.json` en 497 de 497 claves**
   salvo `sha256_index_html`. Igual para V2a (rama = intento 1, artefacto = intento 2) y V2b (rama + repetición
   `39068999603`): `v2.json` reproducido en 276 de 276 claves salvo el sha del tablero.

2. **Reproducción con el evaluador original** (`experiments/_s151_prereg_fk_11/evaluar_fk.py`, idéntico a `main`):
   V1 `salidas/v1_rep.json` = `experiments/_s153_fk_v2/v1.json` en 496 de 497 claves (la distinta es
   `sha256_index_html`: el `index.html` de hoy, `f711c61d…`, no es el de S153, `4014103e…`, y ninguna decisión cambia).
   V2 `salidas/v2_rep.json` = `v2.json` en 275 de 276. Combinado: K lectura A CUMPLE, lectura B NO CUMPLE (veto), como
   en `experiments/_s153_fk_v2/combinado.log`.
3. **Veredicto de K con cada versión de la referencia** (plan §11.2.1), mismas uniones, mismo evaluador:

   | referencia | V1 | V2 | combinado K lectura A |
   |---|---|---|---|
   | la del pre-registro (V1 tabla y OCR; V2 tabla sola) | CUMPLE | CUMPLE con auditoría espacial pendiente (P4) | **CUMPLE** |
   | tabla sola en las dos | CUMPLE (protegidas A que C0 publica: V375 10 en vez de 21; V750 9 en vez de 12) | igual que arriba | **CUMPLE** |
   | tabla y OCR en las dos | CUMPLE | **PENDIENTE DE REPETICIÓN** (Lastarria VIIRS375 2026-04-18 04:42, 1,29 MW, NOAA-20, sólo OCR, C0 publica y K no; más Lastarria 2026-05-02 05:06, 2,36 MW, sólo OCR de Suomi NPP, apartada) | **PENDIENTE DE REPETICIÓN** |

   Salidas: `salidas/v1_solo_tabla.log`, `salidas/v2_con_ocr.log`, `salidas/v2_rep.log`. Con SN, SE y las variantes
   de 0,04 (sección 10 del evaluador) el veredicto no cambia en ninguna de las tres filas.
4. **Placebos (R6)**, `medir_k.py` y `medir_k2.py`, salidas en `salidas/medir_k/` y `salidas/medir_k*_resumen.txt`.
   Primera tanda (placebo sólo en K): V1 INDECIDIBLE en los tres por el control de determinismo K contra F (el
   placebo no es F), no por el criterio. Segunda tanda (placebo en F y K, como los entiende el pre-registro en VIIRS):

   | placebo (K := C0 modificado) | V1 K A | V1 P2 (K contra C0) | V2 K A | V2 P2 |
   |---|---|---|---|---|
   | sólo `triggered_test1=False` | **CUMPLE** (A y B) | MODIS 110 contra 114 GANA; V375 734 = 734 EMPATE; V750 318 contra 331 GANA | **CUMPLE** (A y B) | MODIS 266 contra 268 GANA; V375 863 = 863 EMPATE; V750 407 contra 420 GANA |
   | ×1,10 con el flag en False | **CUMPLE** | idéntico a la fila anterior | **CUMPLE** | idéntico |
   | ×1,20 con el flag en False | **CUMPLE** | idéntico | **CUMPLE** | idéntico |
   | ×1,10 y ×1,20 con el flag como en C0 | INDECIDIBLE (cableado: «declara sin Test 1 y hay records con triggered_test1») | MODIS 114 = 114, V375 734 = 734: EMPATE, sería NO CUMPLE (no gana) | INDECIDIBLE (cableado) | 268 = 268, 863 = 863, 420 = 420: EMPATE |
   | desplazado una pasada (sin información), flag en False | NO CUMPLE (veto): 3 protegidas MODIS netas, V375 y V750 ruidosas | V375 757 contra 734 PIERDE | PENDIENTE DE REPETICIÓN (6, 2 y 26 pérdidas pendientes) | PIERDE en los tres (270, 893, 427) |

   Lectura: una ganancia constante no cambia ninguna publicación (P2 EMPATE); todo el «efecto» del placebo es el
   flag. `salidas/mecanismo_t1off.txt`: 21 pasadas (4 MODIS, 17 VIIRS 750), las 21 con `vrp_mw` 0, `discarded_reason`
   presente, `triggered_test1` True y cúmulo con energía; 17 son negativos limpios. Es el camino de
   `frontend/index.html:1612`: «`if ((r.vrp_mw ?? 0) === 0 && r.discarded_reason && !r.triggered_test1) return false;`»
   (TEXTO). Un brazo sin Test 1 nunca puede publicar esos records; el control sí, y la diferencia cuenta como
   «negativos que el candidato deja de publicar» con tolerancia 0.
5. **Borrado de un día (R2)**: quitar el 2026-09-15 sólo de K da «K le faltan 109 pasadas de C0», COBERTURA DESPAREJA,
   INDECIDIBLE (`salidas/medir_k/v1_borra_K.log`). Quitarlo de los cuatro brazos deja CUMPLE con las sumas 109/722/324
   en C0 (informativo: el criterio no depende de un día).
6. **Barajado (R7, §11.2b)**, `barajar_r7.py`, semilla 160, 1.000 barajados del paquete de referencia (etiqueta,
   `vrp_ref`, protegida A y B, `alerta_solo_ocr`, `rutina_pasada`, `noche_con_alerta_sensor`) dentro de cada estrato
   volcán por sensor, publicaciones fijas. Controles: (a) sin barajar, la reimplementación de §5 y §6 da los mismos
   veredictos que el evaluador en V1 y V2 (IGUAL); (b) un barajado adverso construido a mano (12 protegidas de V1 y
   57 de V2 movidas a pasadas que C0 publica y K calla) da NO CUMPLE (veto) en V1 y PENDIENTE DE REPETICIÓN en V2.
   Resultado: **0 de 1.000 barajados cumplen** en V1, en V2 y en el combinado; Wilson 95 % [0,0000; 0,0038] → **OK**.
   Distribución: V1 1.000 NO CUMPLE (veto); V2 1.000 PENDIENTE DE REPETICIÓN. El veto P1 es el que da el poder: con
   etiquetas sin información, alguna protegida barajada cae en una pasada que C0 publica (88 % en VIIRS 375) y K no.
   P3 y P4 no se recalcularon (sólo agregan sufijo; declarado en el script).
7. **Controles positivos del plan**, `controles_d25.py` (`salidas/controles_d25.txt`): (a) métrica M propia (mediana
   de d con bootstrap por bloques noche-volcán, 2.000) sobre los 260 pares VIIRS 375 y 32 VIIRS 750 de C0 contra
   MIROVA en V1: g = 1,0 NEUTRO [0, 0]; g = 1,1 MEJORA; g = 1,2 MEJORA (V375 mediana d −0,079, IC [−0,079; −0,067]);
   g = 0,8 EMPEORA. Reproduce la fila 9 de `docs/AUDIT_S158_R2.md` §1. (b) K contra K' de D25 V1 (run 39530508296):
   4.610 pares, 0 records distintos, 0 sin parear; control positivo del instrumento: C0 contra su gemelo de F/K V1
   (jobs distintos) 448 + 880 + 888 records distintos y 0 campos que lea el predicado; control de mutación 37 → 37.
8. **H1b, `etiquetar` reimplementado** (`etiquetar_propio.py`, sin importar ningún módulo del repo), contra la tabla
   del evaluador en cuatro referencias: V1 tabla y OCR (4.820 pasadas), V1 tabla sola, V2 tabla sola (12.023), V2
   tabla y OCR. Protegidas A y B: **0 diferencias** en las cuatro. `vrp_ref`: 0. Etiquetas: 86, 84, 212 y 215
   distintas, todas «mío sin_info, banco neg_limpio», y `salidas/etiquetar_propio_explicacion.txt` las explica
   enteras: son pasadas nocturnas cuya fecha UTC tiene una fila **diurna** de MIROVA (FALSO_POSITIVO o alerta de la
   tarde, p. ej. Láscar 2026-09-18 17:48 FALSO_POSITIVO 2,13 MW) que `banco_paridad.indexar_referencia` (l. 239)
   descarta con `es_pasada_diurna_descartada` antes de armar `noche_sensor`. Control positivo del comparador: con
   tolerancia 0 s cambian 2.052 etiquetas y 20 protegidas A.
9. **Punto 11.1.2 (`alerta_protegida` sin cruzar canales)**, `prot_cruce_canales.py`: llamadores trazados
   (`evaluar_fk.py:194` y `auto_audit_weekly.py:776` la aplican fila por fila). Pasadas protegidas A cuya protección
   descansa sólo en el OCR: 11 en V1 (VIIRS 375) y 3 (VIIRS 750); 39 y 32 en V2 con OCR; **en ninguna** la tabla trae
   FALSO_POSITIVO ni RUTINA para esa pasada: todas carecen de fila CONS. Control positivo: la pasada sintética CONS
   FALSO_POSITIVO 3 MW + OCR ALERTA 2 MW sí cuenta como protegida (el mecanismo existe, el sustrato no).
10. **R13**, `salidas/r13_p2_por_volcan.txt`: K gana la suma de P2 (lectura A) en los 33 estratos sensor por volcán
    de V1 y en los 33 de V2; ningún signo invertido.
11. **Disco.** Aviso del orquestador a las 04:4x UTC: la carpeta de D: llegó a 3,0 GB (tope 2 GB). Borré dentro de
    `D:\vrp-trabajo\temporales\s160_audit\f1a\` los brazos de placebo (`placebos\` 682 MB y `placebos2\` 1,7 GB; se
    rehacen con `medir_k.py` y `medir_k2.py`) y las extracciones de las cuatro ramas (`rama_*`, 185 MB; están en git).
    Quedan 419 MB: artefactos de V1 y V2a (no están en git), las tres uniones, D25 K y K', y los `tmp_*` del evaluador.

## Hallazgos

### 161. El instrumento de K da CUMPLE a un placebo: el control con sólo `triggered_test1` en False
- ARCHIVO:LÍNEA: `experiments/_s151_prereg_fk_11/evaluar_fk.py:613-641` (ruido de P2 = pasadas discordantes del
  gemelo, 0 en V1; V2 hereda `ruido_frac` 0,0 por `--ruido-de`), `:502-503` (huella que obliga a un brazo «sin Test 1»
  a no traer `triggered_test1`), `frontend/index.html:1612` (`isSummitDetection`).
- QUÉ PASA. Físicamente: en una noche sin nada, C0 deja records con un cúmulo con energía pero `vrp_mw` 0 y una
  razón de descarte, que el tablero publica sólo porque el Test 1 integrado disparó. Un candidato que no tenga ese
  flag deja de publicarlos sin haber medido nada distinto, y como la tolerancia de P2 es 0, esas 4 (MODIS) y 13
  (VIIRS 750) pasadas bastan para GANA; con P1 intacto (no tocan protegidas) el veredicto es CUMPLE en las dos
  ventanas y en las dos lecturas. Una ganancia constante ×1,1 o ×1,2 no mueve ninguna publicación (EMPATE); todo el
  efecto es el flag. El instrumento no distingue «detecta mejor» de «no lleva un flag que el tablero lee».
- CÓMO SE VE EN EL DASHBOARD: invisible hoy. Para K real los márgenes son 10 a 20 veces mayores que el efecto del
  placebo (P2 10 contra 114, 37 contra 734, 26 contra 331 en V1; 25 contra 268, 63 contra 863, 46 contra 420 en V2),
  así que la adopción no descansa en esto. Lo que tuerce es el siguiente A/B que use este instrumento con un candidato
  de efecto chico: con tolerancia 0, una pasada decide.
- CÓMO REPRODUCIRLO: `python experiments\_s160_audit\f1a\medir_k2.py D:\vrp-trabajo\temporales\s160_audit\f1a\v1_union
  D:\...\v2a_union D:\...\v2b_union experiments\_s160_audit\f1a\salidas\medir_k
  D:\vrp-trabajo\temporales\s160_audit\main\data\mirova_equivalent experiments\_s160_audit\f1a\salidas\v1_rep.json`
  (caso `v1_solo_t1off`; Villarrica VIIRS750 2026-08-29 06:18 UTC es la primera de las 21).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 5 por la regla del plan (el instrumento sostiene una decisión en producción); con la salvedad de los
  márgenes de K escrita arriba, quien filtre puede bajarla a 4.

### 162. El veredicto de K depende de qué versión de la referencia se use
- ARCHIVO:LÍNEA: `experiments/_s151_prereg_fk_11/evaluar_fk.py:59-62` (`solo_tabla` fijo por ventana);
  `REGLA_ADOPCION.md` §4.2 («se listan las protegidas sólo OCR que K pierde. No deciden, pero se miran», TEXTO).
- QUÉ PASA. Con la tabla sola, CUMPLE en V1 y V2. Con tabla y OCR en V2, K deja de publicar la protegida de Lastarria
  VIIRS 375 del 2026-04-18 04:42 (1,29 MW, NOAA-20, sólo en el OCR; C0 la publica) y el veredicto de V2 y del combinado
  es PENDIENTE DE REPETICIÓN. La regla eligió la tabla sola para V2 por A119 (OCR mal calibrado hasta el 2026-06-11) y
  mandó mirar estas pérdidas: `experiments/_s153_fk_v2/lector2/INFORME.md` las lee como lejanas con su distancia propia.
  Lo que no se hizo es la repetición que el propio instrumento pide, ni se dejó escrito el veredicto combinado con OCR.
- CÓMO SE VE EN EL DASHBOARD: una noche de Lastarria en abril de 2026 que C0 mostraba como anomalía y K no.
- CÓMO REPRODUCIRLO: el `--solo-tabla no` de la bitácora 3 y `--combinar salidas/v1_rep.json salidas/v2_con_ocr.json`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3.

### 163. Los datos con que se adoptó K no están en el repo
- ARCHIVO:LÍNEA: `origin/s146-ab/38639658446:experiments/_s146_ab_sin_test1/salidas/38639658446/cobertura.txt`
  (TEXTO: «COBERTURA DESPAREJA»; gemelo sin Villarrica, F faltan 39, K 22); `experiments/_s153_fk_v2/README.md:4-6`
  (las uniones vivían en `C:\Users\nmend\AppData\Local\Temp\claude\`, hoy inexistente).
- QUÉ PASA. La rama guarda el intento 1; el intento 3 está en el artefacto `s146ab-todo` del run (vence el
  2027-01-14); el intento 2 no está en ninguna rama ni artefacto. Uniendo 1 y 3 con `unir_ventana.py` la cobertura
  queda pareja y `v1.json` se reproduce; igual V2a (rama + artefacto, vence) y V2b (rama + repetición en rama). Dentro
  de 84 días la adopción de K no se podrá re-evaluar desde el repo.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: bitácora 1.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (es de forma hasta el 2027-01-14; después, el A/B que sostiene producción deja de ser reproducible).

### 164. R7 pasa, pero sólo por el veto: P2 no tiene poder propio contra etiquetas sin información
- ARCHIVO:LÍNEA: `experiments/_s160_audit/f1a/barajar_r7.py`; `evaluar_fk.py:634-639` (GANA si la suma del candidato
  es menor que la del control menos el ruido).
- QUÉ PASA. 0 de 1.000 barajados cumplen (fila R7 OK). Pero en los 1.000 el rechazo viene de P1 (V1 NO CUMPLE (veto)
  1.000 veces; V2 PENDIENTE 1.000 veces): P2 sigue dando GANA a K porque K publica menos que C0 en cualquier
  partición de las pasadas. Un candidato que calle más que el control gana P2 con etiquetas al azar; el único freno es
  que no calle en las protegidas. Con 21 protegidas en VIIRS 375 y 3 en MODIS (V1), ese freno es el que el pre-registro
  §3 ya declaró débil fuera de Láscar y Chillán.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: bitácora 6.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### 165. El nombre CUMPLE del combinado promete más de lo que la regla prueba
- ARCHIVO:LÍNEA: `evaluar_fk.py:780-806` (`combinar` elige el peor por prefijo y pierde el sufijo «con auditoría
  espacial pendiente (P4)»); `:770-777` (un P3 FALLA sólo agrega sufijo); `resultado_v1/VERIFICADOR.md` §4 (P3 anulado
  por construcción en VIIRS 375); `CLAUDE.md` marca S153 («CUMPLE en V1 y V2»).
- QUÉ PASA. El CUMPLE combinado se propagó a `CLAUDE.md` sin el sufijo de V2 ni la observación de que la magnitud de
  VIIRS 375 empeora contra MIROVA (razón mediana 0,748 → 0,620) y P3 no lo puede ver. La regla §3 ya pide leer la
  lista por ventana; la auditoría A61 se hizo (`_s153_fk_v2/a61/`). Es de nombre, no de medición.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `--combinar salidas/v1_rep.json salidas/v2_rep.json`.
- CONFIANZA: SOSPECHA (es un juicio sobre el nombre).
- GRAVEDAD: 2.

### 166. Las bandas del auto-audit siguen calibradas sobre C0 y juzgan a K
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:120` (`RECALL_MIN`, sin cambio desde `c110a29ac`, 2026-07-02) y `:132`;
  `REGLA_ADOPCION.md` §4.8 («Se decide en el PR, con los números de V1 y V2, si se recalibran o se acepta que
  salten», TEXTO); `docs/superpowers/plans/2026-10-19-auto-audit-por-detector.md:28` («las bandas (`RECALL_MIN`) se
  calibraron sobre cráter en S119 y no hay bandas para publicación», TEXTO).
- QUÉ PASA. El issue #864 (2026-10-19) saltó sobre K por recall VIIRS 750 73,3 % contra una banda de 79,5 % medida
  sobre C0, y listó como «alerta protegida sin publicar» las dos de Tupungatito que el propio pre-registro apartó por
  ser sólo OCR de Suomi NPP (con el aviso A119 al lado, pero contadas). La decisión que §4.8 pedía no aparece tomada.
- CÓMO SE VE EN EL DASHBOARD: invisible (issues semanales).
- CÓMO REPRODUCIRLO: `gh issue view 864`; `git log -S"RECALL_MIN = {" -- scripts/auto_audit_weekly.py`.
- CONFIANZA: CONFIRMADO por lectura; SIN DATO sobre si Nicolás lo decidió fuera del repo.
- GRAVEDAD: 2.

## SEGUIMIENTOS (fuera de mi eje)

- S-1. `scripts/calidad_referencia_mirova.py` imprime en V1 el hito 2026-04-14 (Distancia_aprox) como «tramo con
  defecto» aunque la propia línea dice que es una columna complementaria; y el aviso va sólo a stderr (`:66`), que
  `evaluar_fk.tabla` (`:126-128`) captura con `capture_output=True` y no reimprime. CONFIRMADO (lectura). Gravedad 1.
- S-2. `evaluar_fk.py:434` lanza `armar_tabla.py` por cada par de brazos (4 en V1): la referencia se carga e indexa
  4 veces y el aviso A119 sale 6 veces por corrida. Forma. Gravedad 1.
- S-3. El `sha256_index_html` que graba el evaluador (`:425`) es el del archivo con CRLF de la copia de trabajo (hoy
  `f711c61d…`; S153 `4014103e…`): mide la máquina además del código, al revés de `sha_lf`. Gravedad 1.
- S-4. `scripts/banco_paridad.py:300-333`: «sin ALERTA ni FP esa noche» excluye las filas diurnas de MIROVA de la misma
  fecha UTC porque `indexar_referencia` las descarta antes (`:239`). Es diseño defendible (A76) y no está dicho en el
  docstring de `etiquetar` ni en `meta.definiciones` de `main` (`:520-527`). 86 pasadas de V1 y 212 de V2 cambian de
  `neg_limpio` a `sin_info` si se cuentan. Gravedad 2 (F1b lo hereda en los 7 evaluadores).
- S-5. `scripts/libro_de_cuentas.py` no registra ningún número de la adopción de K (811 de 832, 0 protegidas
  perdidas, 2,5 y 3,7 %): quedan sin instrumento que los recalcule. Gravedad 2.
- S-6. En V1 el control de determinismo compara K con F en VIIRS (`evaluar_fk.py:511`); un candidato futuro que no
  venga en par con su gemelo de código cae en INDECIDIBLE por ese control aunque el criterio no lo toque (le pasó a mi
  primera tanda de placebos). Propiedad del instrumento que conviene dejar escrita. Gravedad 1.
- S-7. `prot_cruce_canales.py` (mío) cuenta protegidas A sin `decide_sensor`: en V2 da 96 y 94 donde el evaluador
  cuenta 59 y 56 (VIIRS desde abril). No cambia la conclusión del punto 11.1.2 (0 casos en ambos conteos).

## VERIFICADO LIMPIO

- El evaluador reproduce los veredictos de S153 sobre las uniones rehechas (vara: `experiments/_s153_fk_v2/v1.json`
  y `v2.json`; comando en bitácora 2).
- `etiquetar` y `alerta_protegida` contra una reimplementación independiente (vara: mi propio script, no el banco):
  0 diferencias en protegidas y `vrp_ref`; etiquetas explicadas (bitácora 8).
- Punto 11.1.2: 0 pasadas (bitácora 9).
- R13: ningún estrato con el signo invertido (bitácora 10).
- R7: 0 de 1.000 (bitácora 6), con los controles (a) y (b).
- Los dos controles positivos del plan (bitácora 7).
- R1: pre-registro antes del primer dato (`2c174b5b1` 2026-10-14 15:35Z contra run 38639658446 creado 2026-10-14
  21:21Z, API); la sección 10 que entró después (`5170f9539`, 2026-10-15) está rotulada «INFORMA, decide la original».
- R8: los tres flags tienen consumidor en los tres procesadores (`pipeline/process_modis.py:138, 159, 172`,
  `process_viirs.py:130, 153`, `process_viirs_mod.py`); el cableado se lee del log de cada job.
- R2: borrar un día de un brazo lo ve la cobertura (bitácora 5).

## SIN DATO

- La hora de la primera evaluación de V2 contra la hora del merge de #848 (R1): lo afirma el verificador S153
  (`experiments/_s153_fk_v2/verificador/VERIFICADOR.md` §2) y no lo pude verificar con las llamadas que me quedaban.
- El intento 2 de V1 y de V2a (no existe en el repo ni en artefactos).
- El predicado del tablero entero (no se reimplementó; sólo se midió el camino de `triggered_test1`).
- `data/audit_continuous/latest.json` (no está en la copia de `main` que se me dio): el estado del auto-audit se
  leyó del issue #864 y del código.
- La hora de la primera evaluación de V1 (`resultado_v1` entró al repo recién en #850, 2026-10-18).

## FUERA DE ALCANCE

- Los instrumentos de prioridad B y C (F1b); el código del scraper Mirova-v1; el veredicto de D25 (#890); la
  vigilancia de la sombra (`scripts/vigilancia_sombra.py`) más allá de trazar `alerta_protegida`.

> **Estado: TERMINADO** (hora de la máquina al cerrar en la última línea).

_Cierre: 2026-10-22 03:46 UTC (hora de la máquina)._
