# Bloque de arranque S159 (cierre de S158: «retomar» + loop + auditoría S158 + ola 1 de S159, 2026-10-21)

Escrito el 2026-10-21 a las 19:16 UTC (hora del servidor) sobre `loop/activo`; `main` en `5b908fc1f` (commits
automáticos encima de lo mergeado en S158). **Nada de esta sesión quedó en vuelo**: los siete agentes de la ola 1
terminaron y están commiteados; el A/B de D25 terminó (V1, V2a y V2b en verde); la sesión de la segunda ronda está
terminada. Lo único corriendo al cerrar es el cron «Experimental diario» (rutina, no de esta sesión). Los tres procesos
`python.exe` vivos en la máquina (`run_ciclo.py`, `registro.py`, `control_positivo.py`) no son de este proyecto.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| Reemplazo del histórico por K | **HECHO**: 68.072 de 68.072 records con K, R8 en el sitio publicado | #883 y #884 mergeados; tag `pre-s158-reemplazo-k`; commits `1bea8c35e`, `3251bcb5b` en `loop/activo` |
| Relleno de pasadas faltantes | **HECHO** 10 de 10 | `5f4ab1257` |
| Merges de la tabla b de S158 | **HECHO**: #878, #869, #879, #881, #882 (#876 cerrado); #864 respondido | `ad1a1e358`, `dbbf768fc`, `de5607da0` |
| A/B de D25 (V1, V2a, V2b) | **TERMINADO, VEREDICTO SIN LEER** (a propósito, ver d) | V1 con cobertura pareja de 4.610 por brazo (`27b925e1c`); V2a run 39575542584 y V2b run 39612909810, los dos `success` |
| Sesiones paralelas de S158 | **borradores abiertos** | #885 (código de MIROVA, oráculo, diseño D17, auditoría R1), #886 (Tupungatito V375), #887 (V750 que K no publica) |
| Auditoría S158, segunda ronda | **HECHA**, borrador; ningún hallazgo refutado por sus verificadores | #888, `docs/AUDIT_S158_R2.md` (rama `claude/s158-audit-r2-0eeee2`, `5280b49a9`) |
| Bloque R2 en el loop | **incorporado** | `tasks/LOOP_OBJETIVOS.md` §4 «Bloque S158 R2 y plan S159» (`acfedb84c`) |
| Plan S159 | **aprobado por Nicolás**; ola 1 COMPLETA, olas 2 y 3 pendientes | `docs/superpowers/specs/2026-10-21-pruebas-post-auditoria-s158-design.md` en `s159-pruebas` |
| Ola 1: P1, P2, P3, GEO, O1, COB | **commiteados** en `s159-pruebas` (`dc8b51832`, subida) | `experiments/_s159/<frente>/INFORME.md`; resumen en la bitácora del loop (`1c53d4365`) |
| Ola 1: IA (instrumentos) | **PR #889 listo, CI verde sobre `d0968e389`, merge BLOQUEADO** por el clasificador de permisos: lo mergea Nicolás | tag `pre-s159-instrumentos`; suite local 2.359 pasan, 0 fallas |
| Ola 1: IA, pieza I2 (evaluador de D25) | **PR #890 borrador**, requiere adenda | rama `s159-evaluador-d25` (`1438c8fff`); 10 pruebas pasan |
| Lista «mejor que MIROVA» | **creada**, viva | `docs/BEYOND_MIROVA_EXTENSIONS.md` §12 en `s159-pruebas` (`5607101dc`) |
| Octave 11.3 | **instalado** (`pkg load image` trae lo que el `.m` necesita) | `C:\Users\nmend\AppData\Local\Programs\GNU Octave\Octave-11.3.0\mingw64\bin\octave-cli.exe` |
| Worktrees | `C:\vrp-trabajo\s159-pruebas` (rama `s159-pruebas`) y `C:\vrp-trabajo\s159-instrumentos` (en `s159-instrumentos`) | C: con ~34 GB libres al lanzar la ola 1 |

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Mergear #889 (cobertura sin falso «completa», pareo único, prueba del tope); el clasificador me bloqueó el merge | mergearlo tú desde GitHub («Ready for review» y «Squash and merge») · darme permiso | **mergearlo tú**: CI verde, toca el NRT sólo en lo que informa, el código de salida no cambia |
| 2 | #890: el placebo de 1,2 veces da MEJORA con los pares reales de K, así que D25 sale INVÁLIDO haga lo que haga | (a) rediseñar la métrica M · (b) usar el placebo como comparador, no como compuerta · (c) quitarlo | **(b)**, por adenda sellada; es la única que conserva el control sin inutilizar el A/B |
| 3 | D25 terminó y le faltan días que CMR no sirve (17 al 20 de octubre, y 13-oct parcial) | evaluar sin esos días, declarados · repetir en otra ventana | **evaluar sin esos días, declarados**, y recién después de resolver 1 y 2; el brazo con el fondo del código va al pre-registro nuevo (R2.3), no a D25 |
| 4 | Correr el paquete O2 en MATLAB Online (15 min, tu cuenta) | sí · no | **sí**: es lo único que fija el VRP de las alertas de un píxel, que varía hasta 1,82 veces según la triangulación |
| 5 | Páginas renderizadas de papers con copyright que ya están en `main` (S146 frente C y F, S158 f2, f4, v2, v3, R2 a113 y m2) | dejarlas · borrarlas del árbol con un PR (quedan en la historia) · reescribir `main` | **borrarlas del árbol con un PR** y que el `.gitignore` de cada carpeta de auditoría las excluya; reescribir `main` es más riesgo que beneficio |
| 6 | Arreglo del tope de cordura de `pipeline/store.py:551-557` (R2-7) | sí con tag · esperar | **sí con tag `pre-s159-tope-cordura`**: hoy no toca ningún record, pero es el escenario de la erupción más grande; el diff está en `experiments/_s159/instrumentos/NOTAS.md` |
| 7 | Pasadas OSF 2025 anteriores a nuestra serie (357, 34 de 1 MW o más) | recortar toda evaluación al 2025-02-15 · ejecutar la ola P4 del backfill | **recortar**; P4 sólo si alguna pregunta necesita enero y febrero de 2025 |
| 8 | Mergear los borradores de investigación #885 a #888 (`experiments/` y `docs/`; #888 trae marcas A113 en CLAUDE.md y MISSION.md) | sí · revisar antes | **sí**, después de tu revisión visual del §9 de `docs/AUDIT_S158_R2.md` |
| 9 | Heredadas de S158 sin cambio: λ de B22 junto con el reproceso que traiga D25; #813 (D-10) postergado; PAT y aviso a OVDAS | | de Nicolás |

