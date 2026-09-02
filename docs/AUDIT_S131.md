# Auditoría S131 — resultados, dashboard y utilidad para OVDAS

> Pedida por Nicolás el 2026-09-02 al pasar a Fable 5.1: *«auditoría de nuestros resultados
> considerando todo lo necesario para que este proyecto funcione y cumpla los objetivos,
> considerando las auditorías anteriores; audita también la visualización en el dashboard;
> busquemos problemas o mejoras»*. Alcance acordado: dashboard = correctitud **y** utilidad
> para el operador; modo = diagnóstico + fixes de bajo riesgo fuera de `pipeline/`;
> escala = 6 agentes en paralelo (Fable orquesta; Fable/Opus/Sonnet según el eje); el
> hallazgo del remuestreo entra como eje de magnitud.
>
> Todo número de este documento sale de un script persistido en `experiments/_s131_audit/<eje>/`
> o `experiments/_s131_remuestreo/`; ninguno transcrito a mano (S91). Los informes por eje, con
> la evidencia completa, viven en `docs/s131/agentes/`.

## Declaración de ejes (regla A del protocolo: prohibido repetir el barrido general)

| eje | modelo | ¿nuevo? | informe |
|---|---|---|---|
| Cadena de magnitud vs papers file:line + **ATBD del sensor vs código** | Fable | **nuevo** (Fase 3 «nunca auditada») | `agentes/MAGNITUD.md` |
| Dashboard: T7 adversarial **+ utilidad para el turno de OVDAS** | Opus | mitad B **nueva** | `agentes/DASHBOARD.md` |
| Declarado ≠ efectivo (T9): FICHA_SDA, MISSION, CLAUDE.md, DIVERGENCES, README, workflows | Opus | repetido — el de mayor rendimiento (S127) | `agentes/DECLARADO_VS_EFECTIVO.md` |
| Pendientes S128 §8 + S129/S130 (regla C) + salud NRT/CI/seguridad | Sonnet | puerta de entrada obligatoria | `agentes/PENDIENTES_INFRA.md` |
| Ground truth espacial por pasada: TIF/KMZ de MIROVA vs nuestra posición (A61) + cruce CSV 3 celdas | Opus | exógeno, 2 usos previos | `agentes/GROUND_TRUTH_ESPACIAL.md` |
| **Otro sensor** (NHI-v1: Sentinel-2 + Landsat SWIR) como tercer juez | Sonnet | **nunca usado** | `agentes/OTRO_SENSOR.md` |

Baseline al abrir: suite **1039 passed, 3 skipped**; NRT 27/27 verdes en 7 días; fecha del
servidor 2026-09-02 (A86).

---

## 1. Resultado primero

**El sistema detecta bien y mide de menos; y lo que peor está es lo que el sistema dice de sí
mismo.** En una línea por eje:

1. **Magnitud** — la física (coeficientes, Planck, áreas nominales) está bien y coincide con el
   OSF v2.5. Lo que diverge de MIROVA es **qué se suma, con qué fondo y sobre qué área**. El
   **área de píxel explica el gradiente cenital completo** (por pasada: 0,77 → 0,45 sin
   corregir; 0,79–0,87 plano con la ley del ATBD) y deja un **déficit uniforme ~0,82** que es
   otro mecanismo (fondo de Eq. 6 + suma/clúster, R1/R2 de S125 siguen en producción: MODIS
   degradado a 1 píxel en el 48,9 %). **Lo que ve el operador para VIIRS375 no es
   `pc.vrp_mw`** (`USE_F5_CORE` default: 0,68 vs 0,58 contra MIROVA; coincide en el 5,7 %)
   y ese número no se persiste.
