# Bloque de arranque S143

> Cierre de S142 (2026-09-15 12:44 a 2026-09-16 00:31 UTC, hora del servidor). `main` en
> `2d546f322`, verificado igual al remoto con `git ls-remote` antes de este commit. Sin PR abiertos,
> sin worktrees extra, los 4 stashes de S72 a S78 intactos. Suite local al cerrar: **1488 passed,
> 10 skipped, 2 xfailed** (los 6 skips nuevos son los tests de los brazos del A/B, que se activan
> solos cuando existan esos perfiles). Tag defensivo de la sesión: `pre-s142-flags-d22-d25`
> (`04c9d4dcf`). El cron NRT sigue corriendo: última corrida verde 20:55 UTC y otra en curso a las
> 23:58 al cerrar.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| Probe v2 (vecinos del foco, VIIRS 375) | **verificado, NO justifica A/B** | #676; `experiments/_s141_fase1_probe_v2/VERIFICADOR_POST_CORRIDA.md`; hipótesis resuelta como no confirmada |
| Línea base de sobre-publicación post #535 | **medida y corregida** | #676; `experiments/_s142_linea_base/linea_base_post535.json`: V375 **87,1 % de 295** por pasada y **100 % de 93** noches (antes 62,1 %) |
| Muestra nevada en otra ventana del OSF | **no viable**, decidido dejar INDETERMINADO | #678; `experiments/_s142_nevado_muestra/PROPUESTA.md`; los records empiezan el 2025-02-15 |
| Nevados de Chillán + MOUNTS + celdas de MIROVA | mergeado; conteo de celdas **INCONCLUSO** | #678, #679; `experiments/_s142_ndc/RESULTADOS.md` |
| Nevados de Chillán al día (serie, mapa, informe) | **regenerado al 15-sep 08:15 UTC** | #679; `experiments/_s141_ndc/ndc_serie_s141.png`, `ndc_mapa_s141.png`, `docs/S141_NDC_JUNIO_SEPTIEMBRE.md` §6 |
| Tablero de objetivos contra la definición de terminado | mergeado | #678; `experiments/_s142_objetivos/TABLERO.md` |
| Ventana del auto-audit sin cruzar #535 | mergeado (TDD) | #677; `ventana_falsas(today)`, no empieza antes del 2026-09-01 |
| Reglas A97 a A106 y enmienda de A39 | **en `CLAUDE.md`** | #679 |
| Flags D22 (compuerta) y D25 (fondo por vecinos) | **escritos, probados y APAGADOS** | #681; plan y verificador en #680; `VRP_PROFILE=mirova_equivalent` da `False`, `False`, `3` |
| A105 anotado (OSF v2.5 sin revisión manual) | mergeado en 7 documentos y el manuscrito | #676, #679 |
| Correo a Coppola ajustado | listo, **no enviado** | `docs/audit_s139/BORRADOR_CORREO_COPPOLA.md` |
| Cron externo del NRT | paso a paso escrito, **falta que Nicolás cree el token** | `docs/audit_s142/CRON_EXTERNO_PASO_A_PASO.md`; fila 31 de `REGISTRO_CREDENCIALES.md` |
| Mapa del workspace | ficha de VRP Chile pasada de 🔴 a 🟢 | `MAPA_WORKSPACE.md` (esa carpeta no está versionada) |

## b. Decisiones que espera Nicolás

| # | pregunta | recomendación |
|---|---|---|
| 1 | Token de Earthdata: **vence 2026-10-03 07:18 UTC** | **renovarlo esta semana**; sin él se detiene la ingesta térmica. Lo hace Nicolás (credencial) |
| 2 | Token fine-grained + trabajo en cron-job.org | crearlos siguiendo `docs/audit_s142/CRON_EXTERNO_PASO_A_PASO.md`; después yo verifico que dispara |
| 3 | Correo a Coppola | revisarlo y enviarlo desde su cuenta; contesta la conectiva, el piso NRT y el fondo |
| 4 | ¿Reabrir la banda focal de falsas publicaciones? | **no todavía**: MIROVA repite su alerta en otra pasada de la misma noche sólo el 56,9 % de 2.484 pares, pero nosotros estamos en 85 % y eso no cambia ningún A/B por ahora |
| 5 | Siguiente frente | **falsas publicaciones de VIIRS 375**: es la brecha más grande y el plan atribuye 66 % a D19 |

## c. Lo aprendido

**Reglas generales del workspace** (ya en memoria del agente):

1. **"0 checks" recién abierto un PR es SIN DATO, no verde.** Mergeé #676 con el CI en rojo por leerlo como ausencia de CI. Esperar el run con conclusión ([[feedback_s142_merge_sobre_ci_rojo]]).
2. **Un documento puede ser insumo de un test.** El mismo error: corrí la suite antes de editar `HYPOTHESIS_LOG.md`, que un test lee. Tras editar docs, `grep -rl <archivo> tests/` y volver a correr.
3. **Un golden de texto crudo con float64 mide la máquina, no el código.** El CI de Linux falló con los flags apagados por el último dígito. Redondear al serializar (quedó en **9** cifras; 12 no alcanzó) y usar la misma canonicalización en los dos lados; el defecto sobrevivía en tres lugares ([[feedback_s142_golden_mide_la_maquina]]).
4. **Un caso de referencia justifica investigar, no priorizar** (A94, reaplicada): el caso del Test 1 en el arnés era real, pero recién medir cuántas detecciones pasan por ahí (2.211 de 3.615) mostró que el control faltante era grave.

**Propias del proyecto**: A97 a A106 ya entraron a `CLAUDE.md` en #679, con la enmienda de A39.

## d. Problemas abiertos e hipótesis

