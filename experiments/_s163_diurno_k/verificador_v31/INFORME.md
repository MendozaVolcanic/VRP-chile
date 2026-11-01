# Verificación limpia v3.1 (cuarta mirada, alcance acotado al diff v3 a v3.1) del pre-registro del A/B diurno de VIIRS sobre K

- Hora del servidor: inicio `Mon, 26 Oct 2026 14:32:53 GMT`, cierre `Mon, 26 Oct 2026 15:12:13 GMT` (`gh api -i repos/MendozaVolcanic/VRP-chile | grep -i ^date`).
- Commit medido: `9700e4e0b5e543563d5ea5a2167202696b33c198` (`git rev-parse HEAD`), rama `claude/s163-diurno-k-prereg-5c4f44`. v3 = `987a760120302322b77aa333ac7712725b5d774f`. `git status` al cierre: sólo `?? experiments/_s163_diurno_k/verificador_v31/` (no toqué nada más del repo).
- Modelo: Sonnet 5.5, esfuerzo bajo. Lista de caminos escrita antes de abrir el diff: `verificador_v31/CAMINOS.md`, sha256 `757332df014cd5086b368dd4db8f37ad9b9fe683114c9ff7c63ca16fd2990a92`, hora `14:32:53 GMT`.
- Procesos: no lancé ninguno en segundo plano ni terminé ninguno.

## Respuesta corta

Los cuatro cambios hacen lo que dicen y no encontré ningún camino por el que la v3.1 adopte algo que la v3 no adoptaba: la variante d y el tope de GANA sólo pueden convertir ADOPTAR o NO ADOPTAR en DECIDE NICOLÁS o INDECIDIBLE (`veredicto_final` solo degrada, `evaluar_diurno_k.py:137-143`). Lo que sí encontré es que **dos de las partes nuevas no están vigiladas por ninguna prueba** (V1 y V2: quitar el filtro de día de la reclasificación, o desconectar el tope de GANA de la compuerta, deja la batería en 80 de 80), y una sospecha de costo (V3: la variante d falla I6 por azar más a menudo). Ninguno es de gravedad 3 o más. Conformidad: **conforme con reservas de gravedad 2 sobre la cobertura de pruebas**, ninguna sobre el veredicto.

## Veredicto por cada uno de los cuatro cambios

| # | Cambio | Veredicto | Resumen |
|---|---|---|---|
| 1 | variante d reclasifica FALSO_POSITIVO diurnos de la tabla a RUTINA | **CONFIRMADO** (el código); la prueba que lo vigila, **CONFIRMADO EN PARTE** (V1) | Toca sólo VIIRS, de día, fuente CONS, sólo con `otra_como_negativo=True`. |
| 2 | placebo c: GANA aparte, `MAX_GANA_C = 4` | **CONFIRMADO** (el código y el umbral); el cableado a la compuerta no tiene prueba propia (V2) | Cuenta sólo GANA; falla con 5 o más de 40; 0,048 sale de la binomial. |
| 3 | textos §5.1 (iii), §6.3, §6.4, §8, §14 | **CONFIRMADO EN PARTE** | Coinciden con el código salvo el matiz de «esas 265 y 60 pasadas» (V5) y la lectura de FALSO_POSITIVO (V6). |
| 4 | sello de 22 a 29 archivos y `git diff` del §8 | **CONFIRMADO** | 29 de 29 sha256 coinciden; el comando corre tal como está escrito (en bash); cierre de imports sin huecos (V7 menores). |

M57, M58 y M59: **CONFIRMADO** atrapadas por aserción (una prueba cada una) en una copia de `git archive` fuera del worktree.

## Hallazgos (ordenados por gravedad)

### V1 · Ninguna prueba vigila el filtro de día de la reclasificación: sin él, la variante d tocaría las pasadas nocturnas y la batería sigue en 80 de 80 · `evaluar_diurno_k.py:403-404` · CONFIRMADO · GRAVEDAD 2
- QUÉ PASA: la condición `es_dia_vol(p.volcano, p.instante)` (línea 404) es la única que impide que los FALSO_POSITIVO nocturnos de VIIRS pasen a RUTINA. Los dos tests nuevos sólo ponen FALSO_POSITIVO diurnos (`test_completo_otra_como_negativo_incluye_falsos_positivos`). Con el filtro quitado (mutación N3 mía), 80 de 80 pruebas siguen en verde.
- CÓMO SE VERÍA EN EL RESULTADO: no hoy (el código está bien), sino tras una edición futura: la variante d contaría como negativos nocturnos de producción más pasadas, cambiaría Q_n y con ella el caso e-i (`Q_d <= Q_n`, `veredicto_sensor`). Medido sobre la referencia congelada: Q_n de VIIRS 375 pasaría de 0,0367 (1.606 negativos) a 0,0486 (1.853), y la de VIIRS 750 de 0,0093 (2.375) a 0,0092 (2.399). No es un mutante equivalente.
- CÓMO REPRODUCIRLO: `python -I experiments/_s163_diurno_k/verificador_v31/mutar_propias.py <copia de git archive>` (fila N3, `mutar_propias_salida.txt`) y `python -I experiments/_s163_diurno_k/verificador_v31/n3_efecto.py <ref congelada>` (`n3_efecto_salida.txt`).

