# Bloque de arranque S201 (escrito por S200, 2026-11-25 ~18:45 UTC)

> El bloque anterior (S200, escrito por S199) queda como histórico en `tasks/BLOQUE_ARRANQUE_S200.md`. Detalle de S200
> en la bitácora `tasks/LOOP_OBJETIVOS.md` §6 (entrada S200, arriba) y en la nota viva
> `D:\vrp-trabajo\temporales\s200\s200_nota_viva.md`. S200 cerró por contexto (550 mil tokens).
> **Estado fijado CON TRABAJO EN VUELO (no es un estado quieto):**
> (1) cadena del piso `D:/vrp-trabajo/temporales/s199/cadena_piso_s199c.sh` viva, esperando la tanda 6 (julio, run
> 45608195262) y despachando agosto a noviembre (registro `D:\vrp-trabajo\temporales\s198\barrido\cadena.log`);
> (2) ronda 5 de Codex, ventana 1, `D:/vrp-trabajo/temporales/s200_r5/cadena_r5a.sh` (faa, fab, fcda, fcdb; lanzó faa a las
> 18:39 UTC; registro `D:\vrp-trabajo\temporales\s200_r5\corridas\cadena.log`);
> (3) vigilante `D:/vrp-trabajo/temporales/s200/vigilar_sombras.sh`, espera las sombras programadas de la noche del 25
> para ver si cierran #1124 y #1125. Los tres son procesos de bash de la sesión S200: si la app se reinicia, mueren.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| `main` | ficha **v1.109** (`3354563c3`), siete PR de S200 | `git show origin/main:docs/FICHA_SDA_VRP_CHILE.md` |
| #1126 (R4FEF-109/106: un JSON roto afecta sólo a su volcán; cobertura se relee cada 5 min) | en main v1.103, **verificado en Pages** (43 tarjetas, sin errores) | PR del agente de S199, verificado por S200 |
| #1127 P0(3) enmascaramiento | en main v1.104: nulo en el flanco en VIIRS 750 | `experiments/_s200_p0_3/INFORME.md` |
| #1128 (R4FEF-107 segunda mitad, R4C-106: miniaturas se releen cada 5 min) | en main v1.105, Pages sirve el `miniaturas.js` nuevo | |
| #1129 re-sello del evaluador del piso (decisión de Nicolás «Sí, re-sella») | en main v1.106 | `experiments/_s196_lab_piso/PREREGISTRO.md` §5b |
| #1130 tres correcciones tras el verificador limpio de #1129 | en main v1.107 | `D:\vrp-trabajo\temporales\s200\verif_1129\VEREDICTO.md` |
| #1131 acta de cierre de la ronda 4 (Nicolás «Sí, apruebo», 17:14 UTC) | en main v1.108 | `docs/ACTA_CIERRE_AUDITORIA_CODEX_RONDA4_2026-11-25.md` |
| #1132 fin del barrido sellado en 2026-11-23 (R4FD-107) | en main v1.109; sello del evaluador `d17a68a2...` = pre-registro | |
| Codex ronda 4 | **TERMINADA** (cierre 14 de 14 confirmado; 402 filas) | `D:\codex-vrp\_salida\ronda4\RESUMEN_R4_PARA_NICOLAS.md` |
| Codex ronda 5 | consulta hecha; ventana 1 corriendo (A re-sello; C+D guardias y auditoría semanal) | `D:\codex-vrp\_salida\ronda5\_consulta\OPINION_RONDA5.md` |
| R4FA-109 (reemplazo NRT por estándar) | medido: 0 alertas borradas en la vía, 0 protegidas | `D:\vrp-trabajo\temporales\s200\r4fa109\INFORME.md` |
| Barrido del piso | abril a junio cerrados y contados; julio en curso | `cadena.log`, `salida_contar_piso_t5.txt` |
| Los 34 | historia 32 volcanes, 216.134 records vía (2025-02-15 a 2026-11-02) + sombra desde 11-03 | `data/historia_34/`, `data/sombra_34/` |
| Guardias | VERDE: MODIS 31 de 29 (vence 2027-03-02), V750 23 de 29 y V375 23 de 29 (vencen 2027-03-11) | vigilancias del 2026-11-25 05:01 y 05:11 UTC |
| Issues | #1124, #1125 (sombras sin corrida programada verde; vigilante en curso); #1106 (cierra 2026-11-30) | `gh issue list` |
| Disco | C: 33 GB, D: 14 GB (18:40 UTC) | `df -h` |

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | P0 parte 4 (ventana de todo el edificio): con P0(3) nulo, la palanca para ver el flanco es la caja | radios del edificio por volcán (D-H) + A45 / esperar | Fijar los radios del edificio en el visor; la caja va detrás de un flag apagado en el laboratorio |
| 2 | Traza `nrt_reemplazado` en `store.py` (R4FA-109, opcional) | sí con A45 / no | No por ahora: 0 alertas borradas en la vía; baja prioridad |
| 3 | Clave de NASA FIRMS para cotejar las lejanas grandes de los 34 (incendios) | pedir la clave (gratis) / no | Pedirla si se van a publicar los 34 (D1 a D15) |
| 4 | Rotar el PAT de GitHub que sigue en `C:\Users\nmend\.claude\settings.json` | rotar y pasar a variable de entorno | Rotarlo |
| 5 | Heredadas del bloque S200 §b.2 y §b.3 (R3F3-104; `Temp-1` a `Temp-228`) | | las del bloque S200 |

