# Bloque de arranque S171 (cierre de la sesión S170, 2026-10-31 ~18:10 UTC)

> **Estado fijado sin trabajo en curso**: 0 procesos Python (`Get-CimInstance Win32_Process`, 18:09 UTC), las
> sesiones MOD-D (`local_5b198297`) y V750 (`local_94f4be0d`) quietas. `loop/activo` local = remoto = `3ed3a3443`
> antes del commit de este cierre. Cuota semanal al 94 %, se reinicia el **domingo 2026-11-01 12:00 UTC**.
> Bitácora detallada: `tasks/LOOP_OBJETIVOS.md` §6, entradas de S170 (02:24 a 17:29 UTC del 2026-10-31).

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| **MOD-D (MODIS): A/B leído** | **PROPONER ADOPCIÓN** (§7 fila 6), 14 controles OK. P1 sin pérdida; P2 GANA (neto −44, B 53, s_K 52, s_V 8, p 1/10001); M MEJORA (n 83); razón V/MIROVA 0,983 en 56 protegidas; Chillán resuelto. **Verificador limpio: LECTURA CONFIRMADA** (cifras propias idénticas; sin PCC sigue GANA, neto −12) | rama `claude/s170-modd-f4-procedencia` `e0bb1b150`; tag de lectura `s170-modd-f4-lectura` (`e27dc2e49`); `D:/vrp-trabajo/temporales/ver_s170_lectura/INFORME.md` |
| MOD-D runner | humo verde al 2.º intento; t1, t2 y t3 verdes: 5.709 filas, 5.321 identidades iguales | runs 41164864021, 41166033637, 41168080181, 41169884696; tag `s170-modd-f4-candado` (`d65fd231d`) |
| MOD-D adenda N-01 | sellada: 45 `escena_invalida` con acuerdo runner-censo dejaban INDECIDIBLE; mutaciones 95 de 95; dos verificadores | tag `s170-modd-f4-candado-n01` (`a7bd7562e`); `ver_s170_adenda/`, `ver_s170_adenda2/` |
| MOD-D procedencia | primera lectura INDECIDIBLE sólo por procedencia (cabeceras con el tag del runner); arreglo mecánico (descendencia más 18 archivos del runner sin cambio, guarda por gancho «open»), 32 de 32 mutaciones, verificador | `procedencia_runner.py` en `e27dc2e49`; `ver_s170_procedencia/` |
| PR a main | **#929** (falso rojo MODIS de la sombra, VR3-01 a 04) `3257db062`; **#930** (yml del humo) `2e9fa2cba`; **#931** (`--force` al bajar el tag) `d2eb4268e`. Los tres con frase de Nicolás | `gh pr view` |
| V375-E lector | **sellado y aprobado por Nicolás**: batería 233 de 233; nulo 129 de 138 más N19, V07b y V07c atrapadas con las pruebas VS170-LEC-01 a 03; M22 equivalente | tag `s170-v375e-lector` (`3ab4b943d`); `ver_s170_lector/INFORME.md` |
| V750-A evaluador | medidor 85 de 85 atrapadas; regla N-3 implementada (E77 a E80), mutaciones M86 a M95 atrapadas; **sin tag** | rama `claude/s162-viirs750-2-918174` `296f55b70`; `D:/vrp-trabajo/temporales/medidor_todo5.log`, `medidor_n3.log` |
| #915 | abierto a propósito, comentado y enlazado a MOD-D, V750 y V375-E | comentario 6542341838 |
| `main` | `fcc5611fd` | `git ls-remote` 18:09 UTC |
| Disco | C: 24 GB, D: 14 GB | `df -h` |

## b. Decisiones que espera el dueño

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Encender la vía de MIROVA en MODIS en producción (resultado de MOD-D) | ahora como excepción / en la parada de la sombra / no | **En la parada de la sombra o en una ventana planificada**: `pipeline/` está congelado (§12.6) y el encendido pide tag defensivo y A45. Antes, leer el INFORME de MOD-D y el del verificador; el «BORRADOR» que quedó escrito en §8.2 y §13 del tag se corrige en un commit de texto |
| 2 | Sello de V750-A | tras V750-B (ROI), con verificador / antes | **Tras V750-B** del 2026-11-03: el pre-registro (§11) pide incorporar la ROI elegida |
| 3 | Cerrar #915 | ahora / cuando decidan las lecturas | **Cuando decidan**: lo que marca es real (recall MODIS 62,5 %, VIIRS 750 74 %) |

## c. Lo aprendido

Proyecto (a `docs/META_RULES_S80.md` en la próxima revisión; memoria `feedback_s170_tres_fallas_de_montaje`):
- **Un yml que baja tags se ensaya en el runner desde un tag de prueba antes del humo.** El fetch del tag anotado
  chocó con el checkout (run 41163955456); sólo existe en el runner.
- **El control de identidad del evaluador se corre con el censo contra sí mismo antes de sellar.** N-01 se descubrió
  con t1 y obligó a una adenda después de correr.
- **Una adenda que cambia el tag de lectura resuelve la procedencia en el mismo sello.** La primera lectura salió
  INDECIDIBLE por eso; ni el autor ni dos verificadores lo vieron.