## c. Lo aprendido

Reglas generales del workspace (propuestas para `CLAUDE.md` global o memoria; aquí quedan escritas):
- **Un port escrito leyendo el mismo texto que otro puede compartir su error de lectura; la vara es el intérprete
  original.** Dos oráculos en Python coincidían entre sí y nadie los había corrido contra el `.m`. Octave lo hizo en
  una hora y confirmó la detección en 791 escenas, con cuatro mutaciones de control que cambiaban lo mismo en los dos.
  Si existe un intérprete libre del lenguaje original, se usa antes de confiar en un port.
- **Las páginas renderizadas de papers no van a un repo público.** La regla A95 obliga a renderizar para citar; el
  render es evidencia local, no entregable. Cada carpeta de auditoría lleva un `.gitignore` con `*/png/`, `*/paginas/`,
  `*/render/` y `*/descargas/`.
- **`git diff origin/main --stat` sobre una rama vieja mezcla el avance de `main` con los cambios de la rama**: mostró
  14.000 líneas de `data/` «borradas» que eran commits del NRT. Para ver sólo la rama: `git diff origin/main...HEAD`.
- **El clasificador de permisos bloquea el merge a `main` aunque el usuario lo haya aprobado en la conversación**: se
  pide al usuario que mergee o que agregue el permiso; no se busca otra vía.