### CONFIRMADO (verificado con herramienta en S142)

- Sobre-publicación V375 post #571: **87,1 % de 295** pasadas y **100 % de 93** noches; focal 84,5 % de 84, nevado 88,1 % de 211. La banda de terminado es 10 % y 15 %.
- Magnitud V375: mediana por pasada **0,83 de 104** hoy; en la línea base larga **0,706 de 1.264**, con sólo 25,1 % dentro de la banda. Peores: Lastarria 0,55 (177), Láscar 0,56 (268), Isluga 0,60 (263). Chaitén se pasa arriba (1,35).
- Detección: **0 noches con alerta perdidas** en los tres sensores en el régimen actual.
- MIROVA contra sí mismo (V375): repite alerta en otra pasada de la misma noche en **56,9 % de 2.484** pares; tras una noche negativa alerta en 27,8 % de las pasadas focales y 5,2 % de las nevadas.
- El camino del Test 1 produce **2.211 de 3.615** detecciones V375 desde el 1 de junio.
- Paper renderizado (sp426.5): Test 1 (visor 6) y Tests 2 y 3 (visor 7) **no tienen condición de temperatura**; la ec. 6 (visor 8) define el fondo como media aritmética de los píxeles que rodean al activo o al cúmulo, sin decir "no alertados" ni mencionar recorte.

### SOSPECHA (no verificado)

- Que el aporte estacional al escalón de #535 sea despreciable.
- Que contar celdas en los TIF UTM de MIROVA reproduzca su VRP: hoy el procedimiento calza en 1 de 6 alertas y no es específico (8 de 19 controles dan lo mismo que una alerta real).
- Que el NRT publicado de MIROVA aplique los umbrales de la Tabla 1 del archivo.

## e. Cerrado en esta sesión, no rehacer

1. **Probe v2**: veredicto reproducido bit a bit; no justifica ningún brazo de A/B. Un v3 necesita pre-registro nuevo (rutas separadas, contraste sólo sobre vecinos perdidos, vecinos por NTI, muestra nueva).
2. **Estrato nevado**: queda INDETERMINADO, sin backfill (decisión tomada).
3. **Muestra nevada de 2024**: imposible, los records empiezan el 2025-02-15.
4. **Ventana del auto-audit**: ya no cruza #535.
5. **A105**: anotado en todos los documentos que lo citaban; el OSF v2.5 no está supervisado a mano.

## f. Prompt para la próxima sesión

```
Retomo VRP Chile en S143. Antes de creerle a nada, verifica el estado real:

  cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
  git fetch origin --prune && git pull --ff-only
  python -m pytest tests/ -q --no-header --tb=line -p no:cacheprovider | tail -1   # base: 1488/10/2
  gh api repos/MendozaVolcanic/VRP-chile -i 2>/dev/null | grep -i "^date:"          # A86
  gh run list --workflow=nrt.yml --limit 3                                          # cadencia del cron
  VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_TESTS_23_NO_BT_GATE_VIIRS375, p.ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375)"   # los dos False

Lee en este orden, comprobando contra el codigo de hoy lo que afirme:
  1. tasks/BLOQUE_ARRANQUE_S143.md                                  <- este archivo (decisiones §b)
  2. docs/superpowers/plans/2026-09-15-flags-d22-d25.md y su _VERIFICADOR.md
  3. experiments/_s142_objetivos/TABLERO.md                          <- objetivos contra hoy
  4. experiments/_s142_linea_base/RESULTADOS.md                      <- linea base de un solo regimen

TRABAJO, en este orden:
  1. Preguntar a Nicolas las decisiones §b (token Earthdata vence el 3-oct, cron, correo).
  2. Tareas 7 a 10 del plan de los flags: perfiles de los brazos (control, literal y cuatro
     ablaciones, mas el brazo que apaga el recorte a cero), PRE-REGISTRO escrito ANTES de correr y
     verificador con contexto limpio sobre el pre-registro. Recien despues despachar el A/B.
  3. Medir el A/B contra la linea base del REGIMEN ACTUAL (87,1 % por pasada, 100 % por noche), no
     contra el 63,5 % viejo.
  4. Si sobra tiempo: contar celdas de MIROVA con una semana de TIF UTM (probe del conteo).

REGLAS DURAS:
  - Manda la PARIDAD POR SENSOR; la fidelidad literal decide solo entre brazos que empatan.
  - Toda metrica con NEGATIVOS, por pasada y por noche, por volcan, con ventana y denominador.
  - Instrumento nuevo: verificador limpio ANTES y DESPUES de correr.
  - Formulas de papers: renderizar la pagina y mirarla. Citas con paper, pagina y parrafo.
  - Tocar pipeline/, store.py, nrt.yml o el perfil: tag defensivo + confirmacion de Nicolas (A45).
  - No mergear con "0 checks": esperar el run con conclusion (A39 enmendada en S142).
  - Un golden con floats se escribe redondeado y se compara con la misma canonicalizacion.
  - NADA de guiones largos ni medios. Espanol de Chile, formas de tu. Fenomeno fisico primero.

SI LA SESION NO ALCANZA: /cierre. Lo que quede a medias va commiteado con su README diciendo que falta.
```

---

## Histórico: bloque S142 (cierre de S141)

Se conserva íntegro en `tasks/BLOQUE_ARRANQUE_S142.md`. Lo que ese bloque daba por pendiente y S142
resolvió: el probe v2 quedó verificado (no justifica A/B), el estrato nevado quedó decidido, la línea
base se midió sobre un solo régimen, A105 se aplicó y el cron quedó documentado. Lo que S142 corrigió
de sí misma: mergeó #676 con el CI en rojo, y el golden de los flags medía la máquina en vez del
código.
