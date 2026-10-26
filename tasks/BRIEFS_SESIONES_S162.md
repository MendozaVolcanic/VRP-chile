# Briefs de las sesiones de relevo (S162, 2026-10-25)

Preparados por la coordinadora S162 el 2026-10-25 a pedido de Nicolás («Revisa las sesiones y retoma en la que sea
necesaria en nuevas sesiones»). No se abrieron porque la app sólo abre sesiones desde un mensaje escrito en el
computador (no desde el control remoto). Para abrirlas: pedirlo a la coordinadora desde el computador, o abrir una
sesión nueva en este repo con el prompt de abajo.

Estado de las hijas al 2026-10-25 ~01:00 UTC:
- `loop-instrumento`: fase 0 terminada (#902 a #905, CI verde, sin merge). No hace falta relevo.
- `loop-viirs375`: PD1 terminado (caja C13 en el cráter; silencio acotado bajo K); loop en pausa esperando la vía de
  proceso en `pipeline/` y #903/#905. Su rama `claude/s162-viirs375-c1b864` no estaba en el remoto: la subió la
  coordinadora (`c0215a97d`). No hace falta relevo todavía.
- `loop-modis`: cerró con /cierre; traspaso en el bloque «0. Cierre» de `tasks/LOOP_MODIS.md`
  (`claude/s162-modis-774bb0` `7824fd1fc`). **Relevo necesario: sesión 1 de abajo.**
- `loop-viirs750`: loop detenido a propósito desde las 19:30 UTC del 24; cola en `tasks/LOOP_VIIRS750.md`
  (`claude/s162-viirs750-f63ef4` `27973d13a`). Camino crítico del programa: el analizador de V750-A y la vía de proceso
  «código MIROVA» en `pipeline/`, de la que dependen V375-E y MOD-D. **Relevo necesario: sesión 2 de abajo.**

**Actualización 2026-10-25 ~02:15 UTC.** La coordinadora lanzó cinco subagentes que hacen parte de este trabajo, cada uno
con su rama en el remoto: A61 de MxD03 (`s162-a61-mxd03`), PR del veredicto de MxD03 (`s162-pr-veredicto-mxd03`),
analizador de V750-A (`s162-v750a-evaluador`), las 6 protegidas de Suomi NPP de VIIRS 375 (`s162-v375-protegidas-snpp`)
y la simulación del auto-audit del lunes. Cada relevo empieza leyendo esas ramas y no repite esas tareas: MODIS 2 parte
por el candado de MOD-D; VIIRS 750 2 parte por la vía de proceso en `pipeline/`.

## Sesión 1: Loop MODIS 2 (veredicto MxD03, A61 y candado MOD-D)

Worktree nuevo desde la rama `claude/s162-modis-774bb0`. Prompt: el bloque «f. Prompt para la próxima sesión» de
`tasks/LOOP_MODIS.md` de esa rama, más estas tres líneas:
- Corre esto como loop propio con la skill `loop` en modo dinámico, sobre `tasks/LOOP_MODIS.md`.
- Puedes abrir sub-sesiones con su propio worktree, avisando su id a la coordinadora.
- Push de tu rama después de cada commit; todo despacho de GitHub Actions se pide a la coordinadora.

## Sesión 2: Loop VIIRS 750 2 (analizador V750-A y procesador código MIROVA)

Worktree nuevo desde la rama `claude/s162-viirs750-f63ef4`. Prompt:

```text
Sesión de VIIRS 750 de VRP Chile (continúa la sesión hija S162 de VIIRS 750, cuyo loop quedó detenido a propósito).
Español de Chile con formas de tú, sin guiones largos, rutas absolutas, explicar como geólogo.

1. Verifica antes de creer: git fetch origin --prune; compara origin/claude/s162-viirs750-f63ef4 (27973d13a o posterior)
   y el tag s162-v750b-sellado (1af6c3cd8) con tasks/LOOP_VIIRS750.md. Lee CLAUDE.md del proyecto (A45, A89, A90, A92,
   A104, A110, A118), la memoria reference_codigo_mirova_osf.md, el programa
   docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md §3 y §7, tasks/LOOP_VIIRS750.md,
   experiments/_s162_v750a/PREREGISTRO_V750A.md (con el diagnóstico S-1 de la sigma de escena en §5) y
   experiments/_s162_v750c/INFORME.md.
2. Trabajo, en este orden:
   a. Analizador de V750-A (evaluar_v750a.py): reusar regla, etiquetas y controles de analizar_v750b.py; P2 contra K;
      M con el comparador y el placebo de evaluar_d25.py del tag s161-d25-lectura; el diagnóstico S-1. Pruebas que
      fallen contra un vacío, mutaciones atrapadas por aserción con control de caída, verificador limpio de otro modelo.
   b. Vía de proceso «código MIROVA» para VIIRS 750 en pipeline/, detrás de un flag apagado: remuestreo con la regla
      GEO (centros X0 ± 25.000 m, paso 750; experiments/_s159/geo/INFORME.md), detección del .m, fondo del código sin
      recorte, suma de los alertados, ROI configurable por volcán (la elige V750-B), sin modo de un píxel ni tope D9.
      TDD: la prueba de equivalencia de V750-A pasa de roja a verde contra el oráculo. Antes del primer edit en
      pipeline/, tag defensivo pre-s162-via-mirova sobre origin/main y aviso a la coordinadora. PR en borrador; no se
      mergea ni se enciende el flag sin el sí explícito de Nicolás (A45). Diseñarla para que V375-E la reutilice con la
      caja C13 en el cráter.
   c. El 2026-11-03: generar los objetivos de V750-B desde su tag y pedir el despacho a la coordinadora con los sha256.
3. Loop propio con la skill loop en modo dinámico sobre tasks/LOOP_VIIRS750.md; sub-sesiones permitidas con su propio
   worktree, avisando su id a la coordinadora.
4. Reglas duras: nunca despaches GitHub Actions (se pide a la coordinadora; si no responde, dejarlo anotado en la cola);
   sólo EARTHDATA_TOKEN (A71); git add por archivo y push tras cada commit; nunca git stash para probar; verificador
   limpio de otro modelo antes de aceptar un resultado; parada si C: o D: bajan de 3 GB. Si la sesión no alcanza: cola
   al día y /cierre.
```