### V2 · Ninguna prueba vigila que `compuerta_i6` le pase los GANA a `juzgar_i6`: el tope puede quedar desconectado sin que nada caiga · `evaluar_diurno_k.py:146` (`gana_c=0` por defecto) y `:381` · CONFIRMADO · GRAVEDAD 2
- QUÉ PASA: `juzgar_i6(res_a, det_a["B"], falsos, gana)` (línea 381) es correcto hoy. Si se borra el cuarto argumento, `gana_c` vale 0 por defecto, el tope de GANA no actúa nunca y la batería da 80 de 80 (mutación N1 mía). M58 atrapa la constante y M59 el contador, pero ninguna prueba mira el tramo entre los dos: `test_i6_cuenta_los_gana_...` sólo compara `c_gana` contra la cuenta a mano, y `test_i6_juicio_de_placebos` llama a `juzgar_i6` directo.
- CÓMO SE VERÍA: I6 volvería a ser el de la v3 (hasta 7 GANA y 0 PIERDE pasan), en silencio, y justo en el lado que lleva a adoptar. Dirección: sobre-adopción potencial ante una edición futura.
- CÓMO REPRODUCIRLO: fila N1 de `mutar_propias_salida.txt`. El valor por defecto 99 (N10) sí cae, así que el hueco es el cableado, no la firma.

### V3 · La variante d falla I6 más a menudo que antes, y cada fallo la vuelve INDECIDIBLE y fuerza DECIDE NICOLÁS · `evaluar_diurno_k.py:588-600` y `veredicto_final` (137-143) · SOSPECHA · GRAVEDAD 2
- QUÉ PASA: armé un brazo ruidoso (publica al azar con q = 0,05 en las pasadas diurnas; referencia congelada 047bd5692, ventanas W2 a W6) y corrí `evaluar` en el principal y en la variante d con las mismas 20 semillas del brazo, con el código de la v3 y el de la v3.1. VIIRS 375 en la variante d: **0 de 20** corridas con I6 fallido en la v3 y **2 de 20** en la v3.1 (con 26 semillas: 2 de 26). Los dos fallos son por la suma de GANA y PIERDE mayor que 7, no por el tope nuevo. Principal: 0 de 20 en ambas. Cuando el principal es ADOPTAR o NO ADOPTAR y una variante da INDECIDIBLE, `veredicto_final` lo manda a DECIDE NICOLÁS.
- CÓMO SE VERÍA: DECIDE NICOLÁS por un azar del placebo en un caso que el principal resolvía solo. Dirección: sub-adopción segura, con costo de revisión humana.
- LÍMITE: n = 20, pareado, sin interpretar el mecanismo (la reclasificación agrega 123 pasadas a los negativos diurnos y cambia los bloques del placebo, pero no lo demostré). Es SOSPECHA hasta repetir con más semillas.
- CÓMO REPRODUCIRLO: `VRP_R=<copia de git archive 987a7601> python -I verificador_v31/i6_variantes.py <ref> 0.05 20` (`i6_variantes_v3_q05_salida.txt`) contra `i6_variantes_q05_salida.txt` (código v3.1, 26 semillas). 19 s por semilla.

