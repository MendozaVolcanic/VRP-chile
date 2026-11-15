# Bloque de arranque S186 (cierre de S185, 2026-11-15 12:50 UTC)

S185 coordinó el loop desde la rama `loop/activo` como sesión dueña única, del 2026-11-14 20:03 al 2026-11-15 12:50 UTC.
Cerró por contexto (61 %). **La próxima sesión del loop es S186.** La bitácora completa de S185 está en
`tasks/LOOP_OBJETIVOS.md` §6, entradas «(S185)» del 2026-11-14 20:04 al 2026-11-15 12:47 UTC. El bloque anterior
(`tasks/BLOQUE_ARRANQUE_S185.md`) queda como histórico.

**El estado se fijó con trabajo en curso:**
- sesión «L1B: Tupungatito V750 y cola baja de Chillán V375» (`local_797fa5af`, worktree `D:\vrp-trabajo\wt_s185_l1b`,
  rama `claude/s185-l1b-probe`): sin `EARTHDATA_TOKEN` local, prepara un PR con un workflow de descarga
  (`probe-s185-l1b.yml`) por decisión de Nicolás («descárgalo desde un workflow por mientras»); el despacho espera su
  «mergea #N». Informe parcial en `D:\vrp-trabajo\temporales\s185_l1b\INFORME.md`;
