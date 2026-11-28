# Bloque de arranque S205 (escrito por S204, 2026-11-28 ~07:50 UTC)

> El bloque anterior (S204, escrito por S203) queda como histórico en `tasks/BLOQUE_ARRANQUE_S204.md`. Detalle de S204
> en la bitácora `tasks/LOOP_OBJETIVOS.md` §6 (entrada S204, arriba) y en la nota viva
> `D:\vrp-trabajo\temporales\s204\s204_nota_viva.md`. S204 cerró por contexto (~550 mil tokens).
> **Estado fijado con trabajo en curso:** la suite completa de #1151 (`D:\vrp-trabajo\temporales\s204\pytest_lance_completo5.txt`,
> basetemp `bt_lance5`, worktree `D:\vrp-trabajo\worktrees\s204-lance2`) seguía corriendo; nadie la vigila ni mergea
> #1151 al terminar. Ninguna cadena de merge, tanda ni Codex quedó viva.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| `main` | ficha **v1.125** (#1145, #1147 a #1150 de S204) | `git show origin/main:docs/FICHA_SDA_VRP_CHILE.md` |
| #1145 NO CUMPLE NHI guardado | en main v1.121: `experiments/_s196_lab_piso/RESULTADO_NHI_S203.md`, `resultado_nhi_s203.json`, `unir_lab_p250.py`, `exceso_minimo_s204.py`; MEJ-5 en `docs/BEYOND_MIROVA_EXTENSIONS.md` §12 | merge 7a9c1c658 |
| #1148 corrección de la lectura NHI | en main v1.122: la «cobertura desigual 3,9 a 4,6 %» era casi entera MODIS de día de producción (R6FN-102); sin él 0 a 0,7 % y NO CUMPLE igual (Planchón-Peteroa p 0,015) | merge 50bb606f7 |
| #1149 tope del CI | en main v1.123: job `pytest` de `tests.yml` 20 a 30 min (12 jobs verdes 13,1 a 19,9 min) | merge 93d7915d5; `D:\vrp-trabajo\temporales\s204\duracion_pytest_ci.txt` |
| #1147 tiempo del respaldo LANCE | en main v1.124: presupuesto de red por proceso en dos bolsas (hoy y ayer 600 s, días anteriores 300 s), espejo colgado al final, nrt4 en `_NASA_HOSTS`. Verificador limpio: NO APRUEBA y luego APRUEBA; suite 5.068/0; 19/19 mutaciones. En producción desde 03:22 UTC del 28-nov; NRT 06:10: 116 recuperaciones, 0 presupuestos agotados, 0 Traceback | merge 115abf7c3; `experiments/_s204_lance_tiempo/` |
| #1150 ícono del cráter | en main v1.125: mira blanca sin relleno + ítem de leyenda (pedido de Nicolás); **verificado en Pages** (Chillán: 1 mira, 0 puntos `#ff5722`) | merge del 07:33 UTC |
| **#1151** residuales del respaldo | **ABIERTO**: R6C-108 (vacío de nrt4 ocultaba a nrt3 recuperado) y R6C-V201 (presupuesto agotado callado). Verificador limpio APRUEBA (I-1 declarado, I-2 dos pruebas nuevas); 24/24 mutaciones; **suite completa corriendo** al cierre | rama `s204-lance-residuales` (head 4159bad05), worktree `D:\vrp-trabajo\worktrees\s204-lance2`; fila en `D:\vrp-trabajo\temporales\s195\merge\fila_PEND_resid.txt` |
| **#1152** acta ronda 6 | **BORRADOR**, espera el sí de Nicolás; no mergear sin él | rama `s204-acta-r6`, worktree `D:\vrp-trabajo\worktrees\s204-acta` |
| Ronda 6 de Codex | terminada: frentes L y N (ciego, confrontación, verificador limpio) y cierre con verificador; registro 507 filas (46 de R6, 0 refutadas) | `D:\codex-vrp\_salida\ronda6\` (`RESUMEN_R6_PARA_NICOLAS.md`, `hallazgos_verificados.csv`); maquinaria `D:\vrp-trabajo\temporales\s204_r6\` |
| Copia de Codex | `D:\codex-vrp` en 115abf7c3 (v1.124) | `D:\codex-vrp\BASE.txt` |
| Issues | #1146 **nuevo** (guardia K MODIS: Chillán MODIS 2026-11-26 13:10 UTC, MIROVA 26,87 MW, producción sin record de la pasada; sin investigar), #1141 (sombra verde a las 21:53 del 27-nov; el monitor de ~09 UTC debería cerrarlo), #1106 (cierra con el audit del 30-nov), #943, #813 | `gh issue list` |
| Disco | C: 29 GB, D: 16 GB | `df -h` |
| Sin commitear en `loop/activo` | sólo lo ajeno de siempre: `experiments/_s140/`, `_s160_espacial/_censo_s159/` y `data/`, `experiments/_s176_codex/` (nunca tocar) | `git status --porcelain` |

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Acta de la ronda 6 (#1152) | aprobar / cambiar | Aprobar con las decisiones 2 y 3 |
| 2 | R6C-105 (gravedad 3, anterior al respaldo): CMR caído con 503 lentos pasa el paso de 50 min | (a) plazo total de red por proceso también para CMR (PR con plan, pruebas y verificador) / (b) aceptar con vigilancia (se pierde una corrida, la siguiente reprocesa) | **(a)**, sin urgencia |
| 3 | Residuales de gravedad 2 del respaldo (R6C-102, 103, 109) | aceptar / arreglar | Aceptar: no quitan nada de lo que trae CMR; revisar si un log muestra `LANCE_RESPALDO_SIN_RESPUESTA` por presupuesto en una caída real |
| 4 | Laboratorio NO CUMPLE: ¿segundo intento? | ninguno / pre-registro nuevo (primero arreglar el cargador de la vara, R6FN-102) / mirar Planchón-Peteroa aparte | Ninguno por ahora; PP como pregunta abierta del experimental |
| 5 | Heredadas | #813 (VIIRS de día), NODD (no), P0 parte 4, traza `nrt_reemplazado`, clave FIRMS, PAT en settings.json | las de los bloques S201 a S204 |

**Ya decidido en S204 (no volver a preguntar):** «Sí, lánzala» (ronda 6, ~23:35 UTC del 27-nov). Pedidos de Nicolás del
28-nov recibidos vía S203: ícono del cráter (hecho, #1150) y resumen por sensor (respondido en el chat de S204, con
números de `D:\vrp-trabajo\temporales\s204\salida_resumen_por_sensor.txt`).

**Preguntas de Nicolás de S204 sin respuesta explícita:** ninguna.

## c. Lo aprendido

- **REGLA GENERAL (A112, reincidencia):** nunca correr mutaciones ni editar código en un worktree donde corre una suite
  completa: S204 invalidó dos suites así (bt_lance2 y bt_lance4) y hubo que detenerlas y repetir.
- **REGLA GENERAL (S196, reincidencia):** nada de Python en heredoc con rutas de barras invertidas: `\v` y `\t` se
  comieron una ruta en la descripción de #1147; se arregló con Write.
- **REGLA GENERAL:** un archivo con CRLF no se muta con cadenas LF (0 coincidencias, el script falla); normalizar los
  saltos de la mutación al del archivo.
- **Proyecto:** el job `pytest` de `tests.yml` ya tarda ~20 min; se canceló a los 20 con 0 fallas. Tope en 30 desde #1149.
- **Proyecto:** el presupuesto de un respaldo que busca de lo viejo a lo nuevo tiene que proteger el día de hoy con una
  bolsa propia; con una sola bolsa, el corte cae justo en hoy (verificador de #1147, I-1).
- **Proyecto:** la vara NHI sellada (S194) carga MODIS de día de producción; su control de cobertura queda consumido por
  ese artefacto y se habría invalidado sola desde el 28-nov (R6FN-102, V201). Un segundo intento la arregla primero.
- **Proyecto:** cada Codex de cierre puede tardar ~3 h; las NRT siguen corriendo entretanto (revisarlas al volver).

## d. Problemas abiertos e hipótesis

- **CONFIRMADO:** R6C-105 abierto (verificador del cierre: 53,0 min con T=30 s; anterior a #1147).
- **CONFIRMADO:** #1147 funciona en producción (NRT 06:10 del 28-nov, `salida_medir_tiempo_0610.txt`).
- **SOSPECHA:** #1146 (Chillán MODIS 2026-11-26 13:10 UTC, 26,87 MW) puede ser una pasada perdida en la caída de CMR del
  26-nov que ya quedó fuera de la ventana del respaldo (sólo hoy y ayer); es diurna (10:10 hora de Chile). Sin investigar.
- **SOSPECHA:** el hueco de CMR del 27-nov sigue sin rellenarse (cada NRT recupera 116 pasadas de ese día por LANCE).
- **CONFIRMADO:** quedan 14 pasadas Aqua nocturnas del 25-nov que el laboratorio no tiene (R6FN-110); causa SIN DATO.

## e. Ya cerrado, no rehacer

- NO CUMPLE de la zona A: reproducido campo por campo por Codex y por dos verificadores; sin MODIS diurno sigue NO CUMPLE.
- Respaldo LANCE: no mete gránulos equivocados ni quita lo de CMR (frente L, 16 combinaciones de espejos verificadas).
- NOAA-21 05:54 de Láscar del 27-nov: era el gránulo vecino, sin record por borde; la pasada es la 05:48 (vía CMR).
- Escena inválida V750 Lastarria 2026-11-27 06:48: borde de barrido (cenit 69,5°), mismo tipo que las de antes.
- Ícono del cráter: hecho y publicado (#1150).

## f. Prompt para S205

```
Retomas VRP Chile como sesión dueña del loop (S205). Español de Chile, sin guiones largos, rutas absolutas.
Si te abrió otra sesión, mcp__ccd_session_mgmt__detach_session("self"). S204 cerró y no trabaja más.
Nicolás autorizó seguir sin preguntar cada paso, hasta 900 mil tokens por sesión (cierre preferido a los 550 mil).