**Preguntas de Nicolás de S200 sin respuesta explícita:** ninguna. «¿Cómo va el plan por sensor y el experimental?
¿Se reprocesaron el resto de los volcanes?» se contestó con datos (guardias, barrido, `data/historia_34/`).

## c. Lo aprendido

- **REGLA GENERAL (memoria `feedback_s200_junctions_y_rm.md`):** un árbol temporal con enlaces de directorio
  (`mklink /J`) al repo se borra quitando antes cada enlace con `cmd /c rmdir`; un `rm -rf` de bash puede seguirlos.
  Viven en cada subcarpeta (S200 quitó 106 y 54 y 54).
- **REGLA GENERAL:** el verificador independiente de un PR propio vale aunque uno ya lo probó: el de #1129 encontró
  tres efectos no buscados (SIN PODER tapaba un INVALIDO; poder contado fuera de la ventana; 82 min de costo) que mis
  pruebas y 8 de 8 mutaciones no veían.
- **REGLA GENERAL:** una prueba que pasa con el código viejo cuando debía fallar es una prueba mal armada: b2 pasaba
  porque al mover fechas colisionaban dos pasadas en la misma clave (28 en vez de 40).
- **Proyecto:** `mutar.py` (S196) arma un árbol con sólo los dos evaluadores; desde el re-sello necesita enlaces a
  `pipeline/` y `scripts/` y `volcanoes.yaml` (#1129). Un texto de mutación que cambia sale «0 veces», no atrapada.
- **Proyecto:** `codex sandbox` pide `--permission-profile vrp-auditoria --profile <perfil> --cd 'D:\codex-vrp'` y una
  ruta de script con barras normales (las invertidas se pierden en bash).
- **Proyecto:** `contar_brazos_piso.py` cuenta publicaciones por brazo: es una mirada parcial a resultados; el re-sello
  lo declara en el §5b.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO:** la sombra código MIROVA del 24-nov 23:47 UTC falló en 5 volcanes del norte por `ReadTimeout` del CMR
  (log del job de Láscar). **SOSPECHA:** las programadas de la noche del 25 cierran #1124 y #1125 (vigilante en curso;
  su salida queda en la tarea de fondo de S200, que muere con la sesión: mirar `gh issue view 1124 1125`).
