# Verificación con contexto limpio del informe de cambios al paper (S152, 2026-10-16)

Informe verificado: `C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\INFORME_CAMBIOS_PAPER.md`.
Repo en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile`, rama `loop/activo`, HEAD `f3520f4d5`
(sin cambiar de rama ni editar). Scripts propios de sólo lectura en
`C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\verif\` (`dia_recuperadas.py` y dos CSV extraídos de
`83b9df8ff` con `git show`).

## 0. Veredicto global: ENTREGAR CON CORRECCIONES

El núcleo del informe se sostiene: ninguna de las 14 FALSA queda refutada. Dos están mal clasificadas (5-5 y
5-24 no eran falsas cuando se escribieron), tres de las cinco graves necesitan una precisión que cambia cuánto
pesan, y un SIN LOCALIZAR sí se localiza. Las citas a `TABLAS.md` apuntan a líneas que no existen.

Conteos sobre 33 ítems revisados: **CONFIRMADO 19, CORREGIR 14, REFUTADO 0**.

- FALSA (14): 12 CONFIRMADO (3 de ellos con una precisión de peso o de unidad), 2 CORREGIR (reclasificar).
- Las 5 graves: 1 CONFIRMADO, 4 CORREGIR (precisión, no refutación).
- Muestra de SIN CAMBIO (5): 5 CONFIRMADO.
- Otros revisados (9): 1 CONFIRMADO, 8 CORREGIR (dos de ellos suben un SIN LOCALIZAR o una SOSPECHA a dato verificado).

Advertencia de conteo: 6-3, 6-14 y 6-16 son la misma premisa falsa («la referencia no tiene negativos»)
contada tres veces. Las 14 FALSA son 12 errores independientes.

## 1. Las 14 FALSA

| id | veredicto | qué lo decide |
|---|---|---|
| 5-1 MxD03 | CONFIRMADO | `pipeline/process_modis.py:470-471` («geo_path is accepted ... but not used», desde `c3e8aca603`, 2026-04-04, así que ya era falso al escribirse); `_interp_geo` en `:342`, usado en `:291-293`; `fetch.py:189-194` baja MOD03/MYD03. Dos matices al texto propuesto: el corrimiento de 1,15 a 2,58 km es **del lado del frame 0** del barrido, no de todo el cenit sobre 30°, y sale de 7 gránulos con veredicto PARCIAL (`experiments/_s151_probe_mod03/README.md:6-20`); la cita «`:30-32` lat/lon gruesas» es `:34-35` |
| 5-3 día | CONFIRMADO | Campus 2022 p. 16-17 según `experiments/_s151_alertas_diurnas/README.md:120-124`; el propio §4 del borrador dice que las falsas alertas ocurren «mainly in daytime images» (`sec4_background.md:133-134`). Ya estaba marcado en las notas del editor (H2, `sec5_methods.md:297-301`): no es hallazgo nuevo. Además «cold at 11 µm» (`sec5_methods.md:31`) es justo la frase que la nota de §6 (`sec6_validation.md:238-239`) dice no estar en la literatura y haber quitado |
| 5-4 cron | CONFIRMADO | S139 ya medía unas 5 corridas al día antes del borrador (`docs/audit_s139/NRT_CADENCIA_Y_MEJORAS.md:1`); 34 corridas del 2026-09-25 al 2026-10-02 (`docs/audit_s150/VERIFICADOR_AUDITORIA.md:319-321`) |
| 5-5 experimental | **CORREGIR: DESACTUALIZADA, no FALSA** | `experimental` salió del cron NRT el 2026-09-14 15:28 (#667, `2bcc9916a`) y la última edición de `sec5_methods.md` es del 2026-09-14 16:55 (`0d483e53c`): en esa fecha la frase era cierta. Dejó de serlo el 2026-10-09 con `experimental-diario.yml` (#775, `600cb6f09`, `git log --diff-filter=A`). El texto propuesto vale |
| 5-23 D17 | CONFIRMADO | `ENABLE_UTM_REGRID = False` (leído de `pipeline.profile`); título de D17 «Nuestra grilla F70 se centró en el punto equivocado» (`docs/MIROVA_DIVERGENCES.md:2205`); contradice `sec5_methods.md:116` |
| 5-24 D18 | **CORREGIR: REBAJADA** | Literalmente, un A/B corrió y no mejoró la paridad (D18 l. 2301); lo que cayó es que midiera la caja (marca S148). La primera medición válida también falló (veto, l. 2303-2310), así que la conclusión «documented rather than removed» sigue en pie. Y el texto propuesto afirma que la posición del píxel del veto «is itself affected by the MODIS geolocation error»: está SIN VERIFICAR (`experiments/_s151_probe_mod03/README.md:20`: «SIN VERIFICAR: ... la posición MxD03 del píxel del veto»; D18 l. 2307: mecanismo SIN VERIFICAR). Decir «may be affected» |
| 6-2 cobertura | CONFIRMADO | Lógica: una alerta no capturada que también habríamos perdido sale del denominador y sube la recall. 79,2 % es por pasada contra el archivo TIF y cota superior (`docs/AUDIT_S128.md:262-276`) |
| 6-3 sin negativos | CONFIRMADO | `latest_consolidado.csv`, ventana 2026-01-01 a 08-31: 32.751 filas RUTINA (MODIS 10.089, VIIRS 12.342, VIIRS375 10.320), mediana de VRP 0,0. MIROVA publica pasadas con VRP 0. Definición del negativo limpio en `docs/audit_s139/MAPA_BASES_MIROVA_V1.md:312` |
| 6-4 diurnas | CONFIRMADO el hecho, **CORREGIR el peso** | Sin filtro horario: `pipeline/mirova_csv_loader.py:146-206`, `scripts/paper_numbers.py:194-205`, y nunca lo hubo (`git log -S"hour"` vacío; tampoco en `83b9df8ff`). 19 / 5 / 6 noches sólo diurnas reproducidas. Pero `verif/dia_recuperadas.py` muestra que **14 de las 19 V375 ya cuentan como recuperadas** (un record nocturno del mismo día UTC), 3 de 5 en V750 y 1 de 6 en MODIS tablero. Excluirlas mueve la recall de 0,931 a 0,936 (V375), 0,803 a 0,808 (V750, referencia de hoy) y 0,122 a 0,118 (MODIS). Es falso como enunciado, chico como número |
| 6-7 cráter válido | CONFIRMADO, **CORREGIR la unidad** | 89,1 % de 4.800 y 93,7 % de 158 son **por pasada** (ventana 2026-01-29 a 08-28, `docs/audit_s146/FASE0_VERIFICADOR.md:89`); el 0,976 del paper es **por noche**. La comparación correcta es por noche: 98,2 % de las noches de negativo limpio con cúmulo en el cráter (`docs/audit_s146/VERIFICADOR_CONTEXTO_LIMPIO.md:217`), más que el 0,976 de las noches con alerta. El argumento sale más fuerte, no más débil |
| 6-9 MODIS | CONFIRMADO, **CORREGIR el texto propuesto** | `docs/S150_RESULTADO_MESES.md:49-58`. El brazo J que da 68/73 contra 11/96 es banda 22 **y sin Test 1 integrado**; producción en esa misma población publica 8/73 contra 1/96 (l. 62-64). «With band 21 ... the detector does not separate» no es exacto: lo que no separa es la presencia del cúmulo; producción publica poco en los dos lados. Decir «band 22, without the integrated Test 1» y que es por pasada y un solo volcán |
| 6-14 | CONFIRMADO | Misma evidencia que 6-3 (duplicado) |
| 6-16 | CONFIRMADO en la premisa | Lo de «no upper bound ... requires negative labels» cae con 6-3. Lo de «suppressing ... would remove the added value» no es falso: cambió el objetivo (`docs/MISSION.md:47-90`, 2026-10-13); esa parte es DESACTUALIZADA |
| `definiciones` «nocturna 03-09 UTC según el loader» | CONFIRMADO | Ver 6-4 |

## 2. Las 5 más graves

1. **Negativos**: CORREGIR. La premisa es falsa (6-3). Pero el 86,1 % / 21,4 % / 5,1 % es del 2026-09-01 al
   09-20, régimen posterior a #535, **no la tasa de los records que valida el paper**. Para el tramo anterior
   el proyecto tiene 62,1 % por pasada en VIIRS 375 (A104; `docs/audit_s146/FRENTE_B_CIERRES_CON_SCRIPT.md:72`
   anota que la salida persistida hoy da 62,6 % de 358, ventana corta) y 100 % por noche
   (`docs/audit_s146/FRENTE_D_CIERRES_CON_NUMERO.md:80`). Si §6 se queda en enero a agosto, no puede citar 86,1 %.
2. **Diurnas**: CORREGIR. Ver 6-4: numéricamente casi no mueve la recall. Y el «40 diurnas contra 232
   nocturnas» es de otra ventana (2026-01-10 a 2026-10-14, A119 aplicado, los tres sensores;
   `experiments/_s151_alertas_diurnas/README.md:134-153`), y de esas 40, **19 tienen magnitud desproporcionada
   (probable reflejo) y 21 no tienen evidencia**. «Perderlas no es lo correcto» lo decide el criterio de
   fidelidad del 2026-10-13, no la física. El 232 de acá no es el 232 de V375 del ítem 6-6: dos cosas distintas con el mismo número.
3. **MxD03**: CONFIRMADO con los matices de 5-1.
4. **MODIS §6.3**: CORREGIR la unidad (6-7) y el texto propuesto (6-9).
5. **Methods / D18**: magnitud publicada (5-11, 5-12) CONFIRMADO (`docs/FICHA_SDA_VRP_CHILE.md:25`, 75,5 %;
   flags leídos de `pipeline.profile`). D18: ver 5-24. Conectiva: CORREGIR un número (ver §3, ítem 4-1/5-7).

## 3. Otros ítems revisados

| id | veredicto | qué lo decide |
|---|---|---|
| 6-13 (30/193, 210/214) | **CORREGIR: SIN LOCALIZAR pasa a DESACTUALIZADA, localizado** | Salen del `numbers.json` de `c421005c8` y `5a2bf24f2` (2026-09-07), **antes del recorte de la ventana de ground truth** de `994c9f842` (#604), que los bajó a 24/187 y 204/208. Los 6 de más son noches posteriores al fin del CSV contadas como «sin alerta», el sesgo que ese recorte vino a quitar. El texto de §6.5 no se regeneró |
| V750 246 a 244 | **CORREGIR: SOSPECHA pasa a CONFIRMADO** | Cargando los CSV de `83b9df8ff` contra los de hoy: las dos noches que faltan son PCC V750 2026-02-26 (fila 05:24, 0,75 MW) y 2026-08-18 (05:48, 0,64 MW), `ALERTA_TERMICA` presentes en el consolidado viejo y **borradas** del actual (no reclasificadas). Es la pérdida silenciosa de la tarea 0.1 |
| `tabla2` 26.028 | CONFIRMADO (SIN VERIFICAR pasa a verificado) | Cortando cada volcán en su `ultimo_record` del paper se obtienen exactamente 26.028 |
| 6-11 (cifra no tocada) | CORREGIR, hallazgo propio | `sec6_validation.md:116` dice «Isluga 0.580 (310)»; hoy da 0,582 sobre 308 (`repro_0831`), por la misma pérdida de filas. Láscar V750 178 a 177 no está en el texto |
| 4-1 y 5-7 | CORREGIR un número | «Con `max`, V375 baja de 35,7 % a 2,7 %» compara brazos **sin Test 1** (B contra F, `docs/S150_RESULTADO_MESES.md:45-48`), no producción contra `max`. Y el recall de esos meses sigue pendiente de Nicolás (l. 34-41) |
| 4-9 | **CORREGIR: SIN CAMBIO** | La nota 8 (`sec4_background.md:283-287`) ya dice que «Muy Bajo» es la etiqueta del sitio y no del paper; sigue siendo cierta. Sólo cabe agregar la fecha de observación |
| T-1 | CORREGIR la línea | El pie está en `TABLAS.md:37`, no `:89` (el archivo tiene 81 líneas) |
| T-2 | CORREGIR la línea | La cabecera es `TABLAS.md:4`, no `:55-56` |
| T-3 | CORREGIR la línea | `TABLAS.md:32`, no `:84` |

## 4. Muestra de SIN CAMBIO

| id | veredicto | qué lo decide |
|---|---|---|
| 4-5 fondo y suma | CONFIRMADO | `sec4_background.md:24-30`: atribuido al paper, correcto como descripción de MIROVA |
| 4-6 grillas | CONFIRMADO | `sec4_background.md:98-116`, coherente con D17 S141 (l. 2207-2213) |
| 5-22 D13 | CONFIRMADO | «part of the detected magnitude» no fija número; el 70,7 % es opcional |
| 6-5 no supervisadas | CONFIRMADO | A105 y la cita a Coppola 2026 p. 7 ya están en el texto |
| 6-12 razones extremas | CONFIRMADO | PP V750 6,783 sobre 2, Tupungatito V750 0,090 sobre 3, PP V375 171 y Tupungatito V375 209 pares: idénticos en `repro_0831` (el diff contra `numbers.json` sólo muestra Isluga V375, Láscar V750 y PCC V750) |

## 5. Lo que no verifiqué

- No rendericé ninguna página de PDF; las citas a Campus 2022, Coppola 2014 y 2016a quedan como el informe dice: tomadas de documentos del repo.
- No corrí la suite ni ningún A/B; los porcentajes de A/B se comprobaron contra sus documentos de resultado.
- 5-13, 5-15, 5-16, 5-18 a 5-21, 5-25 a 5-27 y 6-15 a 6-18 no los revisé uno a uno.