### V4 · El 0,048 del texto es la tasa por evaluación y por sensor; I6 se evalúa unas 10 veces por corrida y la tasa conjunta no está dicha · `PREREGISTRO.md` §5 I6 · SOSPECHA · GRAVEDAD 1
- QUÉ PASA: `P(Bin(40; 0,05) >= 5) = 0,048` está bien calculado (lo recalculé: 0,04803). Pero `evaluar_completo` llama a `evaluar` (con I6 en cada sensor) para el principal y las cuatro variantes, o sea 10 compuertas I6 correlacionadas. Con las tasas por sorteo que midió el verificador v3 (`verificador_v3/placebo_c_tasa_salida.txt`, GANA 3,5 a 5,25 % y PIERDE 2,5 a 4,75 %), simulé el falso fallo por compuerta: sube de 0,7 a 1,5 % (v3) a 2,4 a 5,9 % (v3.1) (`conjunto_i6.py`). En mis 26 corridas el tope nuevo no agregó ningún fallo (columna «v3.1» igual a «v3»).
- CÓMO SE VERÍA: INDECIDIBLE o DECIDE NICOLÁS más frecuentes; nunca un ADOPTAR indebido.

### V5 · «esas 265 y 60 pasadas» sigue sin ser exacto: la variante d pesa 263 y 59 · `PREREGISTRO.md` §6.4 (d), línea 371 · CONFIRMADO · GRAVEDAD 1
- Medido sobre la referencia congelada: VIIRS 375 diurno trae 106 FALSO_POSITIVO, 2.403 RUTINA y 2 «sin geometría» de OCR; los negativos pasan de 2.246 a **2.509** (= 2.246 + 157 + 106). VIIRS 750: 17, 2.475 y 1; negativos de 2.433 a **2.492** (= 2.433 + 42 + 17). Las 2 y 1 «sin geometría» siguen siendo «otra». Las 265 y 60 del texto incluyen esas (`real_c1_salida.txt`). Mismo reparo que la v3 hizo en su V3-1 («59 % y 70 %»), ahora resuelto en lo sustancial (123 de 125 FALSO_POSITIVO y RUTINA) y no en la frase.

### V6 · Leer FALSO_POSITIVO como «MIROVA no alertó» es la lectura más estricta, no la única · `PREREGISTRO.md` §6.4 (d), línea 370; `evaluar_diurno_k.py:401-403` · SOSPECHA · GRAVEDAD 1
- QUÉ PASA: el texto pone «(MIROVA no alertó en el radio)». Según la nota de la memoria del proyecto `reference_mirova_csv_scraper_tags.md` (tabla de tags), FALSO_POSITIVO es «MIROVA detectó hotspot pero fuera del radio asignado al volcán» (MIROVA sí vio algo en la escena). El evaluador común lo deja fuera de los negativos limpios por eso (`scripts/evaluador_comun.py:442`). Una publicación del brazo en esa pasada podría ser el mismo calor que MIROVA vio y descartó por distancia; la variante la contaría como publicación de más. Sólo es una variante: baja a DECIDE NICOLÁS, nunca adopta. No mido cuántas de las 123 serían de ese tipo.

### V7 · Menores del sello y del §8 · CONFIRMADO · GRAVEDAD 1
- El comando del §8 es sintaxis de bash (`$(...)`, `grep`, `awk`); en PowerShell no corre. Con un path inexistente en las dos revisiones `git diff` sale vacío y rc 0 (comprobado), así que un typo en `objetivos_sha256.txt` pasaría por «nada cambió». No cubre `objetivos_sha256.txt` mismo (no se lista a sí mismo; sí aparece como único cambio entre e5042a2e y 9700e4e0).
- `pytest.ini` se abre al correr la batería y no está sellado (sólo `testpaths` y `markers`; no cambia nada con ruta explícita).
- En esta máquina `git archive` entrega los archivos con CRLF: `evaluar_diurno_k.py` extraído da sha256 `4659d05d...` contra `d6eb25b5...` del blob (42.934 contra 42.161 bytes). El texto del §8 ya dice que los sha son de blobs; vale la pena que quien compruebe contra el archivo extraído lo sepa.

## Evidencia de cada comprobación

