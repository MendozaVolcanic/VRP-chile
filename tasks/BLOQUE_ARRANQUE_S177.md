# Bloque de arranque S177 (cierre de S176, 2026-11-09 04:20 UTC)

> **Estado fijado con trabajo en curso.** En GitHub Actions sigue corriendo D2, intento 2 (run 42507820590): a las 04:13 UTC, 33 de 48
> verdes, 6 en curso, 9 en cola. No hay agentes ni procesos locales vivos; el vigilante local de D2 se detuvo a propósito. El NRT de las
> 04:10 UTC estaba en cola. Leer el estado real antes de creerle a esta tabla.
>
> El bloque anterior sigue entero en `tasks/BLOQUE_ARRANQUE_S176.md`. Se cierra por cambio de día (contexto en 25 %), a pedido de Nicolás.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| #965 mapa «Todos los pixels» | MERGEADO y publicado | `7e0cc55da`; verificador MERGEABLE en `C:\Users\nmend\vrp-temporales\s176_verpr\965\INFORME.md` |
| #964 lector de V750-A en una versión | MERGEADO | `87fb5a43a`; verificador MERGEABLE en `C:\Users\nmend\vrp-temporales\s175_verpr\964\INFORME.md`; VPR964-01 a 03 van antes del sello |
| #967 PR A: guardia K y vigilancia de VIIRS, audit por sensor, marca del tablero | MERGEADO 2026-11-08 20:46 UTC, inerte | `ef9b1f9a7`; Tests y Pages en verde; sólo `enable_modis_codigo_mirova` encendido en el perfil; verificador MERGEABLE en `C:\Users\nmend\vrp-temporales\s176_verpr\967\INFORME.md` |
| #966 token rechazado deja el NRT en rojo, con descarga buena por corrida | MERGEADO 2026-11-08 21:32 UTC | `d81d01503`; tag `pre-s176-fetch-966`; verificador MERGEABLE CON RESERVAS en `C:\Users\nmend\vrp-temporales\s176_verpr\966b\INFORME.md`; NRT con ese código en verde a las 01:10, 02:10 y 03:10 UTC |
| Dos preguntas de Nicolás, con números y fuente | CONTESTADAS | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s176_preguntas\RESPUESTAS.md`; verificador SE SOSTIENE EN PARTE, corregido |
| Diseño del encendido de VIIRS (B1 V375, B2 V750) | ESCRITO, sin encender | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\superpowers\specs\2026-11-08-encendido-v375e-design.md` |
| Plan del visualizador contra MIROVA | ESCRITO, espera decisión | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\superpowers\plans\2026-11-08-visualizador-como-mirova.md` |
| Plan GPT Codex y prueba ciega | ARMADA, falta la parte web de Nicolás | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\superpowers\plans\2026-11-08-auditoria-gpt-codex.md`; repo privado `MendozaVolcanic/vrp-codex-ciego` en `be33a9999`, Actions apagado; lista sellada `C:\Users\nmend\vrp-temporales\s176_codex\SELLADO_lista.md`, sha256 `d8099f8a...4950` |
| Reproceso D1 (humo) | VERDE, vía en 100 % | run 42507360401, 31 records |
| Reproceso D2 | **EN CURSO, intento 2** | run 42507820590, 48 trabajos (la bitácora dijo 47); intento 1: 29 verdes, 19 con salida 3 por SEARCH_CMR_TIMEOUT; relanzados con `gh run rerun --failed` |
| Reproceso D3 y D4 | SIN DESPACHAR | sólo existen los tags `s172-retro-d1` y `-d2`; D3 con `_s172_retro_k`, D4 con `_s172_retro_paquete` (176 trabajos) |
| Guardia K de VIIRS | ACTIVA, sin primera corrida | cron 19:35 UTC; primera el 2026-11-09; issues #968 y #969 «vigilancia ciega» previstos (VPR967-06) |
| Guardia K de MODIS | **PRIMERA FALLA** | run 42524887089 del 11-08 21:22 UTC: 8 de 11 volcanes en rojo, 13 a 21 fallas de cobertura cada uno, CMR; las 5 anteriores verdes |
| Sombra de los 11 y de los 34 | ROJAS el 11-08 | 3 de 11 (Chillán, Copahue, Llaima) y 1 de 34 (Callaqui), cobertura incompleta por CMR; #960 y #962 abiertos |
| Audit semanal del 2026-11-09 | NO CORRIDO al cierre | último `audit-weekly.yml` 11-02; es el primero con la vía MODIS |
| #955 síntesis de auditoría S175 | BORRADOR, CLEAN | `43b330ef9`; falta el anexo del audit |
| `loop/activo` | con main integrado hasta #966 | merge `321c3321a`; main siguió avanzando sólo con datos del NRT |
| Plan semanal y disco | 20 % (Fable 25 %), reinicio 2026-11-15 12:00 UTC; C: 14 GB, D: 4,5 GB | `get_usage` y `df -h`, 04:13 UTC; 25 worktrees |