- **Todo arnés de mutaciones se detiene solo con C: o D: bajo 3 GB, y escribe por mutación.** El primer nulo del
  lector dio 135 caídas sin mensaje con C: lleno; se repitió.
- **Una lista de dependencias del runner se deriva rastreando lo que se abre, no de memoria**: faltaban 6 entradas
  (cuatro carpetas `_s151` cargadas por ruta y dos de `evaluar_d25`); la guarda por gancho «open» las encontró.

Regla general del workspace:
- **El verificador limpio encontró algo en 6 de 7 revisiones de S170** (sólo la del humo salió limpia). Vale su costo
  aun con la cuota alta; acotarlo a una pregunta y un modelo distinto del autor lo hace barato (~2 % del plan cada uno).
- **Al ir a dormir, Nicolás autoriza por adelantado con condiciones** («si X y un verificador lo confirma, despacha»).
  Funcionó: t1 a t3 corrieron de noche sin preguntar.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO**: la vía de MIROVA gana a K en MODIS según el pre-registro sellado (lectura y verificador).
- **CONFIRMADO**: las tres tandas, el humo y los dos PR de workflow corrieron sobre el commit del tag.
- **SOSPECHA**: la causa del primer nulo inválido del lector fue el disco (C: 2,5 GB); no se probó.
- **SIN VERIFICAR**: el juicio por día de la sombra y el issue del monitor con datos reales (primera corrida
  2026-11-03 15:00 UTC); el cese de Suomi NPP en CMR (2026-11-02 13:00 UTC).
- **SIN VERIFICAR** (verificador de la lectura): contenido de la referencia y de `externos_referencia.json`, apoyados
  en sus controles OK.

## e. Lo que ya está cerrado y no hay que rehacer

- La lectura del A/B de MOD-D y su verificador. **No releer ni re-correr t1 a t3.**
- La adenda N-01 y el arreglo de procedencia, con sus verificadores.
- El lector de V375-E: sellado y aprobado; no editar.
- VR3-01 a VR3-04 de la revisión de la sombra (#929).
- El medidor de V750-A (85 de 85) y las mutaciones de N-3.

## f. Prompt para la próxima sesión

```text
Retoma VRP Chile como sesión S171 (relevo de S170, cierre del 2026-10-31 ~18:10 UTC). Empieza con /retomar.

1. cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"; git fetch origin --prune; git status -sb
   (rama loop/activo); date -u; df -h /c /d; mcp__ccd_session_mgmt__get_usage (la cuota se reinicia el domingo
   2026-11-01 12:00 UTC).
2. Lee tasks/BLOQUE_ARRANQUE_S171.md y las entradas S170 de tasks/LOOP_OBJETIVOS.md §6. Verifica contra el remoto los
   tags s170-modd-f4-lectura, s170-v375e-lector y la rama claude/s170-modd-f4-procedencia (e0bb1b150) antes de
   creerle al bloque.
3. Sesiones vivas: MOD-D local_5b198297-ad3f-4aca-850a-c5dd3d856b80, V750 local_94f4be0d-2b32-4570-b711-3a6f14cc8a0a.
   Diles que ahora reportan a S171 (tu id).

Trabajo en orden:
- Llevarle a Nicolás la decisión de encender la vía de MIROVA en MODIS (MOD-D: PROPONER ADOPCIÓN confirmado); recomendar
  hacerlo en la parada de la sombra o en una ventana planificada, con tag defensivo (A45). Corregir el «BORRADOR» del
  §8.2 y §13 del pre-registro con un commit de texto en la rama de MOD-D.
- 2026-11-02: audit semanal; #915 queda abierto; comprobar el cese de Suomi NPP (13:00 UTC) en CMR.
- 2026-11-03: V750-B con experiments/_s162_v750b/r4/INFORME.md §3 y §4 (unset VRP_PROFILE con eco, control previo con
  el data/ de main del día, despacho desde tag); a las 15:00 UTC, primera sombra con datos: revisar el run, el commit
  en data/sombra_codigo_mirova/, la línea por volcán y sensor y el monitor (18:30 UTC). Con la ROI elegida: PR de
  roi_v750 en la rama s169-roi-v750 y frase de Nicolás; luego sello de V750-A con verificador.
- V375-E: con datos de la sombra, correr el lector sellado (s170-v375e-lector) sin editarlo; decide en la parada
  (30 noches y 40 alertas).
- Pasar las lecciones de S170 a docs/META_RULES_S80.md.

Reglas duras: pipeline/ congelado durante la sombra (§12.6; excepciones ROI de V750 y emergencias del NRT); nada en
pipeline/, data/ ni frontend/ sin tag y sí de Nicolás (A45); merge a main sólo con frase de Nicolás y
gh pr merge --match-head-commit <sha>; sólo EARTHDATA_TOKEN (A71); despachos de a uno desde tags; verificador limpio
de otro modelo antes de aceptar un resultado; máximo 2 procesos pesados locales con parada bajo 3 GB; temporales en
D:; git add por archivo; nunca git stash; date -u antes de cada encabezado de bitácora; español de Chile sin voseo ni
guiones largos; rutas absolutas. Si el contexto pasa el 50 %: commitea, anota qué quedó corriendo y cierra con /cierre.
```
