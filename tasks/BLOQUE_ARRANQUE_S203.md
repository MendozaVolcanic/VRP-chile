# Bloque de arranque S203 (escrito por S202, 2026-11-27 ~04:00 UTC)

> El bloque anterior (S202, escrito por S201) queda como histórico en `tasks/BLOQUE_ARRANQUE_S202.md`. Detalle de S202
> en la bitácora `tasks/LOOP_OBJETIVOS.md` §6 (entrada S202, arriba) y en la nota viva
> `D:\vrp-trabajo\temporales\s202\s202_nota_viva.md`. S202 cerró por contexto (550 mil tokens).
> **Estado fijado SIN trabajo en vuelo:** las 10 tandas del barrido del piso terminaron en verde; la cadena del piso
> quedó detenida a propósito (no tiene nada más que despachar). Codex: nada corriendo. La sesión lateral
> «latencia-lance» (local_98a1b3b3-fd80-4a9a-b084-5a7de3c1e51c) terminó su informe y está inactiva.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| `main` | ficha **v1.116** (#1136 a #1139 de S202) | `git show origin/main:docs/FICHA_SDA_VRP_CHILE.md` |
| #1136 re-sello R5C-101 | en main v1.113: muestra común entre los nueve brazos y producción, tres frenos (decide su noche, tope 1 %, freno 3 si las publicaciones quitadas cambian la elección); sha256 `74d7648b...` | `experiments/_s196_lab_piso/PREREGISTRO.md` §5c; `tests/test_lab_piso_resello_s202.py` (18); 15 de 15 mutaciones; verificador limpio en dos pasadas `D:\vrp-trabajo\temporales\s202\verif_resello\VEREDICTO.md` |
| #1137 acta de cierre de la ronda 5 de Codex | en main v1.115, **aprobada por Nicolás** («Sí, apruebo», 2026-11-26 ~14:55 UTC) | `docs/ACTA_CIERRE_AUDITORIA_CODEX_RONDA5_2026-11-26.md` |
| #1138 cese de Terra (NASA, 2026-12-01) | en main v1.114: `scripts/ceses_esperados.json` + `frontend/cese_plataformas.js` (lista `CESES`, línea «sin Terra»); verificado en Pages | `tests/test_cese_terra_s202.py` (5) |
| #1139 manifiesto con t8 | en main v1.116 | `experiments/_s196_lab_piso/MANIFIESTO_TANDAS.json` |
| Barrido del piso | **10 de 10 tandas en verde.** t9 octubre run 45821160397 (success 19:49 UTC del 26), t10 1 a 23-nov run 45886487377 (success 23:47 UTC del 26, contada a mano). **Falta agregar t9 y t10 al manifiesto** | `D:\vrp-trabajo\temporales\s198\barrido\salida_contar_piso_t9.txt` y `_t10.txt` (11 volcanes cada uno) |
| Unión hasta septiembre | 24.512 records por brazo, 0 problemas | `D:\vrp-trabajo\temporales\s202\union_t8\` |
| Escenas de validez distinta (R5C-101), marzo a septiembre | 2: Llaima MODIS_TERRA 2026-05-30 02:55 (6 pisos) y Lastarria MODIS_TERRA 2026-09-19 02:10 (5 pisos); inverso 0 | `D:\vrp-trabajo\temporales\s202\union_t8\medir_invalidas_hasta_sept.txt` |
| Nevados de Chillán contra MIROVA (pregunta de Nicolás) | por pasada coincidimos (mediana 0,96 a 1,01 en 30 días); lo visible son VIIRS de día (hasta 93,6 MW) que no procesamos (#813) | `D:\vrp-trabajo\temporales\s202\ndc_magnitudes\comparar.py` |
| Atrasos del 26-nov | caída del catálogo CMR de NASA (indexador, aviso 3294, ~07:40 UTC); repuesto antes de las 03:42 UTC del 27; NOAA-20 05:30 ya publicada | `D:\vrp-trabajo\temporales\s202\latencia_lance\INFORME.md` |
| PR abiertos | sólo #913 (borrador viejo) | `gh pr list` |
| Issues | #1106 (cierra 2026-11-30), #943 (informativo SNPP), #813 (D-10, decisión de Nicolás) | `gh issue list` |
| Disco | C: 26 GB, D: 24 GB | `df -h` |
| Sin commitear en `loop/activo` | sólo lo de siempre, ajeno a S202: `experiments/_s140/`, `experiments/_s160_espacial/_censo_s159/` y `data/`, `experiments/_s176_codex/` (nunca tocar) | `git status --porcelain` |

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | #813 (D-10): ¿abrir VIIRS de día en la réplica? | abrir / no abrir / sólo en `experimental` | Sigue siendo suya. Dato nuevo: en Chillán las mayores potencias de MIROVA de noviembre son pasadas VIIRS diurnas (17:30 a 19:54 UTC); de día el MIR suma reflejo solar |
| 2 | Atrasos de NASA: ¿respaldo por listado de carpetas de LANCE cuando CMR falle, más aviso de «catálogo congelado»? | hacerlo / esperar | Hacerlo (mismos archivos, cero cambio científico, es lo que hace MIROVA según Coppola et al. 2019); toca `pipeline/fetch.py`: plan escrito y verificador limpio |
| 3 | NODD de NOAA en AWS para VIIRS (~30 min de latencia) | experimental tras A/B / no | No por ahora: es otro producto (SDR), divergencia sin medir |
| 4 | Heredadas (P0 parte 4, traza `nrt_reemplazado`, clave FIRMS, rotar el PAT de GitHub en `settings.json`) | | las de los bloques S201 y S202 |

**Ya decidido en S202 (no volver a preguntar):** «Agregar freno 3» (2026-11-26 ~13:00 UTC); «Sí, regístralo» (cese de Terra
a las 00:00 UTC del 1-dic); «Sí, apruebo» (acta de la ronda 5); «Sí, cierra» (cierre de S202).

**Preguntas de Nicolás de S202 sin respuesta explícita:** ninguna (magnitudes de Chillán, atrasos, investigación,
«cómo seguimos» y estado de Codex respondidas en texto).

## c. Lo aprendido

- **Proyecto:** la escena R5C-101 real de Llaima es válida con 9,685 MW en 0,00275 (falso positivo contra la tabla de
  MIROVA, según el verificador). Una exclusión común que sólo quita publicaciones sólo puede bajar el piso elegido; el
  freno 3 lo cierra (R202V-1). Con los tres frenos el re-sello da la elección del sello S200c o INVALIDO (R202V-5).
- **Proyecto:** el NRT busca en CMR y una caída del indexador de CMR devuelve «cero gránulos» sin error: ausencia
  silenciosa que el cortacircuito de `fetch.py` no ve. Chequeo rápido: `https://cmr.earthdata.nasa.gov/search/health`
  (503 con `indexer ok? false`).
- **Proyecto:** el NRT corre cada hora (workflow_dispatch a las :10 desde cron-job.org), no cada 2 h como dice el cron de
  `nrt.yml`; el informe de latencia se equivocó en eso.
- **REGLA GENERAL:** el contador de mutaciones tiene que exigir fallas por aserción (con `--tb=line`, «AssertionError» o
  «assert ...») y llevar un control de caída en ejecución que salga NO atrapado (R5FA-110). Una prueba que sólo verifica
  números redondos puede dejar sobrevivir una mutación de normalización (la hora «5:00» sin cero): darle algo que
  publicar.
- **REGLA GENERAL (ya existía, se rompió otra vez):** Python en heredoc con `\\n` rompió los saltos de un script; usar
  Write o Edit.
- **Proyecto:** la cadena del piso (procesos bash) muere si la PC se apaga y se cuelga si duerme; verificar con
  `gh run view` contra el registro antes de creer que sigue esperando.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO:** t9 y t10 no están en el manifiesto (el de main termina en t8).
- **CONFIRMADO:** 2 escenas de validez distinta de marzo a septiembre; octubre y noviembre SIN DATO hasta unir.
- **SOSPECHA:** la pasada Aqua del 26-nov 07:55 UTC no vuelve al catálogo NRT (CMR sólo lista la de 21:35) y llegará
  sólo con el producto estándar en unos días.
- **SOSPECHA:** el freno 3 dispara con Llaima en el barrido real (depende de dónde quede 0,00275 respecto del 30 %).
- **CONFIRMADO:** Terra deja de observar el 2026-12-01 (aviso de NASA del 17-nov, actualizado el 19-nov; sin hora).

## e. Ya cerrado, no rehacer

- Re-sello R5C-101 con tres frenos (#1136) y su verificador; acta de la ronda 5 aprobada (#1137); Terra registrado
  (#1138); t8 en el manifiesto (#1139).
- Magnitudes de Chillán: no es error de potencia (mediana por pasada 0,96 a 1,01 en 30 días; 2 de 63 pasadas VIIRS 375
  con MIROVA 1,5 veces, oblicuas, sin saturación, no seguidas).
- Atrasos del 26-nov: causa encontrada (CMR), no LANCE ni los satélites.
- R5C-106 en t8: la rama del run viene del intento bueno (commit 12:33 UTC, parcial borrada a las 11:21).

## f. Prompt para S203

```
Retomas VRP Chile como sesión dueña del loop (S203). Español de Chile, sin guiones largos, rutas absolutas.
Si te abrió otra sesión, mcp__ccd_session_mgmt__detach_session("self"). S202 cerró y no trabaja más.
Nicolás autorizó seguir sin preguntar cada paso, hasta 900 mil tokens por sesión (cierre preferido a los 550 mil).

1. Verifica antes de creer: git fetch --prune; ficha de main (esperado v1.116 o más); gh pr list; gh issue list;
   df de C: y D:. No hay cadena del piso corriendo (las 10 tandas terminaron). Lee tasks/BLOQUE_ARRANQUE_S203.md
   (rama loop/activo) y la entrada S202 de tasks/LOOP_OBJETIVOS.md §6.
2. Trabajo, en orden:
   a. Manifiesto con t9 (run 45821160397, 2026-10-01 a 10-31) y t10 (run 45886487377, 2026-11-01 a 11-23) en
      experiments/_s196_lab_piso/MANIFIESTO_TANDAS.json (PR con fila de ficha; mira el run de cada una: intentos y
      trabajos en success; comprueba que su rama s196-lab-piso/<run> venga del último intento).
   b. Con eso en main: unir_tandas.py con --fin-esperado 2026-11-23 a una carpeta en D:; medir escenas de validez
      distinta con D:\vrp-trabajo\temporales\s201\r5c101\medir_invalidas_por_brazo.py; y antes de calibrar, el
      chequeo externo del acta de la ronda 5 (R5C-103): cada carpeta trae regimen.perfil == _s196_lab_<brazo> del
      brazo que dice ser. Después evaluar.py calibrar con la unión (sin_zona, control, siete pisos, --dest en D:).
      Llevar el resultado a Nicolás SIN adoptar nada; explica como geólogo y di si saltó algún freno.
   c. Atrasos de NASA (decisión 2 del bloque): sólo si Nicolás dice que sí.
   d. Ronda 6 de Codex: proponerla a Nicolás sobre la corrida de calibrar, no lanzarla sola.
3. Reglas duras: A45; merges con D:\vrp-trabajo\temporales\s195\merge\uno.sh en serie (fila_<N>.txt antes; versión
   siguiente a la de main; fecha UTC del merge; --match-head-commit); nada de git stash; git add por archivo; nunca
   experiments/_s176_codex/; temporales y worktrees en D:; números sólo de scripts; .md con newline=""; nada de python
   en heredoc con barras invertidas (Write o Edit); un vigilante por corrida; nunca pedir ni recibir tokens por el chat;
   verificador limpio en todo PR propio que toque un evaluador o el pipeline; no agregar líneas al modal de
   frontend/index.html (citas G8).
4. Cierra con /cierre al llegar al umbral de contexto y deja el prompt de S204.
```