Del proyecto (candidatas a regla A del `CLAUDE.md` del repo en un PR que toque ese archivo, A113):
- **La grilla de MIROVA es una sola regla** para los tres sensores: centros en `X0 - 25000 : paso : X0 + 25000`, de
  sur a norte; la de 750 m está corrida -187,5 m en x e y respecto de la de 375 m (GEO). Corrige a A106: sí hay TIF UTM
  nativos de VIIRS 750 y MODIS el 14 y 15 de septiembre.
- **Con un solo píxel alertado, el VRP del código de MIROVA depende de la triangulación de `fillmissing2`** (hasta 1,82
  veces): ningún port es vara del VRP en esos casos (O1).
- **Ningún paper describe la detección de MIROVA en VIIRS 375** (P2): «para VIIRS 375 manda el paper» no tiene paper.
- **Toda evaluación contra el OSF 2025 empieza el 2025-02-15** (COB): antes no hay serie nuestra.

## d. Problemas abiertos e hipótesis

| problema | estado |
|---|---|
| El fondo del VRP con recorte y el `single_pixel_mode` dejan cumbres en 0 MW y bajan la magnitud | **CONFIRMADO** en VIIRS 750 sobre 10 gránulos chilenos y en el corpus (595 de 2.359 cúmulos de cumbre, 64 con alerta de MIROVA de la misma pasada, 0 protegidas) |
| Esos ceros salen del segundo pase en los tres sensores, así que fondo y compuerta de 3 K se miden juntos | **CONFIRMADO** (VA-1) |
| La prueba con gránulos de R2 usó la grilla de 750 m equivocada; las alertas débiles de Láscar 09-26 y Chaitén 10-06 hay que releerlas | **CONFIRMADO** el error de grilla; lo que pasa con las dos alertas: **SIN DATO** hasta la ola 2 |
| La geolocalización MODIS se corre hacia el nadir (hasta 3,4 km de mediana a 40-55° del lado malo) y ±2 líneas en los extremos del gránulo | **CONFIRMADO** como aritmética de índices; el efecto del bow tie, **SOSPECHA** |
| MIROVA usa MOD03 con corrección de terreno | **CONFIRMADO** en el texto (Coppola 2026 Sci Data p. 4) |
| El escalón del OSF sobre 50,0° de cenit (24 % de filas V750 no cumplen la fórmula del código) | causa **SIN DATO**; zonas de agregación **REFUTADAS** por dos agentes; subconjunto de píxeles **SOSPECHA** |
| La caja de Cordón Caulle de MIROVA cubre el foco de 2011 | **SOSPECHA** |
| El centro de la grilla de MIROVA en Tupungatito (a 2,8 km de nuestra coordenada) explica su alerta a 5 km | **SOSPECHA** (MEJ-4) |
| CMR no sirve Chile del 17 al 20 de octubre | **CONFIRMADO** hoy; si vuelve: vigilar en cada vuelta (R2.2) |
| 20-oct: Suomi NPP sin records ni gránulos | causa **SIN DATO** |
| El auto-audit fuera de banda (#864) | explicado casi entero por el fondo y la ROI (R2 §0); **SOSPECHA** para las dos protegidas MODIS de Chillán sin gránulo |

## e. Lo que ya está cerrado y no hay que rehacer

- **Los dos ports en Python son el `.m` en la detección** (Octave, 791 escenas, máscaras idénticas en orden, cuatro
  mutaciones de control): no repetir esa comparación. MATLAB no puede decidir otra máscara por aritmética (margen
  mínimo 2,8e-5).
- **Las 12 afirmaciones del brief de la segunda ronda** se sostienen en lo esencial (`docs/AUDIT_S158_R2.md` §1 y §5).
- **Las 411 pasadas del OSF 2025 sin record no son pérdida de descarga**: 357 de calendario, 53 diurnas, 1 de NASA, 0
  de descarga ni de geolocalización. VIIRS nocturno dentro de la serie: 0 faltantes de 2.263.
- **No hubo ningún L1B sin geolocalización** en 1.772 gránulos nocturnos de 4 volcanes en 45 días (VB-1 existe en CMR
  global, no nos tocó).
- **La sospecha de las zonas de agregación para el escalón de 50°**: refutada; no reabrir.
- **El radio de cumbre de MIROVA es nuestro `inner_radius_km`** en los 11 volcanes (láminas «Dist»).
- **El reemplazo del histórico por K**: hecho y verificado; no reprocesar de nuevo por K.

## f. Prompt para la próxima sesión

```
Retoma VRP Chile en la ola 2 del plan S159. Antes de creerle a nada:

1. cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"; git fetch origin --prune; git status -sb
   (debe ser loop/activo); pide la hora al servidor (gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date, A86).
2. Lee CLAUDE.md del proyecto, después tasks/BLOQUE_ARRANQUE_S159.md entero, después tasks/LOOP_OBJETIVOS.md §4
   («Bloque S158 R2 y plan S159») y la primera entrada de su §6.
3. Comprueba contra GitHub, no contra este texto: estado de #888, #889 y #890 (gh pr view); si #889 ya se mergeó,
   verifica que main tenga el commit y el CI verde. Comprueba si CMR ya volvió a servir Chile del 17 al 20 de octubre
   (búsqueda pública granules.json, sin credenciales).
4. Si Nicolás corrió el paquete O2 (C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\o2_paquete\), lee su salida con
   leer_o2.py antes de la ola 2.

Trabajo (worktree C:\vrp-trabajo\s159-pruebas, rama s159-pruebas; el plan es
docs/superpowers/specs/2026-10-21-pruebas-post-auditoria-s158-design.md):
- Ola 2, en paralelo: N (prueba a escala del fondo y la suma del código junto con quitar la compuerta de 3 K, tope 400
  pasadas, workflow de sólo lectura con EARTHDATA_TOKEN, con la grilla de 750 m que midió GEO y las dos variantes de
  fondo MODIS de P3; el VRP de un píxel se informa con su banda o con O2), M (MODIS con MOD03, estratificado por lado
  del barrido y posición en el gránulo, más las dos protegidas de Chillán del #864) y la relectura de D25 (sólo
  después de que Nicolás decida el choque del placebo de #890, decisión 2).
- Ola 3: pre-registro de adopción del paquete VIIRS 750 (R2.3) con la regla de docs/MISSION.md, diseño del A/B
  respetando A114, verificador con contexto limpio.
- Cada informe de agente lleva el preámbulo canónico ENTERO (docs/_prompts/PREAMBULO-AUDITOR.md), su carpeta
  experiments/_s159/<frente>/, y reporta candidatas para docs/BEYOND_MIROVA_EXTENSIONS.md §12 (lo que podríamos hacer
  mejor que MIROVA, pedido de Nicolás).

Reglas duras: no tocar pipeline/, data/ ni frontend/ sin tag y sí de Nicolás (A45); sólo EARTHDATA_TOKEN, nunca usuario
y clave (A71); una sola sesión dueña del loop; no commitear páginas renderizadas de papers, TIF bajados ni matrices
.mat (gitignore en experiments/_s159/); git add por archivo; esperar el CI con conclusión antes de mergear; español de
Chile sin voseo ni guiones largos; rutas absolutas al entregar archivos.

Si la sesión no alcanza: commitea lo que haya por frente, anota en la bitácora del loop qué quedó corriendo (run id) y
cierra con /cierre.
```
