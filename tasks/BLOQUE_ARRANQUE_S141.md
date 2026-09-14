# Bloque de arranque S141

> Cierre de S140 (2026-09-14, 14:45 a 16:03 UTC, hora del servidor). Rama `main` en `ac96d0312`,
> verificado igual al remoto con `git ls-remote`. Suite **1373 passed**, 4 skipped, 2 xfailed (corrida
> al cerrar, sobre `main`). Sin PR abiertos, sin tareas en segundo plano, un solo worktree, los 4
> stashes de S72 a S78 intactos. Los commits del cron NRT y del sync seguirán aterrizando sobre
> `data/`; no invalidan nada. Sin trabajo en vuelo al fijar el estado.
> **Ojo:** el último NRT corrió a las 09:34 UTC, **antes** de los merges de la 8b, 8d y 7: ninguno de
> esos cambios corrió todavía en producción.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| T1 loader OCR: distancia con mojibake (`â‰ˆ`) | **mergeado** | #652; sin distancia 578 → 21 de 846 (las 21 no la traen) |
| T2 referencia unificada (consolidado + OCR + respaldo 8-abr, con RUTINA y FP) | **mergeado** | #653; `scripts/referencia_mirova_unificada.py`; 244 pasadas del respaldo, **17** ALERTA (no 18) |
| T3 banco de paridad por pasada | **mergeado** | #654; `scripts/banco_paridad.py`; V375 publica en 63,7 % de negativos limpios (S139: 63,5 %) |
| T4 descomposición de magnitud contra OSF | **mergeado** | #655; `scripts/descomponer_magnitud_osf.py`; R_gm 0,659 = F_n 0,553 × F_ex 1,192, idéntico a S139 |
| T5 línea base congelada | **mergeado** | #657; `data/audit_continuous/linea_base_s139/` (main 04c25f34, index 24fba8a1, Mirova-v1 500cf715) |
| T6 auto-audit mide falsas publicaciones, **sin alarma** | **mergeado y corrió en CI** | #658; `latest.json` del 14-sep: V375 62,9 %, V750 22,9 %, MODIS 11,2 % |
| T9 docs: cita del ETI fabricada, A95, D17/D20/D25/D26, README artefactos | **mergeado** | #656 |
| T8b MODIS NRT se etiquetaba "standard" | **mergeado, no corrió aún** | #659; detector en `pipeline/product_version.py`; Láscar: 0 de 4.679 records con MODIS "nrt" |
| T8c aviso de vencimiento del EARTHDATA_TOKEN | **mergeado, no corrió aún** | #660; `scripts/token_edad.py` lee `exp` del JWT; healthcheck diario 12:00 UTC |
| T8d host NASA caído visible en Actions | **mergeado, no corrió aún** | #662; `::warning::` por host + conteo en resumen |
| T7 radiancia de fondo persistida | **mergeado, no corrió aún** | #663; `diag_L_bg_w_m2_sr_um`, `diag_n_bg_anillo`, `diag_L_bg_local_w_m2_sr_um` |
| T8a quitar perfil experimental del cron | **pospuesto por Nicolás** | corre 19 de 38 min del job (Láscar 09:34) y su salida se pierde |
| T10 segunda lectura de papers | **no iniciada** | plan tarea 10 |
| T11 correcciones heredadas | nota D26 hecha (#656); bullet del foco TIF **no aplica** (el banco no usa TIF); los otros dos son reglas ya respetadas | plan tarea 11 |
| Tags defensivos | subidos | `pre-s140-f0-loader-ocr`, `pre-s140-f0-nrt`, `pre-s140-f0-lbg-persistido` |
| Salidas locales sin commitear | `experiments/_s140/` (banco y magnitud de trabajo, `_dl_referencia` ignorado) | regenerables; la foto oficial es la línea base |

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Correo a Coppola (borrador `docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`) | enviar · recortar a 1-5 · no enviar | **enviar**; las preguntas 1 a 5 bloquean los A/B de la Fase 1 |
| 2 | Token Earthdata (vence ~2026-10-03 según S139, no verificado) | renovar ya · esperar el issue del healthcheck | **renovar esta semana**; el issue automático recién avisa con 10 días |
| 3 | Records MODIS históricos NRT etiquetados "standard" (bug de la 8b) | re-etiquetar desde el campo `granule` · dejar | **re-etiquetar con script + tag**, sin reprocesar: el nombre del granule guardado basta. Antes, verificar que el auto-upgrade de `store.py` realmente corre (SOSPECHA abajo) |
| 4 | Issue semanal FUERA_DE_BANDA (#661) por magnitud Isluga 0,54 y Láscar 0,43 | agregar a `UNDER_BAND_KNOWN` con referencia al plan · dejar | **agregar como conocido hasta la Fase 1**, igual que Lastarria: un issue que sale todas las semanas por lo mismo deja de leerse |
| 5 | T8a perfil experimental en el cron | quitar · commitear su carpeta | **quitar** cuando lo decidas; ahorra la mitad del job |
| 6 | Umbrales de terminado (spec §2: falsas ≤ 10 % focales / 15 % nevados; magnitud [0,8; 1,25]) | congelar ahora · revisar | **congelar ahora**: la spec dice "al cerrar la Fase 0" y sólo falta T10, que no los mueve |
| 7 | T10 con subagentes (lectura renderizada de ~20 PDF) | fan-out de lectores + verificador · serie en una sesión | **fan-out chico** (4 lectores por prioridad + 1 verificador), escala pre-acordada (feedback S120) |
| 8 | Script reusable de remapeo de citas `file:line` | crear `scripts/remapear_citas.py` con test · seguir con script ad hoc | **crearlo**: esta sesión lo escribió dos veces a mano |

## c. Lo aprendido

**Reglas generales del workspace** (proponer para `GUIA_MAESTRA_AUDITORIAS.md` §7 o la guía de credenciales):

1. **Un plan escrito en una sesión y ejecutado en otra trae instrucciones que no funcionan.** De 11 tareas, 6 tenían algo roto: un test que pasaba sin el cambio (Láscar existía por OCR), una función que no existe (`evaluar`), un import que arrastraba credenciales, una fecha que no era la de vencimiento, una comparación contra un valor redondeado, y una afirmación sin fuente ("μ/σ como m/s"). Regla: antes de implementar cada paso, correr su test y confirmar que falla **por la razón que dice**, y leer lo que cita.
2. **El vencimiento de una credencial se lee del token, no de cuándo se guardó.** Un JWT trae `exp`; `updated_at` de un secret es la fecha en que alguien lo pegó.
3. **Una función pura que vive en un módulo con efectos al importar (red, `.env`) se muda a un módulo liviano antes de importarla desde otro lado**, y el módulo original la reexporta.
4. **Un parche por script dentro de un heredoc puede convertir `\n` en salto real.** Importar o compilar el archivo inmediatamente después del parche, en el mismo comando.
5. **Una llamada de merge por API que corta por red no dice si mergeó.** Consultar el estado antes de reintentar.

**Propias del proyecto** (van a `CLAUDE.md` en la próxima revisión, junto con A97 a A100 que S139 dejó propuestas):

- **A101 (propuesta)**: agregar una línea a un procesador corre citas `file:line` en tres lugares (contrato G8, `CLAUDE.md`, `MIROVA_DIVERGENCES.md`). Se remapean **por contenido** con `difflib` contra `origin/main`, aceptando sólo líneas en bloques idénticos; nunca por aritmética (la 7 corrió 1, 2 y 3 líneas según la zona) y nunca las citas históricas deliberadas (A6, A49).
- **A102 (propuesta)**: MODIS y VIIRS marcan NRT distinto (`.NRT.` contra `_NRT`, A37). Arreglar el detector (S133) no arregló a sus llamadores: la expresión vieja siguió en los tres procesadores un mes. Al corregir una función, buscar también las **copias en línea** de su lógica.

## d. Problemas abiertos e hipótesis

### CONFIRMADO (verificado con herramienta en S140)

- Banco y magnitud reproducen S139 con otro código y otra referencia (tabla §a).
- Láscar: 0 de 4.679 records con sensor MODIS y `product_version = "nrt"`, al 14-sep (antes de #659).
- La ecuación (5) impresa de SP426.5 (p. 5) es la de NTIbk; el ETI sólo aparece en rótulos de Fig. 3 y 4 (p. 7 y 8), renderizadas.
- Fernandina 2025 p. 6: MIROVA usa B21, B22 y **B31** (TIR) de MODIS; p. 9: grilla UTM 51 × 51 km en la cumbre GVP y fondo = promedio de vecinos no alertados. Renderizadas.
- Coppola 2014 (IJRS p. 3409): test 2 con `and` explícito (algoritmo de Stromboli, no SP426.5).
- El perfil experimental corre en el cron: 19 de 38 min del job de Láscar a las 09:34 UTC.
- El issue #661 lo abrió el cron del lunes (`schedule`, 15:44 UTC), no un merge; sus flags son la magnitud de Isluga y Láscar.
- T6 corrió en GitHub: `latest.json` trae el bloque `falsas_publicaciones` con valores.
- Último NRT a las 09:34 UTC, anterior a #659, #662 y #663.

### SOSPECHA (no verificado)

- Que el `exp` del token real sea legible: lo dirá el healthcheck del 15-sep 12:00 UTC (resumen del job).
- Que los campos de la T7 salgan bien en un record real: primer NRT después de `ac96d0312`.
- Que el auto-upgrade NRT a Standard de `store.py` corra de verdad para MODIS una vez bien etiquetado (no se miró el cron que lo dispara).
- Que el issue de magnitud salga todas las semanas desde S124 (sólo se vio el del 14-sep).
- La fecha de vencimiento ~2026-10-03 del token (viene de S139).

## e. Cerrado en esta sesión, no rehacer

1. Tareas 1 a 9 de la Fase 0 salvo la 8a (pospuesta) y la 10 (no iniciada). No relanzar sus scripts salvo para medir algo nuevo; la foto está en la línea base.
2. **"El auto-audit debe alarmar por falsas publicaciones"**: decidido que no hasta la Fase 1 (Nicolás, 14-sep).
3. **`diag_n_suitable`** se llama `diag_n_bg_anillo` (renombre aceptado).
4. **Dónde vive el detector de producto**: `pipeline/product_version.py`; `fetch.py` lo reexporta.
5. **Cómo se avisa el vencimiento del token**: por `exp` del JWT en el healthcheck, issue por transición.
6. **D20**: verificada contra Fernandina 2025; no reabrir la banda TIR de MODIS.
7. **Cita del ETI**: corregida; el paper no escribe esa ecuación.
8. **El banco no usa TIF**: el bullet 1 de la T11 no aplica.

## f. Prompt para la próxima sesión

```
Retomo VRP Chile en S141. Antes de creerle a nada, verifica el estado real:

  cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
  git fetch origin --prune && git pull --ff-only
  python -m pytest tests/ -q --no-header --tb=line -p no:cacheprovider | tail -1   # esperado: 1373 passed
  gh api repos/MendozaVolcanic/VRP-chile -i 2>/dev/null | grep -i "^date:"          # A86: hora del servidor
  gh run list --workflow=nrt.yml --limit 3                                          # NRT vivo y posterior a ac96d0312?
  gh run list --workflow=nrt-healthcheck.yml --limit 1                              # leer el resumen: estado del token

Lee en este orden, comprobando contra el codigo de hoy lo que afirme:
  1. tasks/BLOQUE_ARRANQUE_S141.md                                         <- este archivo (decisiones §b)
  2. docs/superpowers/plans/2026-09-14-fase0-instrumento-paridad.md        <- tareas 10 y 11
  3. docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md   <- §2 (terminado) y Fase 1
  4. data/audit_continuous/linea_base_s139/README.md                        <- la foto contra la que se mide

TRABAJO, en este orden:
  1. Verificar en produccion lo mergeado sin correr: en el primer record NRT posterior a ac96d0312,
     que existan diag_L_bg_w_m2_sr_um / diag_n_bg_anillo / diag_L_bg_local_w_m2_sr_um con valores
     sanos, y que MODIS NRT quede product_version "nrt". Leer el resumen del healthcheck (token).
  2. Preguntar a Nicolas las decisiones §b (correo, token, re-etiquetar MODIS, issue semanal, umbrales).
  3. Tarea 10 (papers del grupo MIROVA, renderizando paginas) con escala pre-acordada.
  4. Si Nicolas decide: re-etiquetado MODIS (script + tag + A45), UNDER_BAND_KNOWN, T8a.

REGLAS DURAS:
  - Manda la PARIDAD POR SENSOR; la fidelidad literal decide solo entre brazos que empatan.
  - Toda metrica lleva NEGATIVOS; por pasada y por noche de volcan, por volcan, con ventana y denominador.
  - Referencia = scripts/referencia_mirova_unificada.py (remoto de Mirova-v1 con sha + respaldo 8-abr).
    NUNCA load_mirova_alertas para medir paridad. OSF = solo definiciones por fila.
  - Formulas de papers: renderizar la pagina y mirarla. Ni .txt ni capa de texto.
  - Tocar pipeline/, store.py, nrt.yml o el perfil: tag defensivo + confirmacion de Nicolas (A45).
  - Insertar lineas en un procesador: remapear citas file:line por contenido (difflib contra origin/main)
    en el contrato G8, CLAUDE.md y MIROVA_DIVERGENCES; nunca las historicas.
  - Antes de implementar un paso de un plan: su test debe fallar por la razon que dice.
  - Nunca keep_peak apagado solo. Nunca banda 22 sola.
  - NADA de guiones largos ni medios. Espanol de Chile, formas de tu. Fenomeno fisico primero.

SI LA SESION NO ALCANZA: /cierre. Lo que quede a medias va commiteado con su README diciendo que falta.
```

---

## Histórico: bloque S140 (cierre de S139)

Se conserva íntegro en `tasks/BLOQUE_ARRANQUE_S140.md`. Lo que ese bloque daba por hecho y S140 corrigió:
(1) "18 ALERTAS faltan en el consolidado": son **17** contra el respaldo del 8-abr (las 244 pasadas
faltantes son 221 RUTINA, 17 ALERTA y 6 FALSO_POSITIVO). (2) El plan de la Fase 0 tenía seis
instrucciones que no funcionaban tal como estaban escritas (§c regla 1). (3) La sospecha de D20
(MODIS TIR banda 31) quedó **verificada** en Fernandina 2025 p. 6. (4) El `experimental` "escribe en
una carpeta que no se commitea": confirmado y medido (19 de 38 min). (5) Decisiones 3 (8a), 4 (A45 de
7 y 8) y 6 del bloque S140: la 4 se resolvió (autorizadas y mergeadas), la 3 quedó pospuesta, la 6
sigue abierta.