- **CONFIRMADO:** R4FA-109 sin efecto en la vía (1.385 reemplazos, 0 alertas borradas; 8 perdidas en la era K, 7 por
  el cambio a K #850).
- **SOSPECHA:** con Cordón Caulle excluido el barrido no podría dar ELEGIDO (R4FD-102 depende de él; verificador de
  #1129, punto 3); hoy todos los brazos lo traen.
- **SIN DATO:** si la tanda 6 (julio) termina verde; mirar `cadena.log`.

## e. Ya cerrado, no rehacer

- Ronda 4 de Codex: terminada con acta aprobada (#1131). No repetir sus frentes; la ronda 5 cubre lo nuevo.
- Re-sello del piso: hecho y verificado (#1129, #1130, #1132); sello vigente `d17a68a2...`. No volver a tocar el
  evaluador antes de evaluar sin decisión de Nicolás.
- P0(3): nulo en el flanco en VIIRS 750 (razón con/sin 1,000 en mediana a 5 km o más); no repetir en VIIRS 750.
- R4FA-109: medido, aceptado por el acta.
- Los 34 ya están reprocesados con la vía desde 2025-02-15 (`data/historia_34/`, 216.134 records).

## f. Prompt para S201

```
Retomas VRP Chile como sesión dueña del loop (S201). Español de Chile, sin guiones largos, rutas absolutas.
Si te abrió otra sesión, mcp__ccd_session_mgmt__detach_session("self"). S200 cerró y no trabaja más.
Nicolás (2026-11-25 ~18:30 UTC): «sigue con el loop, con las auditorías de codex, y todo lo que falte».
Autorizó antes seguir sin preguntar cada paso, hasta 900 mil tokens por sesión.

1. Verifica antes de creer: git fetch --prune; ficha de main (esperado v1.109 o más); gh pr list; gh issue list
   (#1124 y #1125: ¿se cerraron con las sombras programadas de la noche del 25?; si no, mira la causa); df de C: y D:.
   Procesos de S200 que pueden haber muerto: ps -ef | grep -E "cadena_piso|cadena_r5|codex".
   - Piso: si no hay cadena viva, mira el final de D:\vrp-trabajo\temporales\s198\barrido\cadena.log y relanza en
     segundo plano con la tanda en curso (copia cadena_piso_s199c.sh si hay que cambiar la tanda inicial).
   - Codex ronda 5 ventana 1: mira D:\vrp-trabajo\temporales\s200_r5\corridas\cadena.log y los .fin. Si la cadena
     murió a medias, relanza sólo los pasos faltantes (los pasos son faa, fab, fcda, fcdb de cadena_r5a.sh).
2. Lee tasks/BLOQUE_ARRANQUE_S201.md (rama loop/activo) y la entrada S200 de tasks/LOOP_OBJETIVOS.md §6. Para Codex:
   D:\codex-vrp\_salida\ronda5\_consulta\OPINION_RONDA5.md y la maquinaria D:\vrp-trabajo\temporales\s200_r5\.
3. Trabajo, en orden:
   a. Ronda 5: al terminar cada frente (fa_r5, fcd_r5), verificador Claude de contexto limpio (plantilla
      D:\vrp-trabajo\temporales\s200_r5\verificador_plantilla.txt; copia hacer_verificador_r4.py y consolidar_r4.py de
      s199_r4 a s200_r5 cambiando ronda4 por ronda5 y la central desde ronda4\hallazgos_verificados.csv). Después
      ventana 2: B (historia de los 34, informado, 8 M) y E (declaraciones públicas, informado, 6 M), cierre informado
      6 M; escribe sus encargos como los de la ventana 1. Arreglos verificados de gravedad 3 o más como PR (A45 donde
      toque). Resumen para Nicolás en D:\codex-vrp\_salida\ronda5\RESUMEN_R5_PARA_NICOLAS.md.
   b. Barrido del piso: cuando estén todas las tandas (hasta noviembre), evaluar con experiments/_s196_lab_piso/
      evaluar.py calibrar (fin sellado 2026-11-23) y llevar el resultado a Nicolás sin adoptar nada.
   c. Plan por sensor y experimental: nada listo sin decisión de Nicolás (ver §b); si responde, actuar.
4. Reglas duras: A45; merges con D:\vrp-trabajo\temporales\s195\merge\uno.sh en serie (fila_<N>.txt antes; versión
   siguiente a la de main; fecha UTC del merge; --match-head-commit); nada de git stash; git add por archivo; nunca
   experiments/_s176_codex/; temporales y worktrees en D:; números sólo de scripts; .md con newline=""; nada de python
   en heredoc con barras invertidas (usa Edit); un vigilante por corrida; nunca pedir ni recibir tokens por el chat;
   verifica cada PR por cuenta propia y, si es tuyo y toca un evaluador o el pipeline, con un verificador limpio;
   árboles con enlaces de directorio se limpian con cmd /c rmdir, nunca rm -rf.
5. Cierra con /cierre al llegar al umbral de contexto (550 mil; Nicolás autorizó hasta 900 mil) y deja el prompt de S202.
```