## b. Decisiones que espera el dueño

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Prueba ciega de Codex: conectar sólo `vrp-codex-ciego`, sin internet ni secretos, GPT-6.1 Sol High, una tarea | hacerla o postergarla | Hacerla: no depende del reproceso y sólo Nicolás puede |
| 2 | Merge de #955 tras el anexo | frase | Sí |
| 3 | Sello de la regla de reversión D1 a D7 | ahora o tras recalcular | Tras recalcular las cotas de VIIRS 375 con los casos del reproceso: hoy descansan en 2 y 5 casos (IC 95 % [3, 42] y [6, 30]) |
| 4 | Autorización A45 y excepción §12.6 para B1 y B2 | por sensor | Sí por separado, con 3 noches de guardia y VPR967-02 a 06 resueltos; B2 además con `experiments/_s162_v750a/vara_matlab_v750a.py` en verde |
| 5 | D3 y D4 con `max-parallel` 6 o menos | 6, o bajar a 4 como anticipa la cabecera de `reproc-retro-paquete.yml` | Primero medir si la carga propia influye (ver d); si no se puede, D3 como está y D4 en 4, o en horario sin sombras |
| 6 | Red ampliada de los 34 | radio de cráter propio o seguir sin `inner_radius_km` | Radio de cráter de 5 km |
| 7 | Fases del visualizador | las tres del plan | Partir por la fase 1 del plan |
| 8 | Protección de rama de main | checks obligatorios o dejar | Checks `pytest` y `bateria-v750a` |
| 9 | Limpieza de worktrees viejos en D: (A38) | hacerla o dejar | Hacerla: D: en 4,5 GB |
| 10 | Una caída a K deja la guardia en VIGILANCIA_CIEGA 14 días; decisiones 2, 3 y 4 del bloque S175 | ver bloque S176 | Las recomendadas ahí |
| 11 | Dos líneas para `CLAUDE.md` del proyecto (Constraints), propuestas por revise-claude-md | aplicar o no | Aplicar: «reproceso con `--estricto-cobertura`: un corte de CMR sale con código 3; esperar el fin del run y `gh run rerun --failed`» y «con `MSYS_NO_PATHCONV=1`, `git worktree add` lleva ruta `C:/...`, nunca `/c/...`» |

Sólo Nicolás, sin decisión de por medio: rotar `EARTHDATA_TOKEN` antes del 2026-11-27; rotar el PAT de GitHub que sigue en texto plano en `C:\Users\nmend\.claude\settings.json` y moverlo a variable de entorno; revisar la carpeta sobrante `C:\c`.

## c. Lo aprendido

- **REGLA GENERAL. Un conteo se lee de la salida, no se suma de cabeza.** Dije «26 terminados, 25 bien» sumando los 6 en curso y prometí 2,5 h con la duración de los primeros trabajos; eran 20, y D2 tardó 5,5 h. Extiende S91. Destino: `feedback_s176_lecciones.md`.
- **REGLA GENERAL. Con `MSYS_NO_PATHCONV=1`, `git worktree add /c/...` crea `C:\c\...`.** Destino: misma memoria.
- **REGLA GENERAL. `gh run watch` local muere con un corte de red o con el PC cerrado, y su salida 1 no dice nada del run.** Esperar con un bucle que tolere errores. Destino: misma memoria.
- **REGLA GENERAL. Un armador que limpia su destino no se re-ejecuta** sin mirar qué se agregó a mano después: `armar_ciego.py` borró `AGENTS.md` y `ci/`. Destino: misma memoria.
- **REGLA GENERAL. `grep` con guiones Unicode da falsos positivos en este locale:** comprobar con Python y `\u2014`, `\u2013`.
- **Proyecto.** Alertas térmicas de Mirova-v1: filtrar por `Tipo_Registro == ALERTA_TERMICA`, no por `Clasificacion Mirova`; el audit local con CSV viejo engaña (bajar los frescos).
- **Proyecto.** Una falla de reproceso con salida 3 se clasifica por log antes de relanzar. Un corte de CMR ya no se puede atribuir «a NASA» sin mirar qué más corría (ver d).
- **Proyecto.** Un cambio chico y acotado se verifica bien con Sonnet en high: 31 herramientas, 176 mil tokens, 4 reservas reales, y Fable queda para lo grande.