2. **Dashboard** — la aritmética es exacta (11/11 tarjetas coinciden con el DOM del sitio
   publicado hasta el último decimal). Lo que falla es lo que la pantalla **afirma**: el
   semáforo «Sistema Operativo» era HTML fijo; tarjeta y detalle daban dos niveles distintos
   sin rótulo (11/11); «0,0 km del cráter» es el ancla, no una medición; `index` desbordaba
   2,09× en celular. Para el operador: el badge es una **constante** (100 % «Muy Bajo» en
   4.279 ventanas), sólo el **23,7 %** de las detecciones visibles tienen MIROVA de la misma
   pasada y el dato está sólo en el popup, y no está escrito en ninguna parte **qué NO ve**
   el sistema.
3. **Declarado ≠ efectivo** — 47 afirmaciones: **15 confirmadas · 16 falsas · 13 obsoletas ·
   3 sin respaldo**. Cuatro falsas en el **documento legal** (FICHA SDA): declaraba MOD14/MYD14
   (producto de incendios) como entrada y dos mitigaciones apagadas. El README atribuía al
   pipeline el centrado de grilla que D17 declara NO implementado. 1.635 records publicados
   llevaban el sello del piso VRP con magnitud > 0.
4. **Pendientes** — de los 10 de S128: 2 cerrados, 1 resuelto hoy (M15: 423 K era el techo de
   **otra banda**; el correcto es 343 K, Campus 2022), **7 abiertos** — dos exactamente igual
   que en S128 (inyección de comandos en 7 workflows; `nrt-retry` sin timeout). NRT 27/27
   verde **pero el peor job tardó 56 min contra un timeout de 60** (margen 7 %, A15 pide 30 %)
   y el guard que debería verlo se salta `nrt.yml`.
5. **Ground truth espacial** — el **GeoTIFF de MIROVA queda refutado como árbitro de
   posición** (control de instrumento: error mediano 4,80 km contra `Distancia_km`; pierde
   contra el nulo «está en el cráter» en MODIS/V750). Donde sí hay respaldo (V375, máximo
   sobre el edificio), nuestro clúster está a **228 m = 0,61 px**. En MODIS el máximo MIR
   absoluto no ve el volcán **ni para MIROVA** (20,8 km del cráter): por eso **1.073 de 1.233**
   detecciones MODIS con clúster a ≤2 km quedan `far` (A46/A81, cara b). Cruce por pasada:
   recall MODIS 1,000 · V375 0,961 · V750 0,836; **111 FN, todos reales y sub-umbral**
   (0,19 MW mediano). A69 persiste pero **no es «al N»**: Copahue al S, Villarrica al O.
   `half_km=25,5` es correcto (±0,21 km) — cierra el pendiente #6 de S128.
6. **Otro sensor** — `NHI-v1` publica series SWIR (S2 20 m + Landsat 30 m) para 10/11 Tier A
   sin credenciales. Confirmó el FN A77 de NdC (22-mar) con evidencia independiente. Nuestras
   detecciones sin MIROVA **no se distinguen de la actividad crónica** en 4/5 volcanes (tasa
   NHI igual a su basal) → consistente con A54; NdC 2× su basal en su ventana eruptiva. No sirve
   como gate (basal 20-49 %); sí como panel de contexto. **Gap**: el producto OLI/MSI de
   MIROVA no lo scrapea ningún repo.

**Y una corrección propia, en la misma sesión**: el «f requerido 2,93×» que abrí la sesión
afirmando estaba mal emparejado (cada pasada nuestra contra el **máximo de la noche** de
MIROVA, el error que la cabecera de `_s126_lib.py` documenta y que **S130 heredó igual**).
Por pasada es **1,72**, y el área lo cubre entero. Queda anotado en
`docs/s131/REMUESTREO_LEY_DE_AREA.md` §4 con el original conservado.

---

## 2. Hallazgos que cruzan más de un eje (pesan más)

