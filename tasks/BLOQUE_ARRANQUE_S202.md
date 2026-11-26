# Bloque de arranque S202 (escrito por S201, 2026-11-26 ~10:45 UTC)

> El bloque anterior (S201, escrito por S200) queda como histórico en `tasks/BLOQUE_ARRANQUE_S201.md`. Detalle de S201
> en la bitácora `tasks/LOOP_OBJETIVOS.md` §6 (entrada S201, arriba) y en la nota viva
> `D:\vrp-trabajo\temporales\s201\s201_nota_viva.md`. S201 cerró por contexto (550 mil tokens).
> **Estado fijado CON TRABAJO EN VUELO:** la cadena del piso `D:/vrp-trabajo/temporales/s199/cadena_piso_s199c.sh`
> (procesos 15346 y 46432) sigue viva con la tanda t8 (septiembre, run 45743633871), que tenía 8 trabajos rojos de
> descarga (Copahue y Tupungatito) y un trabajo en curso a las 10:37 UTC; la cadena relanza con espera creciente y
> después despacha t9 (octubre) y t10 (1 a 23 de noviembre). Registro: `D:\vrp-trabajo\temporales\s198\barrido\cadena.log`.
> Son procesos de bash de una sesión vieja: si la app se reinicia, mueren. Codex: nada corriendo.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| `main` | ficha **v1.112** (#1133, #1134, #1135 de S201) | `git show origin/main:docs/FICHA_SDA_VRP_CHILE.md` |
| #1133 unión estricta de las tandas del piso | en main v1.110; verificador limpio en dos pasadas («mergear») | `experiments/_s196_lab_piso/unir_tandas.py`, `D:\vrp-trabajo\temporales\s201\verif_1133\` |
| #1134 declaraciones públicas (frente E) | en main v1.111; verificado en navegador | PR #1134 |
| #1135 manifiesto con t7 y rescate de t2 | en main v1.112 | `experiments/_s196_lab_piso/MANIFIESTO_TANDAS.json` |
| Codex ronda 5 | **entregada y verificada**: A, C+D, B, E, cierre; 461 filas; ninguna g3+ tras verificar | `D:\codex-vrp\_salida\ronda5\RESUMEN_R5_PARA_NICOLAS.md` |
| Re-sello R5C-101 | **APROBADO por Nicolás, SIN HACER** (primera tarea de S202) | §b y §f |
| Acta de cierre de la ronda 5 | sin escribir (después del re-sello) | |
| Barrido del piso | marzo a agosto cerrados y unidos (21.005 records por brazo, 0 problemas); t8 en curso | `D:\vrp-trabajo\temporales\s201\union_piso\informe_union_hasta_agosto.json` |
| Tupungatito, línea horizontal | respondido: fila 55 de la grilla VIIRS 375 de MIROVA, no artefacto | `D:\vrp-trabajo\temporales\s201\tupungatito\` |
| Issues | #1124 y #1125 **cerrados** (nrt-monitor 08:45 UTC); #1106 cierra 2026-11-30 | `gh issue list` |
| Disco | C: 16 GB (bajó de 30 entre 03:00 y 10:30 UTC por algo ajeno al loop; pagefile 27,6 GB), D: 27 GB | `df -h` |

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Acta de cierre de la ronda 5 (después del re-sello) | aprobar / pedir cambios | Aprobar: ronda terminable sin repetir frentes (verificador del cierre) |
| 2 | Arreglos menores verificados g2 de la ronda 5 (R5FB-101 historia de los 32 fuera del tablero; R5FCD-101 pareo a 120 s; R5FB-105 CSV sin motivo de escena vacía; R5C-V201 camino inverso VIIRS 375) | PR por cada uno / registrar como seguimiento | Registrar en el acta; R5FB-101 como tarea propia si se van a publicar los 34 |
| 3 | Heredadas del bloque S201 §b (P0 parte 4, traza `nrt_reemplazado`, clave FIRMS, rotar el PAT de GitHub en `settings.json`) | | las del bloque S201 |

**Ya decidido en S201 (no volver a preguntar):** rescate de t2 de marzo («Sí, acepta el rescate», 2026-11-26 ~00:50
UTC); arreglo de R5C-101 con la opción (a) («Sí, re-séllalo así», ~03:50 UTC), respuesta a «¿Re-sello el evaluador
excluyendo de todos los brazos la escena inválida, con frenos?».

**Preguntas de Nicolás de S201 sin respuesta explícita:** ninguna (Tupungatito, «cómo vamos», espacio y auditoría
de Codex respondidas en texto).

## c. Lo aprendido

- **REGLA GENERAL (Codex):** en el sandbox de Codex, `Remove-Item` de PowerShell falla con «Acceso denegado» aunque la
  carpeta sea escribible; un pase ciego lo leyó como carpeta negada y no escribió nada (fcda, 21:07 UTC). Los encargos
  deben decir que la prueba de escritura y borrado se hace con Python (`Path.write_text`, `Path.unlink`).
- **REGLA GENERAL (Codex):** tras un «You've hit your usage limit», `cupo.py` sigue mostrando el último `rate_limits`
  registrado (75 %): la cadena relanzaría y chocaría de nuevo. Esperar el `resets_at` explícito.
- **Proyecto:** la recolección del workflow del piso publica en la rama los datos parciales de trabajos caídos
  (Isluga de t2: 8 records en vez de 271). Por eso `unir_tandas.py` exige trabajos en success, tantos como trozos, y
  trozos no vacíos. La API REST de trabajos con `per_page=100` y `gh run view --json jobs` dan 500/502 en runs con
  varios intentos; con `per_page=50` responde.
- **Proyecto:** el conteo automático de una tanda (`contar_brazos_piso.py`) puede salir vacío («volcanes []») si el
  `git fetch` de la rama falla («Connection reset»); la cadena registra rc=0 igual. Mirar que no diga `volcanes []`.
- **Proyecto:** agregar líneas a `frontend/index.html` corre las citas `archivo:línea` del guard G8
  (`isValidDetection`); cambios de texto en el modal, en la misma línea.
- **REGLA GENERAL (ya existía, se rompió):** Python dentro de un heredoc con barras invertidas rompió una ruta del
  cuerpo de un PR (`\v`, `\t`). Escribir el script con la herramienta de archivos.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO:** R5C-101: con el detector real, bajar el piso puede volver «no medida» (`fondo_no_estimado`) una
  escena MODIS sólo en los pisos bajos; ningún control de `calibrar` lo ve. Frecuencia real marzo a agosto: 1 de
  21.005 (Llaima MODIS_TERRA 2026-05-30 02:55), inverso 0 (`D:\vrp-trabajo\temporales\s201\r5c101\medir_invalidas_salida.txt`).
- **CONFIRMADO (por el verificador del cierre, no por mí):** esa escena no mueve cuentas que decidan (la noche tiene
  otras 7 negativas limpias, 4 VIIRS; 15 de 146 noches en todos los brazos).
- **SOSPECHA:** t8 termina verde tras los relanzamientos (8 rojos de descarga a las 10:37 UTC).
- **SIN DATO:** frecuencia de R5C-101 en septiembre a noviembre (medir con el mismo script cuando estén las tandas).
- **SOSPECHA:** la caída de C: de 30 a 16 GB entre 03:00 y 10:30 UTC no es del loop (pagefile igual, 27,6 GB).

## e. Ya cerrado, no rehacer

- Ronda 5 de Codex: cinco piezas entregadas y verificadas; no repetir frentes. Registro 461 filas.
- Unión de tandas: hecha y verificada (#1133); marzo usa t1, t2 (5 volcanes) y t2c; Cordón Caulle de marzo sólo de t1
  (en t2 y t2c idéntico salvo `codigo_sha`: 6.300 conflictos si se unen los tres).
- Rescate de t2: decidido por Nicolás. Arreglo de R5C-101: decidido (opción a).
- Tupungatito: fila de la grilla, no artefacto (historia completa: bloque 2 × 2 en el cráter; vecinos verticales 778,
  horizontales 572).
- #1106: diagnosticado en S197 (Chaitén, borde doble), cierra el 30-nov. #1124 y #1125: cerrados.
- Declaraciones públicas del frente E: corregidas (#1134).

## f. Prompt para S202

```
Retomas VRP Chile como sesión dueña del loop (S202). Español de Chile, sin guiones largos, rutas absolutas.
Si te abrió otra sesión, mcp__ccd_session_mgmt__detach_session("self"). S201 cerró y no trabaja más.
Nicolás autorizó seguir sin preguntar cada paso, hasta 900 mil tokens por sesión.

1. Verifica antes de creer: git fetch --prune; ficha de main (esperado v1.112 o más); gh pr list; gh issue list;
   df de C: y D:. Cadena del piso: ps -ef | grep cadena_piso; final de D:\vrp-trabajo\temporales\s198\barrido\cadena.log
   (t8 septiembre run 45743633871 tenía 8 rojos de descarga; después t9 y t10). Si la cadena murió, relanza desde la
   tanda en curso copiando D:\vrp-trabajo\temporales\s199\cadena_piso_s199c.sh. Tras cada tanda: que el conteo no diga
   «volcanes []» (fetch fallido).
2. Lee tasks/BLOQUE_ARRANQUE_S202.md (rama loop/activo), la entrada S201 de tasks/LOOP_OBJETIVOS.md §6 y
   D:\codex-vrp\_salida\ronda5\RESUMEN_R5_PARA_NICOLAS.md (sección «Cierre en una pantalla»).
3. Trabajo, en orden:
   a. RE-SELLO R5C-101, aprobado por Nicolás («Sí, re-séllalo así», 2026-11-26): en experiments/_s196_lab_piso/evaluar.py
      calibrar, antes de contar: toda escena (volcán, sensor, datetime_utc) inválida (diag_codigo_mirova.motivo_vacio,
      la misma regla de scripts/banco_paridad.py::es_escena_invalida) en ALGUNO de los nueve brazos se excluye de los
      nueve brazos Y de producción, y la salida la declara y la cuenta. Dos frenos sellados que dan INVALIDO: (1) alguna
      escena excluida decide su noche (era la única negativa limpia o la única alerta de MIROVA de esa noche en alguna
      unidad; leer cómo cuenta noches E.tasas_barrido del S194); (2) las excluidas pasan del 1 % de las noches negativas.
      Detalle y medición del verificador: D:\codex-vrp\_salida\ronda5\cierre_verificacion\VEREDICTO.md (R5C-101, R5C-V201,
      R5C-V203: la exclusión tiene que tocar también producción o control_tasas da INVALIDO) y
      D:\codex-vrp\_salida\ronda5\cierre\PROPUESTA_CIERRE.md. PREREGISTRO.md §5c con la decisión literal y el sha256
      nuevo (la prueba tests/test_lab_piso_preregistro_s196.py compara el sello); pruebas en
      tests/test_lab_piso_resello_s200.py o un archivo nuevo (caso Llaima real, caso sintético de Codex, camino inverso
      VIIRS 375, frenos), mutaciones con control. Verificador Claude de contexto limpio antes de mergear. TODO antes de
      correr calibrar sobre el barrido. A45 no aplica (no es pipeline/), pero es un evaluador sellado: verificador sí.
   b. Acta de cierre de la ronda 5 (como docs/ACTA_CIERRE_AUDITORIA_CODEX_RONDA4_2026-11-25.md): estado de cada g2+,
      seguimientos con responsable y disparador, el re-sello; PR y llevar a Nicolás.
   c. Manifiesto: agregar t8, t9 y t10 a experiments/_s196_lab_piso/MANIFIESTO_TANDAS.json cuando cada run termine verde
      (PR con fila de ficha). Al tener las 10 tandas y el re-sello en main: unir_tandas.py con --fin-esperado 2026-11-23,
      medir_invalidas_por_brazo.py (D:\vrp-trabajo\temporales\s201\r5c101\) y evaluar.py calibrar; llevar el resultado a
      Nicolás sin adoptar nada.
   d. Plan por sensor y experimental: nada sin decisión de Nicolás.
4. Reglas duras: A45; merges con D:\vrp-trabajo\temporales\s195\merge\uno.sh en serie (fila_<N>.txt antes; versión
   siguiente a la de main; fecha UTC del merge; --match-head-commit); nada de git stash; git add por archivo; nunca
   experiments/_s176_codex/; temporales y worktrees en D:; números sólo de scripts; .md con newline=""; nada de python
   en heredoc con barras invertidas (Write o Edit); un vigilante por corrida; nunca pedir ni recibir tokens por el chat;
   verificador limpio en todo PR propio que toque un evaluador o el pipeline; árboles con enlaces de directorio se
   limpian con cmd /c rmdir, nunca rm -rf; en encargos a Codex, borrar con Python, no con Remove-Item; no agregar líneas
   al modal de index.html (citas G8).
5. Cierra con /cierre al llegar al umbral de contexto (550 mil; Nicolás autorizó hasta 900 mil) y deja el prompt de S203.
```