**Cambio 1 (reclasificación)**, camino por camino (CAMINOS.md C1a a C1h):
- C1a, C1b: sobre la referencia congelada (W2 a W6, canal unión, 12.346 pasadas) comparé `clase_p2`, `es_dia` y estado de cada pasada entre `evaluar(..., otra_como_negativo=False)` y `=True` (`real_c1.py`, `real_c1_salida.txt`). Pasadas nocturnas que cambian de clase o de estado: **0**. MODIS: ninguna (sus 3 FALSO_POSITIVO son nocturnos y no cambian). Los 123 cambios de estado `fp` a `rutina` son exactamente los FALSO_POSITIVO diurnos de la tabla (106 de VIIRS 375 y 17 de VIIRS 750), y todos terminan «negativo». Los conteos de negativos del principal (2.246 y 2.433) coinciden con `nulo_estructural_salida.txt`.
- C1c: la reclasificación sólo corre con `otra_como_negativo=True` (línea 400); la mutación N6 («siempre») cae por aserción. De las nueve llamadas a `evaluar` de `evaluar_completo` (líneas 593-609) sólo la de la variante d pasa `otra_como_negativo=True`.
- C1d: `NamedTuple._replace` sólo cambia `estado`; `vrp_mw`, `dist_km`, `fuente`, `instante` quedan. Ni `clave` ni `record_de` ni `es_protegida` (exige `estado == "alerta"`) se alteran. La lista de entrada no cambió (`assert pas == copia` pasó en `real_c1.py`).
- C1e: sólo `fuente == "CONS"`. En la referencia no hay FALSO_POSITIVO de OCR (la tabla de conteos de `real_c1_salida.txt` no los trae). Quitar el filtro de fuente (N5) o de sensor (N4, N11) no cambia ningún resultado en producción, porque `clase_p2` ya exige `fuente == "CONS"` para ser negativo y `pasadas_de` ya saca MODIS de día; son mutantes equivalentes, no huecos.
- C1f: todo lo que sigue usa la lista reclasificada: `marcadas`, `T = ec.tabla_por_pasada(pas, ...)`, `compuerta_i2(... marcadas_eval ...)` (líneas 407-415 del archivo). Una sola población.
- C1g: una pasada con alerta y FALSO_POSITIVO es «alerta» (`_estado`, orden alerta, mínima, fp, rutina); no se toca.
- Dirección: más negativos con las mismas publicaciones sólo puede subir el neto o bajar Q_d. La variante nunca produce un veredicto final más permisivo que el principal (`veredicto_final` sólo degrada).

**Cambio 2 (placebo c)**:
- Umbral: `binom.sf(4, 40, .05) = 0.048028`, `binom.sf(3, 40, .05) = 0.1381`; `binom.sf(7, 40, .10) = 0.0419`. `gana_c > MAX_GANA_C` con `MAX_GANA_C = 4` falla con 5 o más (N8, con `>=`, cae). `len(SEMILLAS_C) = 40` (161 a 200).
- Conteo: `gana += res_c == "GANA"` (línea 378) cuenta sólo GANA; N2 (GANA o PIERDE) y N12 (`c_gana` igual a `falsos`) caen. `falsos` no cambió.
- En la humo regenerada de la v3.1 aparece `c_gana` (1 y 3) y los `c_falsos` no cambian respecto de la v3 (`git diff` de `humo_c0_W6b_salida.txt`).
- Hueco de cableado: V2.

**Cambio 3 (textos)**:
- §5.1 (iii) y §6.3 contra `veredicto_global` (líneas 111-135): el único camino a ADOPTAR global es VIIRS 375 en ADOPTAR y VIIRS 750 en SIN CAMBIO; y SIN CAMBIO sólo sale de `veredicto_sensor` con `neto <= 0`, sin beneficio y sin que el brazo publique nada diurno en ese sensor. Un brazo que publica exactamente las alertas da ADOPTAR por sensor (`nulo_estructural_salida.txt`: «e-i ADOPTAR» en ambos) y DECIDE NICOLÁS global por la rama de VIIRS 750. Consistente.
- §14: los IDs y gravedades de la tabla (V3-1 a V3-6: 2, 2, 2, 1, 1, 1) coinciden con `verificador_v3/INFORME.md`. «80 pruebas» confirmado (corrí la batería: `80 passed in 8.32s`; las dos nuevas son las del diff).
- Una afirmación que no auditó nadie en esta pasada: «la tercera mirada no encontró ningún camino nuevo a un ADOPTAR indebido» (§14 y encabezado). Lo que leí en `verificador_v3/INFORME.md` (V3-3, «no abre ningún camino a un ADOPTAR indebido») la apoya para la regla de VIIRS 750; no revisé el diff v2 a v3.
- El nulo (`nulo_estructural.py`) no llama a `evaluar`, `juzgar_i6` ni `compuerta_i6`, así que su salida de la v2 no queda invalidada por este diff; no lo re-corrí.