- sesión «Paper y mazos al día (S182 a S185)» (`local_fe610939`, worktree `D:\vrp-trabajo\worktrees\s185-paper`):
  números y `revisiones/REVISION_S185.md` del paper privado (sin tocar la prosa) y láminas en
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\congreso geologico 2026\2_PRESENTACIONES\`;
- CI de #1016 y #1017 en curso (pendiente a las 12:48 UTC);
- la sombra de los 34 corre por cron a las 13:07 UTC del 11-15 (primera con #1007; cierra #1004 si sale verde).

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| b.2: la versión de la ficha se toma al mergear (#1009) | INTEGRADO | merge `0a1102d5d`, 2026-11-14 22:09 UTC |
| b.1: escenas inválidas fuera del banco y del auto-audit (#1010) | INTEGRADO, ficha v1.30 | merge `86a07971f`, 22:22 UTC; recall y veredicto iguales; negativos limpios 16.117 a 15.871 |
| b.3: la guardia K de VIIRS reproduce a K de producción | CERRADO | 505 de 505 pasadas, 0 distintas (investigador Sonnet, verificador Opus) |
| #1013: la ficha actualiza la cabecera en toda versión | ABIERTO, CI verde, CLEAN | espera «mergea #1013» |
| #1016: vigilancias, plazo por instante y ventana efectiva del nulo | ABIERTO, CI en curso | sin cambio de veredicto; 19 pruebas, 13 de 13 mutaciones; verificador Opus en dos vueltas |
| #1017: el auto-audit nombra a la vía como detector vigente | ABIERTO, CI en curso | sin cambio de veredicto; 133 pruebas; verificador Opus |
| Parche B: guard A119 para todo VIIRS | SIN PR, decisión de Nicolás | `D:\vrp-trabajo\temporales\s185_auditfix\B.patch`; Láscar V375 10-01 deja de ser flag y el veredicto pasa a VERDE |
| Plazo MODIS | 22 de 29 protegidas, VERDE | `guardia_modis_latest.json` 2026-11-15 02:07 UTC; informe de cierre listo y verificado: `D:\vrp-trabajo\temporales\s185_cierre_modis\informe_cierre_modis.py` |
| Plazos VIIRS 750 y 375 | 11 y 8 de 29, VERDE | `guardia_v750_latest.json`, `guardia_v375_latest.json` |
| Auditoría semanal del 11-16 (anticipada hoy) | 1 flag (Láscar V375 10-01, A119) y 4 aparte; recall MODIS 96,9, V375 98,5, V750 96,3 % | `D:\vrp-trabajo\temporales\s185_audit_pre\` y `_audit_verif\` |
| Programa por sensor §12.9 | ESCRITO en `loop/activo` | `c61af222a` y corrección `abb5f787b` (MOD-E ya hecho en S162, V375-F medido) |
| Fidelidad de la vía contra el `.m` | AUDITADA y VERIFICADA | `D:\vrp-trabajo\temporales\s185_fid_viirs\`, `_fid_modis\` y sus `_verif\` |
| Documentos contra producción | 35 contradicciones, verificadas | `D:\vrp-trabajo\temporales\s185_docs\`, `_docs_verif\`; tarjeta propuesta «Documentos al día con la vía» (task_875e6dfd) |
| Tablero: modal «Acerca de» con métricas de julio | CONFIRMADO, publicado hoy | `frontend/index.html` l. 542 a 553; arreglo pide tag y sí de Nicolás |
| Tanda 1 de los 34 (#1012) y Pages (#1014) | ABIERTOS (otra sesión) | revisión independiente de #1012 CONFIRMADA salvo Pages; #1014 lo arregla; aplicar sólo tras #1014 |
| #1011 (gráficos, otra sesión) | EN CONFLICTO por la ficha | revisión enviada a su sesión; pasa a v1.31 |
| Disco | C: 27 GB, D: 31 GB | `df -h` 12:48 UTC |

## b. Decisiones que espera el dueño

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Merges | «mergea #1013», «#1016», «#1017», «#1014» y luego «#1012» | Sí a los cinco, en ese orden para #1014 y #1012. #1013, #1016 y #1017 no cambian veredicto ni detección |
| 2 | Guard A119 para todo VIIRS (parche B) | PR / no | Sí, en PR aparte tras #1017: el mecanismo es el mismo en NOAA-20 y NOAA-21 (CONFIRMADO, n chico) y no esconde pérdidas |
| 3 | Regla de posición del punto caliente | formalizar «radiante» / probar otra | Formalizar «radiante», que ya corre: concuerda en clase con MIROVA 98,7 % (pico igual; cercano 93,6 %). La comparación con `Distancia_km` no sirve para elegir |
| 4 | Modal «Acerca de» del tablero con métricas de julio | arreglar / dejar | Arreglar (tag y sí): lo leen operadores |
| 5 | Documentos con K como producción | iniciar la tarjeta / no | Iniciarla: incluye la ficha SDA, documento público ante el CPLT |
| 6 | Divergencias de la vía sin documentar (5 km, 100 píxeles, 45 km, fila al norte, caja `sens` de Tupungatito, K1 y piso dNTI de V750 en MODIS) | documentar / medir / cambiar | Documentarlas ya en el catálogo y la ficha; medir costo antes de cambiar nada (A116) |
| 7 | `EARTHDATA_TOKEN` | rotar antes del 2026-11-27 | Hacerlo: si vence, se apaga el NRT |
| 8 | Color de #1011 (5 km fijo como MIROVA o regla de publicación) | MIROVA / publicación | Decide Nicolás; el PR declara la regla de publicación |

## c. Lo aprendido

- **Regla general del workspace:** el tope de agentes paralelos es una regla de costo y disco, no técnica. Con el plan
  por reiniciarse y agentes de solo lectura con tope de disco por carpeta, 11 a la vez funcionaron (C: bajó de 29 a 22
  GB y volvió). Cada resultado se aceptó sólo tras un verificador limpio de otro modelo. Memoria:
  `feedback_s185_lecciones.md`.
- **Regla general:** desde un turno que inició un agente o un mensaje de otra sesión, la app no deja iniciar
  sesiones: sólo proponerlas. Iniciarlas en el turno del usuario.
- **Regla general:** antes de escribir que una tarea está «sin empezar», buscar su identificador en `experiments/` y
  en la bitácora. S185 escribió «MOD-E sin empezar» y estaba hecho desde S162.
- **Regla general:** commitear antes de una prueba de mutación que restaura con `git checkout --`: S185 perdió un
  refactor sin commitear así y lo rehízo.
- **Del proyecto:** después de cada adopción, barrer los documentos contra el perfil (declarado contra efectivo): hoy
  35 contradicciones, varias de gravedad alta, incluida la ficha SDA.
- **Del proyecto:** `Distancia_km` de MIROVA se comporta como la distancia al píxel alertado más lejano desde el centro
  de su grilla (`docs/audit_s139/DISTANCIA_MIROVA_VS_TIF.md`): no sirve para elegir la regla de posición.
- **Del proyecto:** el NRT de LANCE ya no conserva gránulos de hace meses; una comparación NRT contra estándar hay que
  hacerla en el momento o guardar el diagnóstico del record NRT antes de que el almacén lo reemplace.
- **Del proyecto:** `EARTHDATA_TOKEN` existe sólo como secreto de GitHub; un análisis local de L1B necesita un
  workflow (PR y merge) o que Nicolás ponga el token en el entorno.

## d. Problemas abiertos e hipótesis

| Problema | Marca |
|---|---|
| Las 6 alertas de Tupungatito V750 que la vía calla (NTI 7 a 15 % bajo el umbral) | CONFIRMADO el hecho; la causa (NRT contra estándar o celda vecina) es SOSPECHA; NRT ya no recuperable |
| Cola baja de Chillán V375 ligada al lado este del barrido | CONFIRMADO el patrón con cortes redondos (p 0,013); la causa es SOSPECHA (se cierra con L1B) |
| Corte de 5 km al centro (VIIRS 375 y MODIS) que no viene de MIROVA | CONFIRMADO; su costo en alertas es SIN MEDIR (0 alertas en las 596 pasadas sólo de K) |
| MODIS de la vía con K1 −0,7 y piso 0,02 (números de V750) en vez de −0,8 y 0,01 | CONFIRMADO; efecto SIN MEDIR contra la Tabla 1 |
| Escalón de cenit sobre 50° de MIROVA (mitad del VRP en el 24 % de las filas) que la vía no reproduce | CONFIRMADO en la data de S158; vigencia en el NRT SOSPECHA |
| Costura de gránulo: 2 alertas débiles perdidas en 8,3 meses | CONFIRMADO; son del detector sobre la escena válida |
| Láscar MODIS subestima en 3 pasadas de 1 píxel | CONFIRMADO en los 3; no es sesgo general (mediana 0,996, n 79) |
| Tupungatito V750 2026-07-31 06:24, 1,36 MW sin MIROVA | SOSPECHA de artefacto (c) |
| Irruputuncu y Guallatiri (tanda 1 de los 34): positivos persistentes en 1 a 4 celdas | SOSPECHA de fuente débil persistente tipo fumarola; Irruputuncu 12,9 MW aislado del 10-09 |
| TIF de MIROVA congelados desde el 2026-09-22 | CONFIRMADO al 2026-11-15 |

## e. Lo que ya está cerrado y no hay que rehacer

- b.1, b.2 y b.3 (integrados o cerrados con verificador). La guardia K de VIIRS sirve para decidir reversión.
- Tupungatito V750 con la vía (8 de 14 contra 2 de 14 de K), V375-F (sin déficit), MOD-E (S162, reproducido),
  cobertura vía contra K, costura de gránulo, falsas publicaciones, regla de posición en producción, riesgo de la
  unión histórica del lunes (bajo) y estado de los TIF: medidos y verificados; no repetirlos.
- El informe de cierre del plazo MODIS está listo; el día que se cumpla sólo hay que correrlo.
- La auditoría del 11-16 ya está anticipada y clasificada: si da lo mismo, no hace falta reclasificar.

## f. Prompt para la próxima sesión

```text
Sesión S186 de VRP Chile, dueña única del loop (respondes sólo a Nicolás). Carpeta
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile, rama loop/activo. Hay otras
sesiones de Nicolás en este repo (L1B, paper y mazos, historia de los 34, gráficos): no toques
sus ramas ni sus worktrees.

