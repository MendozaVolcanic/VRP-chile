# Bloque de arranque S142

> Cierre de S141 (2026-09-14 16:28 a 2026-09-15 12:30 UTC, hora del servidor). Rama `main` en
> `112018870`, verificado igual al remoto con `git ls-remote` antes de este commit. Sin PR abiertos,
> sin worktrees extra, sin corridas en curso, los 4 stashes de S72 a S78 intactos. Los commits del cron
> NRT y del sync seguirán aterrizando sobre `data/`; no invalidan nada. Sin agentes vivos al fijar el
> estado. Suite: NO re-corrida en el cierre (el CI de #675 salió verde); anota el conteo real al retomar.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| Tarea 7 (radiancia de fondo persistida) | **verificada en NRT** | run 34866860598; campos con valores en los 11 Tier A |
| Upgrade NRT a standard de `store.py` | **corre** (VIIRS y, tras re-etiquetar, MODIS) | 173 `STORE upgrade` MODIS en run 34881778236 |
| Auto-audit: Láscar e Isluga sub-banda conocidos | mergeado | #664; issues #511 #568 #603 #661 cerrados |
| `scripts/remapear_citas.py` (A101) | mergeado | #665; validado contra el remapeo manual de la T7 |
| Re-etiquetado MODIS NRT por nombre de granule | script #666 + data aplicada | `ab76888cf`; 254 records; tag `pre-s141-relabel-modis-nrt` |
| T8a: perfil experimental fuera del cron | mergeado y verificado | #667; paso `skipped` en los 11 jobs; Láscar 40 a 18 min |
| Umbrales de terminado congelados | mergeado | #668; sin medir la consistencia del propio MIROVA (escrito) |
| Tarea 10: lectura de papers verificada | mergeado | #669; `docs/audit_s139/LECTURA_PDF_SEGUNDA_PASADA.md`; notas D14 D17 D18 D20 D25 D28 |
| Manuscrito: citas con paper, página y párrafo | mergeado | #670; secciones 4, 5 y 6 |
| Fase 1, probe v1 (vecino del foco) | **INDETERMINADO, lecturas retiradas** | #671 #672 #673; `experiments/_s141_fase1_probe/RESULTADOS.md` y `VERIFICADOR.md` |
| Nevados de Chillán jun-sep + cambio de régimen tras #535 + cron evaluado | mergeado | #674; `docs/S141_NDC_JUNIO_SEPTIEMBRE.md`, `experiments/_s141_ndc/regimen_535.json`, `docs/audit_s141/NRT_CRON_EXTERNO.md` |
| Fase 1, probe v2 (márgenes por test de detección) | **corrido, SIN interpretar** | #675; run 34967596160; controles C1 a C4 = 1,0 en 38 pasadas; `juntar.py` da HETEROGENEO en focal e INDETERMINADO en nevado; artefactos y `criterio_total.json` commiteados en este cierre |
| Artículo Scientific Data Coppola 2026 + User Guide del dashboard OSF | descargados y leídos en páginas renderizadas | `documentacion/` (fuera de git): PDF + .md de cada uno |
| Cron NRT | **sin cambio**; atraso de creación del evento | `experiments/_s141_cron/atraso_despacho.json`; último NRT 07:12 UTC al cerrar |
| Tarea separada: TIF vacíos en mirova-tif-archive | chip creado, no iniciado | TIF NdC 20260913_051801 de 0 bytes |

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Cron externo del NRT | A servicio externo (cron-job.org) con token fine-grained que creas tú · B tarea programada de Windows con `gh` · D dejar el de GitHub | **A** con el cron de GitHub de respaldo, horas impares `10 1-23/2 * * *`; detalle en `docs/audit_s141/NRT_CRON_EXTERNO.md` |
| 2 | Estrato nevado del probe v2 (sin candidatos nuevos) | otra ventana del OSF · reusar pasadas del v1 · dejar sólo focal | **otra ventana del OSF** (2024 o parte de 2025 no muestreada): reusar pasadas ya miradas contamina el pre-registro |
| 3 | Piso VRP (S130 lo quitó "porque el canon no lo respalda") frente a la Tabla 1 del artículo Scientific Data, que aplica umbrales por sensor al archivo | reabrir el A/B · dejar como está · preguntar a Coppola | **no reabrir todavía**: el artículo describe el ARCHIVO; primero confirmar con el correo a Coppola si el NRT publicado usa esos umbrales (pregunta nueva) |
| 4 | Correo a Coppola (borrador `docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`) | enviar · ajustar con S141 · no enviar | **ajustar y enviar**: agregar la pregunta del piso NRT, el cambio de formato de TIF y la conectiva; las lecturas S141 ya contestan parte de 4 y 6 |
| 5 | Token Earthdata | renovar ya · esperar el issue | **renovar esta semana**: vence 2026-10-03 07:18 UTC (leído del JWT por el healthcheck) |

## c. Lo aprendido

**Reglas generales del workspace** (ya en memoria del agente; proponer para `GUIA_MAESTRA_AUDITORIAS.md` §7):

1. **Un job de CI en verde no prueba que el script corrió.** `python ... | tee` sin `set -o pipefail` devuelve el código de `tee`: la primera corrida del probe salió verde en ~1 min sin procesar nada. Mirar duración y salida antes de leer resultados.
2. **Envolver `sys.stdout` dos veces cierra la salida.** El primer `TextIOWrapper` queda huérfano y al recolectarse cierra el buffer compartido. Envolver una sola vez, en el punto de entrada.
3. **Verificar el instrumento ANTES de correrlo** con un verificador limpio: en el v2 encontró que la pregunta estaba decidida por construcción (H3) sin gastar la corrida.
4. **Toda referencia lleva paper, página y párrafo** (pedido de Nicolás), y "SIN LOCALIZAR" antes que inventar.
5. **Un PDF "descargado" puede ser la página HTML** (Nature devolvió 210 KB con `<!DOCTYPE`): verificar magic bytes siempre.

**Propias del proyecto** (para `CLAUDE.md` en la próxima revisión, junto con A97 a A102 pendientes):

- **A103 (propuesta)**: un cúmulo agrupa componentes conexas del hot mask; un vecino marcado que toca al centro siempre entra. Toda pérdida de píxeles tibios frente a MIROVA está en la DETECCIÓN (umbrales, compuerta D22, fondo D25), no en el ensamblado.
- **A104 (propuesta)**: la máscara de nube de 260 K dejaba ciegas ~1 de cada 5 pasadas VIIRS 375 en invierno y así escondía la sobre-publicación: al apagarla (#535) la publicación en negativos limpios subió de 0,61 a 0,87 en los 11 Tier A. Una métrica con ventana que cruza #535 mezcla regímenes.
- **A105 (propuesta)**: el OSF v2.5 NO está supervisado a mano: clasificación automática DBSCAN más reglas por distancia (Coppola et al. 2026, Scientific Data, p. 7 y p. 11-12), y aplica umbrales VRP por sensor al construir el archivo (Tabla 1, p. 8: noche MODIS 0,1 MW, VIIRS 750 5 MW, VIIRS 375 0,01 MW; día 50 MW). Corrige la regla S139; toda comparación contra el OSF en VIIRS 750 está truncada a 5 MW de noche.
- **A106 (propuesta)**: MIROVA cambió sus TIF VIIRS 375 de EPSG:4326 a UTM nativo (375 m, EPSG:32719 o 32718) el 2026-09-14 (republicó la pasada de las 06:36 en el formato nuevo cerca de las 23:35 UTC). Sólo los TIF posteriores dan la celda exacta de MIROVA.

## d. Problemas abiertos e hipótesis

### CONFIRMADO (verificado con herramienta en S141)

- Cambio de régimen tras #535: 0,61 / 0,84 / 0,87 de publicación en negativos limpios V375, 11 Tier A (`regimen_535.json`); 75 de 160 no publicadas estaban ciegas antes, 0 después; piso VRP explica 5 de 297.
- El atraso del NRT está en la creación del evento `schedule` (mediana 56 min, 4,75 corridas de 12 por día); un `workflow_dispatch` arranca en 3 s.
- Probe v2: controles C1 a C4 = 1,0 en 38 pasadas; veredicto del script HETEROGENEO focal, INDETERMINADO nevado.
- Cita del artículo Scientific Data: "No additional quality control or manual screening was applied during this aggregation step" (p. 7); clasificación DBSCAN (p. 10 a 12); Tabla 1 con umbrales (p. 8). Leído en páginas renderizadas.
- Formato de los TIF MIROVA cambió el 2026-09-14 en los 11 volcanes (rasterio sobre 35 TIF del archivo).
- Nevados de Chillán 2026-09-14: 05:42 (zen 1°) MIROVA 0,09 MW contra nuestro 0,094; 06:18 y 06:36 MIROVA sin alerta y nosotros publicamos 0,043 y 0,072.

### SOSPECHA (no verificado)

- Que el NRT publicado de MIROVA aplique los umbrales de la Tabla 1 del archivo (el artículo sólo describe el archivo).
- Que el veredicto HETEROGENEO del probe v2 sea el fenómeno y no un artefacto: falta verificador limpio post corrida.
- Que el aporte estacional al escalón de #535 sea despreciable (el tramo entre merges tiene 64 pasadas).
- Que el TIF UTM de la pasada NdC 2026-09-14 06:36 (máximo 0,727) sea un dato distinto y no un artefacto de reproceso.
- Reconstrucción del VRP del 2026-09-15 06:18 desde el TIF: no concluyente (1 celda 0,030, 2 celdas 0,065, publicado 0,05).

## e. Cerrado en esta sesión, no rehacer

1. Decisiones 3 a 8 del bloque S141 (todas ejecutadas; ver tabla a).
2. **Probe v1**: INDETERMINADO y sus lecturas por estrato retiradas por el verificador. No reinterpretar sus números.
3. **Cron**: no subir la frecuencia ni sacar el NRT de `push-main` (S139 y S141).
4. **chrome-devtools-mcp**: evaluado, no aporta sobre el navegador de la app; no instalado.
5. **Explore Archive de MIROVA** = dashboard del mismo OSF 2000 a 2025; no trae NRT. MSI, OLI y Combined MIR sólo sirven PNG.
6. **Afirmación "Laiolo 2026 muestra que MIROVA filtra por distancia"**: es una serie de estudio, no el NRT (nota en D14).

## f. Prompt para la próxima sesión

```
Retomo VRP Chile en S142. Antes de creerle a nada, verifica el estado real:

  cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
  git fetch origin --prune && git pull --ff-only
  python -m pytest tests/ -q --no-header --tb=line -p no:cacheprovider | tail -1   # anotar el conteo real
  gh api repos/MendozaVolcanic/VRP-chile -i 2>/dev/null | grep -i "^date:"          # A86
  gh run list --workflow=nrt.yml --limit 3                                          # cadencia del cron

Lee en este orden, comprobando contra el codigo de hoy lo que afirme:
  1. tasks/BLOQUE_ARRANQUE_S142.md                          <- este archivo (decisiones §b)
  2. experiments/_s141_fase1_probe_v2/criterio_total.json   <- probe v2, SIN interpretar
  3. docs/superpowers/plans/2026-09-15-fase1-probe-vecinos-v2.md  <- criterio pre-registrado
  4. docs/S141_NDC_JUNIO_SEPTIEMBRE.md y experiments/_s141_ndc/mirova_pagina_20260915.json
  5. documentacion/Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.md (p. 7, 8, 10-12)

TRABAJO, en este orden:
  1. Probe v2: leer criterio_total.json contra el pre-registro y lanzar un verificador con contexto
     limpio sobre el veredicto antes de cualquier lectura. No proponer brazos de A/B sin eso.
  2. Nevados de Chillan: sumar MOUNTS (web http://www.mounts-project.com/timeseries/357070, con
     anomalia el 15-sep, y el proyecto local C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\MOUNTS:
     leer su CLAUDE.md y su salida publicada, no su data/ por ruta) y contar los pixeles de MIROVA con
     los TIF UTM de mirova-tif-archive (sólo los posteriores al 2026-09-14 06:36).
  3. Re-medir la linea base de sobre-publicacion de la Fase 1 sólo con el regimen posterior a #535.
  4. Aplicar A105 a la memoria y a los docs que usen "OSF supervisado"; decidir con Nicolas el piso VRP.
  5. Preguntar a Nicolas las decisiones §b pendientes (cron, estrato nevado, correo, token).

REGLAS DURAS:
  - Manda la PARIDAD POR SENSOR; la fidelidad literal decide sólo entre brazos que empatan.
  - Toda metrica con NEGATIVOS, por pasada y por noche, por volcan, con ventana y denominador; separar
    el regimen antes y despues de #535 (2026-08-28 23:00 UTC).
  - Instrumento nuevo: verificador limpio ANTES de correr y DESPUES de correr.
  - Formulas y tablas de papers: renderizar la pagina y mirarla. Citas con paper, pagina y parrafo.
  - Tocar pipeline/, store.py, nrt.yml o el perfil: tag defensivo + confirmacion de Nicolas (A45).
  - Pasos de CI con tee llevan set -o pipefail; mirar duracion y salida de cada job.
  - NADA de guiones largos ni medios. Espanol de Chile, formas de tu. Fenomeno fisico primero.

SI LA SESION NO ALCANZA: /cierre. Lo que quede a medias va commiteado con su README diciendo que falta.
```

---

## Histórico: bloque S141 (cierre de S140)

Se conserva íntegro en `tasks/BLOQUE_ARRANQUE_S141.md`. Lo que ese bloque daba por pendiente y S141
resolvió: decisiones 3 a 8 ejecutadas (re-etiquetado MODIS, UNDER_BAND_KNOWN, T8a, umbrales, T10,
remapeo de citas); las sospechas de T7, T8c (token legible: sí, vence 2026-10-03) y del upgrade de
`store.py` quedaron verificadas. Lo que S141 corrigió de su propia sesión: la primera corrida del probe
salió verde sin datos; las lecturas por estrato del probe v1 eran falsas; la corrección "los TIF de
MIROVA son UTM" era parcial (cambió el 2026-09-14); y la regla "OSF supervisado a mano" es falsa para
la v2.5.