1. Verifica antes de creer: git fetch --prune; ficha de main (esperado v1.125 o más); gh pr list; gh issue list;
   df de C: y D:. Lee tasks/BLOQUE_ARRANQUE_S205.md (rama loop/activo) y la entrada S204 de tasks/LOOP_OBJETIVOS.md §6;
   nota viva D:\vrp-trabajo\temporales\s204\s204_nota_viva.md.
2. Trabajo, en orden:
   a. #1151: lee la última línea de D:\vrp-trabajo\temporales\s204\pytest_lance_completo5.txt (suite completa del head
      4159bad05). Si 0 fallas: copia D:\vrp-trabajo\temporales\s195\merge\fila_PEND_resid.txt a fila_1151.txt y corre
      uno.sh 1151 s204-lance-residuales v1.126 <fecha UTC> "<resumen>" "#1151, S204; cierre ronda 6 (R6C-108, V201)".
      Si la suite no terminó o falló, repítela en el worktree quieto antes. Al mergear, quita el worktree s204-lance2.
   b. Lleva a Nicolás las decisiones 1 a 3 del bloque (acta #1152, R6C-105, residuales) con el resumen
      D:\codex-vrp\_salida\ronda6\RESUMEN_R6_PARA_NICOLAS.md. Con su sí: cabecera del acta con fecha y frase textual,
      merge con uno.sh. Si elige (a) en R6C-105: plan (writing-plans), pruebas primero, verificador limpio.
   c. #1146 (Chillán MODIS 2026-11-26 13:10 UTC, 26,87 MW sin record): diagnosticar (systematic-debugging) si es la
      caída de CMR del 26-nov fuera de la ventana del respaldo, una pasada diurna o otra cosa. Números sólo de scripts.
   d. Ver que #1141 se cerró con el monitor y que el audit del 30-nov cierra #1106.
3. Reglas duras: A45; merges con D:\vrp-trabajo\temporales\s195\merge\uno.sh en serie (fila_<N>.txt antes; versión
   siguiente a la de main; fecha UTC del merge; --match-head-commit); nada de git stash; git add por archivo; nunca
   experiments/_s176_codex/; temporales y worktrees en D:; números sólo de scripts; .md con newline=""; nada de python
   en heredoc con barras invertidas (Write o Edit); nunca mutar ni editar un worktree donde corre una suite (A112); un
   vigilante por corrida; nunca pedir ni recibir tokens por el chat; verificador limpio en todo PR propio que toque un
   evaluador o el pipeline; no agregar líneas a frontend/index.html (citas G8); git fetch antes de leer origin/...
4. Cierra con /cierre al llegar al umbral de contexto y deja el prompt de S206.
```