1. Verifica antes de creer:
   - git fetch origin --prune; git status -sb; df -h /c /d. Con C: bajo 3 GB, para y avisa.
   - gh pr list --state open y gh issue list --state open. Avísale a Nicolás los issues de alerta
     abiertos antes de cualquier otra tarea.
   - ¿Qué pasó con #1013, #1014, #1016, #1017, #1012 y #1011 (mergeados, CI)? ¿La sombra de los 34
     de las 13:07 UTC del 11-15 salió verde (#1004)? Si falla, mira «Region:» en el log.
   - Auditoría semanal del 2026-11-16: compárala con la anticipada de S185
     (D:\vrp-trabajo\temporales\s185_audit_pre\INFORME.md). Si da lo mismo, no reclasifiques.
   - python -I D:\vrp-trabajo\temporales\s181_verif994\chequeo_post_nrt.py origin/main tiene que
     decir OK.
2. Lee CLAUDE.md, tasks/BLOQUE_ARRANQUE_S186.md y las entradas (S185) de tasks/LOOP_OBJETIVOS.md §6.
   Ojo: CLAUDE.md todavía dice que VIIRS es K; es falso desde el 2026-11-11 (ver §b.5).
3. Trabajo, en orden:
   a. Plazo MODIS: lee data/audit_continuous/guardia_modis_latest.json (duracion). Al llegar a 29,
      corre D:\vrp-trabajo\temporales\s185_cierre_modis\informe_cierre_modis.py (README al lado) y
      lleva el informe a Nicolás.
   b. Recoge lo de las sesiones L1B y paper y mazos (notas en esta sesión o list_sessions linked).
   c. Lleva a Nicolás las decisiones b.1 a b.8 del bloque con su recomendación.
   d. Lo que Nicolás apruebe: PR del parche B, tarjeta de documentos, arreglo del modal del tablero.
Reglas duras:
- Los merges a main, toda A45 nueva y aplicar a data/ son sólo de Nicolás, con «mergea #N».
- Merge commit con gh pr merge --merge --match-head-commit; nunca squash.
- Nada en pipeline/, data/ ni frontend/ sin tag y su sí.
- Sólo EARTHDATA_TOKEN (está sólo como secreto de GitHub).
- Verificador limpio de otro modelo antes de aceptar un resultado; effort high explícito.
- Temporales y worktrees en D:\vrp-trabajo; export MSYS_NO_PATHCONV=1 y rutas D:/ en git worktree.
- Tope de agentes: 5 y 2 procesos pesados, salvo que Nicolás lo levante; tope de 500 MB por agente.
- Quita tu worktree al mergear, revisando list_sessions justo antes. Worktrees de S185 vivos:
  D:\vrp-trabajo\wt_s185_vigil_pr (#1016), wt_s185_audit_a (#1017), wt_s185_doc2 (#1013).
- git add por archivo; nunca git stash; nada de experiments/_s176_codex/.
- Commitea antes de una prueba de mutación que restaure con git checkout.
- date -u antes de cada encabezado de bitácora.
- Texto con rutas de Windows o comillas invertidas: escríbelo con Write a un .py, nunca dentro de
  un heredoc de bash.
- Ficha SDA: la versión se toma al mergear (#1009); quien mergea une main y pone la siguiente.
- Español de Chile, sin guiones largos ni medios; rutas absolutas para Nicolás.
- Nombra la referencia de MIROVA leyendo el loader (tabla, OCR o ambos).
Si la sesión no alcanza: deja en la bitácora qué quedó a medias y cierra con /cierre al 50 % del
contexto; Nicolás autorizó que la sesión que cierra inicie la siguiente.
```