**Cambio 4 (sello)**:
- `git show e5042a2e:<ruta> | sha256sum` contra las 29 filas de `objetivos_sha256.txt`: **29 OK, 0 distintas**, 29 filas (`grep -vc '^#'`). Entre e5042a2e y 9700e4e0 sólo cambió `objetivos_sha256.txt`.
- Cierre de lo que se lee: `gancho.py` (hook de auditoría de Python sobre la batería más `sys.modules` tras importar `nulo_estructural`, `sustrato_k`, `congelar_referencia`) y un import real de `evaluar_diurno_k`, `banco_paridad` y `sustrato_k`: ningún archivo del repo cargado o abierto fuera del sello, salvo `objetivos_sha256.txt` y `pytest.ini`. No leí `data/` del brazo ni la referencia (entran por argumento).
- Comando del §8 corrido tal como está, con sello `e5042a2e...` y etiqueta `9700e4e0...`: salida vacía, rc 0. Control positivo con `987a7601` como sello: «4 files changed, 119 insertions(+), 17 deletions(-)».

**Mutaciones del autor (M57 a M59)** en `git archive 9700e4e0` fuera del worktree (`mutar_m57_59_salida.txt`): M57 cae por `test_completo_otra_como_negativo_incluye_falsos_positivos`; M58 por `test_i6_juicio_de_placebos`; M59 por `test_i6_cuenta_los_gana_del_placebo_simetrico`; cada una 1 fallo, 79 verdes. Tras restaurar, el archivo vuelve al sha256 del blob. Mis mutaciones N1 a N12 (`mutar_propias_salida.txt`): caen N2, N6, N7, N8, N9, N10, N12; sobreviven N1 (V2), N3 (V1), y N4, N5, N11 (equivalentes).

## VERIFICADO LIMPIO

- Reclasificación acotada a VIIRS diurno de la tabla: 0 cambios nocturnos y 0 en MODIS sobre 12.346 pasadas reales (vara: comparación pasada por pasada entre las dos llamadas, `real_c1.py`).
- La reclasificación no cambia el principal, no muta la entrada y mantiene una sola población en todo `evaluar` (N6 cae; `pas == copia`).
- Umbral y semántica del tope de GANA: binomial recalculada, `>` frente a `>=`, 40 semillas, contador sólo de GANA (varas: `scipy.stats.binom`, mutaciones N2, N8, N9, N12).
- Sello: 29 de 29 sha256 contra los blobs de e5042a2e; comando del §8 vacío cuando debe y no vacío con control positivo; cierre de imports sin huecos (vara: hook de auditoría).
- Batería: 80 de 80; M57 a M59 atrapadas por aserción (no por caída) en copia de `git archive`.
- Coherencia texto y código de §5.1 (iii), §6.3 y la tabla de §14 (vara: `veredicto_global`, `veredicto_sensor`, `verificador_v3/INFORME.md`).

## SIN DATO

- Mecanismo exacto por el que la variante d falla I6 más seguido en VIIRS 375 (V3): n = 20, pareado, no repetí con más semillas.
- Cuántos de los 123 FALSO_POSITIVO diurnos son el mismo calor que el brazo detectaría (V6).
- Qué pasa con las 62 mutaciones previas sobre la v3.1: el autor dice que no repitió la corrida completa (§14) y yo tampoco; sólo corrí M57 a M59 y las mías.
- El nulo y la prueba de humo con datos reales de W2 a W6: no re-corrí `nulo_estructural.py` ni `evaluar_diurno_k.py` sobre corridas del A/B (no tengo las raíces); sólo usé la referencia congelada (`congelar_referencia.py --commit 047bd5692`, 4 CSV con sha256 OK).

## QUÉ NO MIRÉ

- El diff de la v2 a la v3 ni el resto del pre-registro fuera de los cuatro cambios (§0 a §4, §7, §9 a §13) ni la regla R1 o la prueba D.
- `pipeline/diurno.py`, perfiles YAML, workflow de despacho, `main()` y la sección de W1.
- Versiones de numpy y scipy (la prueba de signos usa sorteos y `binom`); no están selladas ni declaradas en el diff.
- No audité el criterio de victoria de `docs/MISSION.md` ni cité PDFs: no hizo falta para este diff.

## Archivos de esta carpeta

`CAMINOS.md`, `gancho.py`, `real_c1.py` y `real_c1_salida.txt`, `i6_variantes.py`, `i6_variantes_q05_salida.txt`, `i6_variantes_v3_q05_salida.txt`, `conjunto_i6.py`, `mutar_propias.py` y `mutar_propias_salida.txt`, `mutar_m57_59.py` y `mutar_m57_59_salida.txt`, `n3_efecto.py` y `n3_efecto_salida.txt`. Referencia congelada y copias de `git archive` en el directorio temporal de la sesión.