## d. Problemas abiertos e hipótesis

| Ítem | Etiqueta |
|---|---|
| 19 de 48 trabajos de D2 fallaron por SEARCH_CMR_TIMEOUT, ninguno en descarga ni de credencial | CONFIRMADO (19 logs clasificados) |
| El 11-08 por la tarde el corte tocó además guardia MODIS (8 de 11) y sombra de los 11 (3 de 11), mientras el NRT seguía verde | CONFIRMADO |
| **Nuestro propio reproceso aporta a esos cortes** (6 trabajos paralelos con búsquedas por ventana de hasta 20 días, más NRT, sombras y guardia con el mismo token) | **SOSPECHA**: todas las fallas caen entre las 19:13 y las 00:20 UTC con el reproceso corriendo, pero D1 y los primeros 19 de D2 no fallaron y no hay un control sin reproceso. Importa antes de D4 |
| Audit local con datos del 11-08: FUERA_DE_BANDA por V375 Chillán 0,602 y Tupungatito 0,466 | CONFIRMADO, no es el audit oficial |
| Razón de magnitud 11-03 a 11-07: V375 producción 0,504 y sombra 0,993; V750 0,482 y 1,000 | CONFIRMADO con verificador, EXPLORATORIO, no decide adopción; «ninguna pierde protegidas» vale sólo de noche |
| VPR966B-01: token que muere a mitad de corrida con 403 no aborta esa corrida; la siguiente sí | CONFIRMADO en simulación; qué status da LAADS al vencer un token es SIN DATO |
| VPR966B-02: `_DESCARGA_BUENA` no mira lo devuelto (`pipeline/fetch.py`, tras `download_granules`) | CONFIRMADO, g1 a 2, semántica heredada del contador anterior |
| VPR967-01: cotas de VIIRS 375 con 2 y 5 casos | CONFIRMADO, pesa en el sello |
| Causa de la corrida roja de la sombra del 11-03 | SIN VERIFICAR |
| Heredados de S176: VX-04 Planchón-Peteroa Terra en NRT y K; `pipeline/store.py:693` «3-5 days»; `scripts/token_edad.py` «ok» con salto de línea; rótulo «sin publicación de MIROVA» (`frontend/index.html:2352`) | CONFIRMADOS al cierre de S175, no revisados hoy |
| V33B-02: `alerta_protegida` acepta filas sólo OCR anteriores a 2026-06-11 | SOSPECHA, g2 |

## e. Lo que ya está cerrado y no hay que rehacer

- #964, #965, #966 y #967 en main, cada uno con verificador limpio de otro modelo y frase de Nicolás. Decisión de VPR966-01 ya tomada: por corrida.
- Por qué no se publica la sombra de los 34: 17 detecciones, 0 a 5 km o menos del volcán, 3 a 10 km o menos, dos pares son el mismo foco; no tienen `inner_radius_km`.
- 45 volcanes, no 43: 11 en el NRT, 34 en sombra; el tablero no los lee a propósito (`hasMirova`).
- La auditoría de los dos visualizadores y el plan para Codex: hechos, no rehacer; falta decidir y ejecutar.
- El medidor completo de V750-A deja de decidir: con flag propio B2 pasa a lectura informativa (spec, decisión 6).
- `armar_ciego.py`: no volver a correr.
- Issues #968 y #969: esperados, no son falla.

## f. Prompt para la próxima sesión

