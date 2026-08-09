# AUDITORÍA INTEGRAL S122 (protocolo A51) — 7 ejes en paralelo

> Fecha: 2026-08-02. 7 subagentes read-only (misión/fidelidad · operacional NRT · docs/memoria ·
> frontend · git/repo · ground truth · seguridad+tests). Los hallazgos load-bearing fueron
> **re-verificados por el orquestador** con file:line o comando propio (A48: los subagentes
> pueden malinterpretar convenciones). Los no verificados se marcan como tales.
>
> **Nota de método**: durante la auditoría se detectó que el worktree local estaba **341 commits
> atrás** de `origin/main` (A25/A52 en vivo). Se actualizó y se **re-corrieron** los análisis de
> la sesión (Paso 0 D12 y cross-validation AVTOD) sobre data fresca: conclusiones intactas.

## ✅ P0 — RESUELTO el 2026-08-04 *(era: NRT caído ~2 semanas por token NASA expirado)*

> **Addendum de cierre — 2026-08-09 (S123).** Verificado contra el remote (`gh api`, nunca contra
> el checkout local). **La ingesta térmica propia se recuperó y la serie quedó sin hueco.**
> El cuerpo original de este P0 se conserva abajo como registro de lo que se sabía el 02-ago.
>
> | Qué | Evidencia (remote) |
> |---|---|
> | NRT verde de nuevo | `nrt.yml` run **1135 = último `failure`** (04-ago 06:26 UTC); **1136 en adelante `success`** (04-ago 10:37 UTC) — 5 días corridos sin fallos |
> | Ingesta viva hoy | Commits `NRT update` del **09-ago** para 10 de los 11 Tier A (Copahue, NdC, Chaitén, Villarrica, PCC, Lastarria, Planchón, Isluga, Láscar, Tupungatito). Llaima: último 08-ago 21:28 — dentro de cadencia, no es stale |
> | **Serie sin hueco** | El backfill previsto en "Acciones (2)" **se ejecutó**: `data(backfill): Copahue 2026-07-21..2026-08-02 (S120)` el 04-ago 08:33, más `data(geometry)` S122. El hueco 21-jul → 02-ago quedó relleno; el NRT normal retoma el 04-ago 11:42 |
> | Frescura Tier A | El healthcheck A58 **dejó de reportar stale** tras el 04-ago 13:44 (último comentario en #498) |
>
> **Alcance real de la caída**: 23-jul → 04-ago = **13 días, 107 runs fallidos** (no 9 días/81).
> La ventana 26-jul–04-ago da exactamente 81; los 26 fallos del 23, 24 y 25 de julio quedaron
> fuera de esa ventana. El primer fallo cae el 23-jul porque A57 dispara a las 72 h del último
> dato bueno (20-jul).
>
> **Lo que sigue abierto de este P0** (no lo cierra la recuperación):
> - **Acción (3)** — distinguir credencial-muerta de host-caído en `fetch.py` y abortar: *sin
>   verificar en esta sesión*. La causa raíz del retraso en detectar sigue en pie.
> - **Acción (4)** — canal de notificación: ver el diseño de escalonamiento de S123. El problema
>   no fue falta de alerta sino **exceso**: ~9 correos/día por 13 días entrenan a ignorarlos.
> - **Higiene de issues**: **#498** (`nrt-stale`) sigue **abierto** pese a que el sistema se
>   recuperó el 04-ago, y **#336** (`nrt-alert`) sigue abierto **desde el 04-jun** con 58
>   comentarios. Ningún canal emite señal de *recuperación*, así que los issues quedan en rojo
>   permanente y pierden valor como semáforo.

<details>
<summary>Cuerpo original del P0, tal como se escribió el 2026-08-02 (registro histórico)</summary>

**Verificado por el orquestador** en el log del run 30771155452 (job 91558429689):

```
[diag] AUTH_OK
WARN: Failed to fetch MODIS_TERRA: {"errors":["Token [***] has expired..."]}
```

…para los **8 sensores**, en cada volcán, en cada corrida.

- Último dato producido: **2026-07-20**. Hoy 2026-08-02 → **~13 días de hueco**.
- `nrt.yml`: **100% de fallos** desde 2026-07-23 (verificado: 8/8 últimos runs `failure`).
- Entre 07-18 y 07-22 los runs salieron **"verdes" sin commitear dato** → patrón zombie de manual.
- El dashboard que consume SERNAGEOMIN está congelado en data de hace dos semanas.

**Causa del retraso en detectarlo — el problema de diseño real**: el pipeline trata el error de
credencial como una caída transitoria de NASA (`WARN`, sigue, exit 0). El probe imprime `AUTH_OK`
porque valida que el token **exista**, no que **sirva** (no lo contrasta contra CMR). Un host caído
es transitorio y degradar con gracia es correcto (A64); **una credencial muerta es permanente y
debe abortar con exit≠0**. Los detectores SÍ funcionaron: el guard A57 hace fallar el workflow y
el healthcheck abrió el issue **#498 el 22-jul** — pero quedó 11 días sin que nadie lo viera.

**Acciones**: (1) Nicolás regenera el token en `urs.earthdata.nasa.gov` y actualiza el secret
`EARTHDATA_TOKEN` (Claude NO toca credenciales); (2) backfill de los ~14 días; (3) **fix de
diseño**: distinguir credencial-muerta de host-caído en `fetch.py` y abortar; (4) canal de
notificación que Nicolás vea (el issue solo no alcanzó).

</details>

## P1 — Desempeño: la pérdida de MODIS es de ETIQUETA, no de detección (GT fresco)

Ground truth CONS∪OCR, ventana válida 2026-01-10..07-20, `pc.vrp_mw` (A10), alias A14 resueltos:

| Sensor | n | recall dashboard | **recall al cráter** | precisión | ratio med |
|---|---|---|---|---|---|
| MODIS | 81 | **12.3%** | **97.5%** | 2.9% | 0.75 |
| VIIRS750 | 215 | 80.0% | 80.0% | 15.8% | 0.81 |
| VIIRS375 | 778 | 92.4% | 92.4% | 43.0% | 0.68 |

Ventana 90 d: VIIRS375 98.0% · VIIRS750 84.5% · MODIS cráter ~100% → **coincide con lo declarado
en S119** (98.4/84.5/100): sin drift de recall. La precisión no está declarada en ningún doc
reciente (no hay contra qué medir drift); y por A54 ~95% de esos "FP" son anomalías físicamente
reales sub-umbral que MIROVA no publica — no leerlos como error.

**Hallazgo:** el pipeline **encuentra el cráter en MODIS el 97.5% de las veces** pero el dashboard
solo muestra 12.3%: los 71 FN tienen VRP MIROVA **mediana 1.06 MW** (38/71 sobre 1 MW) → **no es
señal sub-umbral, es el bug de etiquetado A46/A82 far→summit**. Esto cuantifica con GT fresco el
costo de D12 (ver §D12 abajo).

**VIIRS750 es el eslabón débil real**: Tupungatito 46% recall *y* 7.47× de magnitud, PP 43%,
Isluga 66%. Modo mixto (sub-umbral + inflación en régimen glaciar/multicráter, A19/A22). Los FN de
VIIRS375 sí son puramente sub-umbral (mediana 0.22 MW) → benignos.

## P1 — Frontend: divergencias reales entre las 3 vistas

**Verificado file:line por el orquestador:**
- **`diario.html:243` no tiene el cap de sanidad** que sí tienen `index.html:981` y `mosaico.html:250`
  (`vfb > 50000 ? 0 : vfb`), ni el fallback `?? r.vrp_mir_mw`. Un fósil pre-S41 (el PP de 695.431 MW)
  se **grafica en diario** y se anula en las otras dos. Peor: el comentario `index.html:977` afirma
  *"paridad sanity cap con diario.html:237"* — **es falso**.
- `_mirova_confirmed` (cinturón anti-artefacto) solo se puebla en index → el mismo record es visible
  en index y se oculta como artefacto en diario/mosaico.
- En index el filtro de artefacto vive **fuera** del punto de display (en cada call-site), no dentro
  del helper → cualquier panel nuevo nace sin la supresión cirrus/difuso.
- `beyond-mirova.html:391` apunta a `data/_s99_test1_eq16/` **purgado en S121** → panel Eq.16 muerto
  en silencio; y `:231` carga el JSON completo (13-17 MB), la regresión de peso que S121 ya arregló
  en las otras vistas.

## P2 — Estructural: `.git` crece 13.5 MB/día y la poda S121 no lo frena

Medido: `.git` **3.1 GB** local / 3.58 GB en GitHub. El *working tree* quedó estable tras la poda
(+0.23 MB/día → no vuelve al tamaño pre-poda), pero **la historia** suma **~13.5 MB/día** reales
(1.905 blobs / 16.2 días, con delta-compresión) → **+4.9 GB/año → ~8 GB en 12 meses**. Ya bloqueó
la red una vez (disco 98%, S121). Causa: cada corrida NRT reescribe JSON monolíticos de 20-30 MB
completos. El `filter-repo` diseñado ataca el pasado; **sin cambiar la arquitectura de escritura**
(particionar por año/mes, o sacar `data/` del repo) el problema se regenera.

## P2 — Fidelidad: conmutación de método POR VOLCÁN, viva en el operacional

**Verificado**: `volcanoes.yaml` tiene `local_kernel_bg: true` en 5 volcanes y
`lbg_global_compatible: true` en 3; los gates están en `process_modis.py:887`,
`process_viirs.py:1178`, `test1_integrated.py:141-147`. Pero `MISSION.md:74-79` establece que
MIROVA NRT es **un algoritmo por SENSOR, uniforme entre volcanes**, y que *"NO conmuta de método
por volcán ni por régimen térmico"* — que es **exactamente el criterio por el que se rechazó Eq.16
en S99**. Aplicamos la regla para rechazar lo nuevo, pero tres flags preexistentes la violan.
Contradicción viva, sin resolver, no listada en los anti-patrones de MISSION.

Relacionado (MEDIA): `path_d_only_cap_tbg_max_k: 270.0` sigue activo como gate de magnitud
condicionado por `t_bg` (`process_modis.py:844-849`), mientras `MIROVA_DIVERGENCES.md:515-519`
declara que *"el candidato t_bg-gate quedó descartado (anti-MIROVA + trap A68/A80)"*. La distinción
detección-vs-magnitud es defendible, pero el doc no la explicita.

## P2 — Punteros de estado contradictorios (la enfermedad que ya costó ~70 sesiones)

**Verificado**: `CLAUDE.md:1165` lista *"abiertas: D2, D3, D9, D11"* — pero `MIROVA_DIVERGENCES.md:1232`
dice **D11 CERRADA S114**, D9 está resuelta desde S113, y **omite D12**, que sí está abierta
(`:1334`) y es el frente activo de S122. Y el puntero de "última auditoría" apunta a **tres docs
distintos**: `INDEX.md:11` y `CLAUDE.md:1164` → AUDIT_S105; `MEMORY.md` → AUDIT_S119; real →
AUDIT_S121. Una sesión fría arranca 16 sesiones atrás.

Además: `docs/INDEX.md` congelado en S105 → **24 docs invisibles**, incluidos todos los audits
S106-S122. `CLAUDE.md:994` manda clonar workflows que fueron movidos a `_archive/`.
`MEMORY.md` sin filas para S120-S122. Docs huérfanos: **0**.

## P3 — Cobertura de tests: el ensamblado no tiene red

Suite **806/806 verde** (verificado tras el pull). Cobertura total 57%, pero desigual: los helpers
extraídos están protegidos (`scan_geometry` 100%, `store` 95%, anchor/clustering 98-100%) mientras
los orquestadores no: `process_viirs_mod.calculate_vrp` **7%**, `process_viirs` **14%**,
`process_modis` **43%**. Es decir, **el camino granule→record no tiene test de regresión** — justo
donde vivieron A49 (`compute_bg_stats` con el `return` comido) y A46 (hotspot↔cluster).

## P3 — Seguridad: limpia (sin acción urgente)

0 credenciales en árbol y **0 archivos de credenciales jamás commiteados** (historial verificado
con `-S`/`--diff-filter=A` sobre rutas de código; no exhaustivo sobre blobs de `data/`). Secrets solo
vía `env:`, sin `pull_request_target`, permisos declarados y razonables. Gaps menores: `.netrc` no
está en `.gitignore` (una línea gratis); `audit-weekly.yml:13` declara `contents: write` a nivel
workflow — revisar si lo necesita.

## Higiene menor
`scripts/compact_anomaly_pixels.py:24-27` apunta a directorios purgados en S121 → no-op silencioso ·
52 de 117 ramas remotas ya mergeadas sin borrar · TIF trackeados en `Pruebas/` y `kmz/` pese a estar
ignorados · workflow fantasma `reproc-f28-pp-saturation.yml` registrado pero sin archivo.

## Estado de D12 tras esta auditoría

El Paso 0 (`AUDIT_S122_C2_PASO0.md`) mostró que **C2 no es viable** (el blob path-D no tiene núcleo;
peak-of-kernel colapsa por igual la cura de Láscar y el artefacto de PCC). El eje 6 **cuantifica el
costo de no arreglarlo**: 71 FN MODIS con mediana 1.06 MW que NO son sub-umbral, sino mal
etiquetados. Ambas cosas son ciertas a la vez: la cura es valiosa y no hay separador conocido a
1 km. La cobertura práctica sigue siendo VIIRS375 (98% recall, A77). **Decisión de cierre formal:
pendiente de Nicolás.**
