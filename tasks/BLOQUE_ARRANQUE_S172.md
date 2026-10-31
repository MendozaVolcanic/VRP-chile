# Bloque de arranque S172 (cierre de la sesión S171, 2026-10-31 23:15 UTC)

> **Estado fijado sin trabajo en curso de VRP Chile**: 0 agentes vivos de esta sesión (los cuatro entregaron); el único
> proceso Python del computador es de otro proyecto (`Empresas/Autoscan/autoscan-chile/run_ciclo.py`, desde las 23:06
> UTC). `loop/activo` local = remoto = `3ab2c36fe` antes del commit de este cierre; `main` = `f7de70e27` (sólo commits
> de datos desde `478d9c086`, el commit medido hoy). **Cuota semanal al 98 %, se reinicia el domingo 2026-11-01 12:00
> UTC**; la de Fable va en 38 %. Bitácora detallada: `tasks/LOOP_OBJETIVOS.md` §6, entradas S171.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| **MOD-D (MODIS): se ADELANTA** | Nicolás decidió no esperar la parada: encender la vía con K de guardia y reversión pre-autorizada. **Borrador de la regla escrito, sin sellar**, con las cotas del A/B marcadas A COMPLETAR | `experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md` (`3ab2c36fe`); bitácora S171 «Nicolás adelanta MODIS» |
| Pre-registro de MOD-D | marca SELLADA en §8.2 y §13 (texto original conservado) | rama `claude/s170-modd-f4-procedencia` `25e3cc3ba` |
| V750-B (2026-11-03) | **ensayo en seco completo y limpio**: control de datos falla con `--hasta 2026-11-02` hoy y pasa con el 30; 5.945 objetivos, IGUALES, 0 sin gránulo, N-3 = 4; armado de la rama de disparo OK; el yml no baja tags | `D:/vrp-trabajo/temporales/v750b_r4_ensayo_s171/`; bitácora S171 |
| V750-A equivalencia | **VERDE en main** (1.020/10) con la copia de main de la prueba. S171 había dicho ROJA por correr la copia atrasada de la rama: lo corrigió el verificador limpio. Vara del criterio 1 decidida: **MATLAB directo** | `D:/vrp-trabajo/temporales/ver_s171_equiv/INFORME.md`; bitácora S171 «CORRECCIÓN» y «vara MATLAB directo» |
| Pre-mortem del 2 y 3 de nov | ningún camino deja esos días sin dato en silencio; 171-01 (descarte de gránulos de borde) baja a G2 porque el lector de V375-E lo trata como SIN DATO; el cron de la sombra llega 4 a 5 h tarde | `D:/vrp-trabajo/temporales/audit_s171_dia3/INFORME.md` (§7: qué mirar el 2 y el 3); `ver_s171_171_01/INFORME.md` |
| D-43 | re-verificada: abiertas sólo la 6 (C-10) y la 9 (K1 -0,7 y tope D9) | fila D-43 de `tasks/LOOP_OBJETIVOS.md` §5 |
| Programa | §12.7 nuevo: calendario y cuatro mejoras (ROI de V750 el día de la lectura, ensayo en seco, token el 27-nov, limpieza) | `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` |
| META_RULES | lecciones de S170 pasadas | `docs/META_RULES_S80.md` (`ddfb5dab2`) |
| Limpieza | 16 + 1 sesiones archivadas (MOD-D incluida); 18 worktrees quitados con respaldo de lo no versionado (464 MB) | `D:/vrp-trabajo/papelera_s171/` (`LEEME_commits.txt`); C: 35 GB, D: 14 GB |
| Sesión viva | VIIRS 750 (`local_94f4be0d`), quieta, 28 % de contexto; reporta a S171/S172 y tiene todos los encargos | mensajes S171 |
| Token Earthdata | `estado=ok vence=2026-12-07T18:03`; rotar el 2026-11-27 | `nrt-healthcheck` run 41219805607 |
| Producción | NRT verde (21:00 UTC); sombra verde a diario sin ventana hasta el 3 | `gh run list` |

## b. Decisiones que espera el dueño

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Sello de la regla de reversión de MODIS | sellar tras verificador / pedir cambios | **Sellar tras completar las cotas desde el A/B y un verificador limpio de otro modelo** |
| 2 | Merge del encendido de MODIS (A45) | sí / no | **Sí, cuando el PR tenga la lista del §5 del borrador** (flag, guardia, ficha SDA, marca en las tres vistas, tag `pre-s171-adopcion-modd`) |
| 3 | Guardia de MODIS | reusar la sombra con MODIS en K / perfil nuevo | **Reusar la sombra**, si el lector sellado de V375-E no marca régimen nuevo por cambiar claves de MODIS (comprobar primero) |
| 4 | D-43 punto 6 (C-10) y punto 9 (K1 -0,7, tope D9) | mirar / postergar | **Postergar hasta después de la parada**: los dos tocan `pipeline/`, congelado |
| 5 | Rotar `EARTHDATA_TOKEN` | el 2026-11-27 / al vencer | **El 2026-11-27** (lo hace Nicolás) |

## c. Lo aprendido

Proyecto (a `docs/META_RULES_S80.md` en la próxima revisión; memoria `feedback_s171_lecciones`):
- **Antes de correr un instrumento, comprueba de qué ref sale cada archivo.** S171 armó el árbol con el módulo de main
  y la prueba de una rama atrasada, y reportó una equivalencia ROJA que en main es VERDE. Un `sha256sum` de las dos
  copias lo habría visto; lo vio el verificador limpio.