```
Sesión S177 de VRP Chile (coordinadora del programa de réplica por sensor). Carpeta:
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile, rama loop/activo.

1. Verifica antes de creer: date -u; git fetch origin --prune; git status -sb; HEAD contra git ls-remote origin -h
   refs/heads/loop/activo; df -h /c /d; get_usage; gh pr list --state open. Mira el último run de nrt.yml, sombra-34.yml,
   sombra-codigo-mirova.yml, guardia-k-modis.yml, guardia-k-viirs.yml, vigilancia-guardia-viirs.yml y audit-weekly.yml, y el run
   42507820590 de D2 (intento 2).
2. Lee: CLAUDE.md; tasks/BLOQUE_ARRANQUE_S177.md entero; las entradas S176 de la bitácora §6 de tasks/LOOP_OBJETIVOS.md;
   docs/superpowers/specs/2026-11-08-encendido-v375e-design.md; experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md §10 y §11.
3. Trabajo, en este orden (máximo 5 agentes, sólo con holgura de memoria comprometida):
   a. Avísale a Nicolás de los issues abiertos y de qué pasó con la guardia MODIS del 11-08 (primera falla, cortes de CMR).
   b. D2: si quedan trabajos rojos, clasifícalos por log y relanza con gh run rerun --failed. Antes de D3 y D4, mide si nuestro reproceso
      aporta a los cortes de CMR (horas de falla de guardia, sombra y NRT contra trabajos activos). D3 (_s172_retro_k, tag s172-retro-d3) y
      D4 (_s172_retro_paquete, tag s172-retro-d4, 10 volcanes sin Tupungatito, 2025-02-15 a 12-31, 176 trabajos), tags sobre a7a6ae360,
      de a uno según §10.3. Comprueba C-via y baja con bajar_tramos.py --estricto. No leas nada como evidencia antes del candado §11.
      Los artefactos duran 30 días.
   c. Audit semanal del 2026-11-09: léelo, escribe el anexo de #955, verificador si cambia conclusiones, pide el merge.
   d. Guardia K de VIIRS: 3 noches desde la primera corrida (cron 19:35 UTC, puede atrasarse). Recalcula las cotas de VIIRS 375 con los
      casos del reproceso. Atiende VPR967-02 a 06 y VPR964-01 a 03. Prepara B1 y B2 en borrador; el sello y la autorización son de Nicolás.
   e. Si Nicolás hizo la prueba ciega: puntúa INFORME.md contra C:\Users\nmend\vrp-temporales\s176_codex\SELLADO_lista.md (al menos 5 de
      8 defectos con archivo correcto y ningún archivo o línea inventados); las 3 mutaciones sembradas están en
      C:\Users\nmend\vrp-temporales\s176_codex\SELLADO_mutaciones.json. Después el segundo mensaje.
   f. Aprobado, sin preguntar otra vez: conteo de filas OCR que descarta la tabla (decisión 1 de #957), sacar S139 de la suite como
      histórica, re-correr F5b con la máscara corregida.
   g. Según lo que decida Nicolás: fases del visualizador, red ampliada de los 34.
4. Reglas duras: pipeline/ congelado durante la sombra (excepciones: ROI de V750, emergencias del NRT, token autorizado); nada en
   pipeline/, data/ ni frontend/ sin tag y sí de Nicolás (A45); merge a main sólo con frase de Nicolás y gh pr merge --match-head-commit;
   sólo EARTHDATA_TOKEN (A71), nunca entregado a Codex; ninguna llamada a NASA desde verificadores; verificador limpio de otro modelo antes
   de aceptar un resultado y el autor comprueba al verificador; effort high explícito y carpeta temporal propia; máximo 2 procesos
   pesados locales; parada bajo 3 GB libres en C: o D: (mira C:\pagefile.sys); git add por archivo; nunca git stash; date -u antes de
   cada encabezado de bitácora; un PR sin checks no es verde; heredocs sin \v ni \t; export MSYS_NO_PATHCONV=1 en git show, y con él
   rutas C:/ en git worktree add; español de Chile con tú y sin guiones largos ni medios; rutas absolutas completas para Nicolás.
5. Si la sesión no alcanza (contexto sobre 50 %, dos hitos o cambio de día): commitea, anota en la bitácora y cierra con /cierre (bloque S178).
```