| hallazgo | ejes que lo vieron | qué significa |
|---|---|---|
| **El far→summit de MODIS es un artefacto del `final_hotspot` por MIR absoluto** (21 km del cráter; el máximo de MIROVA a 20,8 km; ρ = 0,023 entre ambos) | ground truth (H2/H3) · T9 (FICHA F3) · magnitud (§2.5) | A72: es artefacto, no señal — la salida es el algoritmo (derivar `distance_class` del `primary_cluster`), no el display. Reabre la cara b de A81 con evidencia exógena nueva |
| **Una sola magnitud publicada, trazable** | magnitud (§2.10) · dashboard (B2/B3) | lo que se audita (`pc.vrp_mw`) no es lo que se publica en V375 (`f5CoreMagnitude`); decisión de Nicolás: persistir el número del display o volver el default |
| **Los mecanismos que distinguen cat-b real de artefacto están inertes** | dashboard (A7, A16) · ground truth (H10) · otro sensor | `geo_class="extension"` 0/11.599, `isThermalArtifact` 0/57.851; A54 (95 % físicamente real) sigue sin recomputar porque no hay gazetteer de rasgos |
| **Corregir texto sin guard no cierra nada** | T9 (4 citas drifteadas tras S127) · pendientes (#4/#5 idénticos a S128) · INDEX congelado 4.ª vez | regla B aplicada: 8 guards nuevos en `tests/test_guard_declarado_vs_efectivo_s131.py` |
| **A69 vale, su ejemplo no** | ground truth (M2c) · T9 (A12 falsa) | «~1 km al N» describe los dos volcanes que S104 miró; la dirección es propia de cada volcán |

---

## 3. Lo que se corrigió en esta sesión (rama `s131-audit-fixes`)

Todo fuera de la lógica de `pipeline/` (sólo comentarios/docstrings ahí); cada cambio con su
guard o su verificación:

| qué | dónde | verificación |
|---|---|---|
| Inyección de comandos: 29 interpolaciones `github.event.inputs.*` movidas a `env:` en 7 workflows | `.github/workflows/{nrt,backfill-*,reproc-*}.yml` | `scan_injection.py`: 31 → **0**; YAML válido |
| `nrt-retry.yml` con `timeout-minutes: 15`; job `process` de `nrt.yml` 60 → **80 min** (peor caso 56 × 1,3 = 73) | workflows | A15 |
| FICHA SDA: entrada L1B real, sin «zonas de exclusión», sesgo topográfico declarado sin mitigación activa; fila v1.5 | `docs/FICHA_SDA_VRP_CHILE.md` + cabecera `vrp_regimes.py:10` | guards G1, G2 |
| MISSION: pisos RETIRADOS S130, máscara de nube RETIRADA S126, líneas de Regla D, lista de abiertas apunta al catálogo | `docs/MISSION.md` | — |
| CLAUDE.md: `radius_km` 25 sólo en Tier A; «34 sin pull» falso; A12 marcada FALSA; A17 sub-frase tachada; 4 citas file:line actualizadas; concurrency reescrita como condición | `CLAUDE.md` | guard G8 (10 citas) |
| README: grilla NO centrada en MIROVA (D17), TIR VRP deshabilitado, 34 volcanes, 3 vistas + 1 preview | `README.md` | guard G7 |
| DIVERGENCES: D2 medida 79,2 %, D3 sin instrumento, D12 «Siguen ON» tachado, D18 encabezado | `docs/MIROVA_DIVERGENCES.md` | — |
| INDEX: S128 y S131 listadas, sin «Última» hardcodeada | `docs/INDEX.md` | guard G6 |
| Docstrings: nota operacional nadir-fijo, `roi_mask_bbox` uso actual, `viirs_pixel_areas` número corregido (4,38×), `cloud_free` todo-True | `pipeline/scan_geometry.py`, `process_viirs.py` | comentarios, sin lógica |
| MAPA_WORKSPACE: VRP Chile 🟢 (era 🔴 en el grafo), carrera de push cubierta | workspace | guard G4 |
| Frontend: semáforo del header alimentado por la peor frescura Tier A; rótulos «última pasada» / «máx 30 d»; «en el cráter (ancla)» en vez de 0,0 km; regiones Lastarria→Antofagasta, Tupungatito→Metropolitana en `index`+`mosaico`; móvil (`flex-wrap`, `overflow-x`); voseo en `comparacion` | `frontend/*.html` | navegador real 8091 (ver §5) |
| Protocolo: registro de ejes actualizado (otro sensor 1 uso; TIF refutado para posición; ATBD vs código; utilidad OVDAS) | `docs/PROTOCOLO_AUDITORIA_PROFUNDA.md` | — |

**Suite**: 1054 passed · 3 skipped · **2 xfail estrictos** (G3 sellos del piso, G7 `vrp_tir_mw`),
que se convierten en verdes cuando Nicolás apruebe la limpieza de datos (§4.1).

---

## 4. Decisiones de Nicolás (no las tomo yo)

1. **Limpieza del dato publicado** — `experiments/_s131_audit/limpiar_sellos_data.py`
   (dry-run: 1.635 sellos a quitar, 28 `vrp_tir_mw` → 0, sobre 60.694 records). Reversible,
   con tag defensivo; dos guards estrictos esperan.
2. **M15 saturación** (`process_viirs_mod.py:193-196`): 423,0 → **343,0 K** (Campus 2022
   Tabla 1, misma fuente que M13 = 634 K; el UserGuide da 374,6 K como techo de LUT). A45.
3. **Una sola magnitud publicada**: (a) persistir `display_vrp_mw` cuando `USE_F5_CORE` sea
   default, o (b) volver el default a `pc.vrp_mw`. Validación: `04_display_f5_vs_pc.py`.
4. **`distance_class` de MODIS desde el `primary_cluster`** (ground truth R1): A/B con reproc
   real, criterio pre-registrado (los 65 TP MODIS no pueden bajar; medir cuántos de los
   2.410 de la celda (c) pasan a summit). A45.
5. **El A/B del área** (magnitud R1): área desde la geolocalización del propio granule (sin
   modelo, incluye los saltos de agregación), flag OFF, 3 brazos (control · área ·
   área + corona Eq. 6), criterio pre-registrado (bin 50°+/nadir en 0,9–1,1 por pasada;
   ≥ 6/8 volcanes en banda V375; 0 noches MIROVA perdidas; pares > 2 ≤ 10 %). A45.
   **No extender a MODIS** por extrapolación (50 pares, un volcán).
6. **B22 primaria en MODIS** (Coppola 2016a l.141-144; hoy B21): una línea, A45.
7. Higiene de disco: duplicados de `documentacion/` (101,9 MB) y ~113 MB huérfanos en
   `experiments/_s104_roi_probe/` — A38.
8. Rotar el PAT de `~/.claude/settings.json` (recordatorio obligatorio).

## 5. Verificación del frontend (navegador real, puerto 8091)

Sobre `frontend/index.html` servido desde el repo (data local con 38 h de atraso respecto
del servidor — justo el caso que A1 describía):

| qué | antes | después (medido en el DOM) |
|---|---|---|
| Semáforo del header | `status-dot` verde fijo, «Sistema Operativo» | `status-dot mon-lagging` (ámbar), texto **«Datos atrasados»**, tooltip «Peor frescura entre los volcanes Tier A: datos atrasados · última pasada hace 38 h» |
| Distancia en tarjeta (7 de 11 en `test1_roi`) | «0.0 km del cráter · 14 px» | **«en el cráter (ancla) · 14 px»**; Lastarria 0,9 km, Tupungatito 2,4 km, PCC 1,4 km, Chaitén 2,9 km siguen como distancia |
| Badge tarjeta / detalle | mismo badge, sin rótulo | tarjeta con tooltip «Nivel de la ÚLTIMA pasada (48 h)…»; detalle **«… · máx 30 d»** |
| Regiones | Lastarria «Atacama», Tupungatito «Valparaíso» | **Antofagasta**, **Metropolitana** (index y mosaico) |
| Móvil 375 px | `scrollWidth` 783 (2,09×); enlaces a las otras vistas fuera de pantalla | **375/375**; los 4 enlaces y «Acerca de» dentro de pantalla (right ≤ 273 px); la tabla de eventos scrollea dentro de su caja |
| Consola | — | 0 errores de script; los únicos 404 son `*_recent.json`, que sólo existen en el sitio publicado (`build_recent_json.py`) y tienen fallback al JSON completo |

**Sitio publicado** (`pages-deploy` run `success` sobre `b0066a6c7`, 2026-09-02 20:50 UTC;
leído desde https://mendozavolcanic.github.io/VRP-chile/index.html): header `status-dot
mon-fresh` + «Sistema Operativo» con tooltip «Peor frescura entre los volcanes Tier A:
monitoreado · última pasada hace 14 h» (con data fresca el semáforo queda verde, y ahora por
dato, no por HTML); Villarrica/PCC/Chaitén «en el cráter (ancla)», los otros 8 con distancia;
regiones Antofagasta ×5 / Metropolitana ×2; detalle «Sin datos · máx 30 d» (abre en Taapaca,
R7 pendiente). Móvil 375 px en el sitio publicado: `scrollWidth` **375/375**, los cuatro
enlaces del header con borde derecho entre 252 y 272 px (antes 399-716).

Scripts de verificación: los del agente en `experiments/_s131_audit/dashboard/` (réplica de
los 10 predicados de `index.html`, 11/11 tarjetas coinciden con el sitio publicado) y las
lecturas del DOM de esta sesión (registradas en el transcript; los valores de la tabla son los
devueltos por el navegador).

## 6. Pendientes declarados (regla C — puerta de entrada de S132)

1. Los 7 pendientes de S128 que siguen abiertos con lo de hoy descontado: A54 (necesita
   gazetteer de rasgos en `volcanoes.yaml` para ser un `join`), D13 (denominador), el A/B del
   área (antes «filtro de cenit»), `mirova_center` por volcán×sensor, corpus duplicado.
2. Dashboard R3/R5/R7/R8/R11/R12/R13 (frontend puro, no hechas hoy): columna MIROVA en la
   tabla, T MAX/T FONDO en tarjeta, arrancar en volcán con data, marcar el cap 5,00 MW,
   sección «qué NO ve», eje de anomalía relativa, «próxima pasada esperada».
3. R14-R17: `region` en `volcanoes.yaml`; `volcanic_features.yaml` para los 11 + hacer
   alcanzable el marcador «extension» (PCC 82 % summit > 5 km); sello de tiempo de proceso.
4. `nti_max` persistido en MODIS (patrón A7, seis líneas) — A45.
5. Guard para el timeout de `nrt.yml` contra su duración observada.
6. `mirova-tif-archive` parado desde 2026-05-20 (95 días): reactivar el poller.
7. Scrapear el producto OLI/MSI de MIROVA (`NPixHot`) — ningún repo lo hace.
8. El «≤ 0,17 % contra OSF v2.5» de los coeficientes sigue sin instrumento en el repo.

## 7. Método — lo que esta auditoría dice sobre auditar

- **El eje exógeno volvió a rendir, y volvió a rendir en el control, no en el veredicto.** El
  GeoTIFF se refutó a sí mismo como árbitro de posición antes de emitir uno; NHI se midió
  contra su propia basal antes de adjudicar. Las dos sondas «filosas» sobrevivieron porque
  llevaban control de instrumento.
- **Tres veces en un día el número cambió con la definición**: f requerido (2,93 → 1,72,
  emparejamiento), «MIROVA plano» (por noche sí, por pasada menos), A81 (S130). A90 aplicada
  al eje de emparejamiento: **la unidad de comparación es la pasada**, no la noche.
- **A89 me pasó otra vez y esta vez a un agente**: la cabecera del script decía «un par por
  (volcán, fecha, bucket)» y el código hacía otra cosa. Un docstring no es una medición.
- **Un agente por eje con modelo según el juicio que exige** funcionó: los dos ejes con más
  lectura de ecuaciones y rasters (Fable, Opus) trajeron los hallazgos que cambian decisiones;
  los mecánicos (Sonnet) cerraron pendientes con comandos. Costo total ≈ 1,7 M tokens de
  subagentes.