- **Un verificador limpio de otro modelo volvió a encontrar algo** en las dos revisiones de S171 (un error de montaje
  propio y cuatro huecos de la vara). La regla sigue valiendo.
- **Antes de borrar worktrees, respaldar también lo ignorado** (`git status --porcelain --ignored`): ahí estaban los
  CSV de hallazgos de S160 y los `.mat` de MATLAB (que además estaban versionados en main, lo que S171 no comprobó).

Regla general del workspace:
- **El cron de GitHub Actions llega con horas de atraso** (4 a 5 h medidas en la sombra y el monitor): un calendario
  operativo se escribe con la hora real de la corrida, no la del cron.
- **Los agentes Fable descuentan de las dos cuotas** (la de Fable y la general): con la general al 95 %, dos agentes
  Fable la llevaron a 98 %.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO**: la vía de VIIRS 750 de main es igual a MATLAB en 311 de 311 escenas (verificador limpio).
- **CONFIRMADO**: la vía descarta en silencio los gránulos de borde (171-01); el lector de V375-E los deja SIN DATO.
- **CONFIRMADO**: el pre-registro de V750-A §4.1 todavía nombra la vara vieja y no hay salida verde registrada
  (VS171-01, G4); el halo de 7 celdas no se prueba (VS171-02, G3); E3 debe quedar (VS171-03, G3).
- **SOSPECHA**: el SIN DATO del lector de V375-E sesga hacia el borde del barrido (no medido).
- **SOSPECHA**: los cuatro worktrees que reaparecieron a las 21:45 UTC (`beautiful-tu`, `determined-mcclintock`,
  `mystifying-hofstadter`, `serene-mclaren`) los recreó la app al archivar sesiones; están limpios y en commits del
  remoto, no se tocaron.
- **SIN VERIFICAR**: la primera sombra con datos y el monitor del 3 (ver la §7 del pre-mortem).

## e. Lo que ya está cerrado y no hay que rehacer

- El ensayo en seco de V750-B. **No repetirlo**; el 3 se corre con `--hasta 2026-11-02` y el `data/` de main del día.
- La verificación de D-43 contra main.
- La equivalencia de V750-A: VERDE en main; no volver a correr la copia de la rama.
- La lectura del A/B de MOD-D y su verificador (de S170).
- La revisión del token y de la preparación para el cese de Suomi NPP (#892, #897, #900).

## f. Prompt para la próxima sesión

```text
Retoma VRP Chile como sesión S172 (relevo de S171, cierre del 2026-10-31 ~23:15 UTC). Empieza con /retomar.
No empieces trabajo pesado antes del 2026-11-01 12:00 UTC (reinicio de la cuota semanal; mira
mcp__ccd_session_mgmt__get_usage antes de lanzar nada caro y di el costo).

1. cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"; git fetch origin --prune; git status -sb
   (rama loop/activo); date -u; df -h /c /d.
2. Lee tasks/BLOQUE_ARRANQUE_S172.md y las entradas S171 de tasks/LOOP_OBJETIVOS.md §6. Verifica contra el remoto
   loop/activo, la rama claude/s170-modd-f4-procedencia (25e3cc3ba) y el borrador
   experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md antes de creerle al bloque.
3. Sesión viva: VIIRS 750 local_94f4be0d-2b32-4570-b711-3a6f14cc8a0a. Dile que ahora reporta a S172.

Trabajo en orden:
- MODIS (decisión de Nicolás: se adelanta): completar las cotas A COMPLETAR del borrador desde el resultado del A/B de
  MOD-D (rama claude/s170-modd-f4-procedencia, experiments/_s168/modd_f4_candado/lectura_ab2/resultado_f4.json); comprobar
  en el lector sellado s170-v375e-lector si cambiar claves de MODIS en la sombra marca régimen nuevo en VIIRS 375;
  verificador limpio de otro modelo; frase de sello de Nicolás. Después: tag pre-s171-adopcion-modd, PR del encendido
  con la lista del §5 del borrador, y el sí de A45 de Nicolás antes del merge.
- 2026-11-02: audit semanal (puede abrir un issue duplicado de #915, 171-07); cese de Suomi NPP 13:00 UTC en CMR.
- 2026-11-03: V750-B (la sesión de VIIRS 750 tiene los comandos; el ensayo en seco ya salió limpio). Primera sombra con
  datos: llega ~19-20 UTC, no a las 15:00; mirar con la §7 de D:/vrp-trabajo/temporales/audit_s171_dia3/INFORME.md y no
  despachar a mano antes de las 22:00 UTC.
- V750-A: la sesión de VIIRS 750 escribe la vara MATLAB directo en el §4.1 y §7.1 (decisión de Nicolás) y cierra
  VS171-01 a 05 antes del sello.

Reglas duras: pipeline/ congelado durante la sombra (excepciones: ROI de V750, emergencias del NRT y el encendido de
MODIS ya decidido, anotado como excepción); nada en pipeline/, data/ ni frontend/ sin tag y sí de Nicolás (A45); merge a
main sólo con frase de Nicolás y gh pr merge --match-head-commit <sha>; sólo EARTHDATA_TOKEN (A71); despachos de a uno
desde tags; verificador limpio de otro modelo antes de aceptar un resultado; antes de correr un instrumento, sha256 de
cada archivo contra su ref; máximo 2 procesos pesados locales con parada bajo 3 GB; temporales en D:; git add por
archivo; nunca git stash; date -u antes de cada encabezado de bitácora; español de Chile sin voseo ni guiones largos;
rutas absolutas. Si el contexto pasa el 50 %: commitea, anota qué quedó corriendo y cierra con /cierre.
```
