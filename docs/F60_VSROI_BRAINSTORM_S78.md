# F60 — VSROI per-volcán brainstorm (S78)

> **Estado**: READ-ONLY brainstorm. NO se modifica pipeline ni data.
> **Sesión**: S78 (2026-05-25). Worktree dedicado A44: `VRP-Chile-s78-brainstorm-vsroi`.
> **Trigger**: gap metodológico documentado en Vault `aveni2024tirvolch` línea 87 ("VSROI volcán-específico — tenemos ROI única por `radius_km`").

## 1. Por qué importa (fenómeno físico antes que código)

El pipeline VRP-Chile usa círculos para decidir qué pixel "cuenta" como anomalía
del volcán. Un círculo de 5 km centrado en el vent es geométricamente simple
pero **no respeta la forma real del edificio volcánico**. En el campo, un
edificio activo tiene:

- un **cráter activo** (zona caliente persistente, pocos pixels)
- **flancos asimétricos** (algunos con glaciar, otros desnudos)
- a veces un **lago cráter** (cuerpo de agua dentro del edificio)
- a veces **lagos peri-volcánicos** (Caviahue, Villarrica, Calafquén) que
  retienen calor nocturno y producen ΔBT 5-15 K vs aire frío circundante

Cuando el inner-radius circular incluye un glaciar grande NW del vent (caso
Villarrica/Pichillancahue), el pixel VIIRS de 375 m mezcla hielo + roca y el
algoritmo de detección lo lee como "anomalía" porque el ΔBT relativo al ring
1-5 km nieve más fría dispara el gate. Resultado: **125 FPs por temporada
sobre el glaciar mientras MIROVA no reporta nada** (cf.
`docs/VILLARRICA_VIIRS375_OVERDETECTION.md`, ratio sobre-detección ~21-40×).

Aveni 2024 RSE §4.3.4 resolvió esto con **VSROI = Volcano-Specific Region Of
Interest**: un polígono dibujado a mano sobre el rasgo térmico persistente
real (cráter, fumarola, lava lake) de **1×1 o 2×2 km típicamente**, centrado
en el "hottest pixel" histórico. Sólo dentro del VSROI se aplican thresholds
más sensibles (Z>5 vs Z>7, ΔTbg=0.5 K). Fuera del VSROI el algoritmo usa los
ROIn concéntricos (1, 5, 12.5, 25 km) con thresholds más conservadores.

Diferencia clave con nuestro `inner_radius_km`:

| Aspecto | Nuestro `inner_radius_km` | VSROI Aveni 2024 |
|---|---|---|
| Forma | Círculo | Polígono arbitrario |
| Tamaño típico | 3-20 km | **1-2 km** |
| Anclado en | `vent_lat/lon` o `mirova_center_*` | hottest pixel histórico |
| Propósito | clasificar summit vs far visual | aplicar thresholds más sensibles |
| Excluye glaciar | No (es círculo) | Sí (se dibuja evitándolo) |
| Múltiples regiones | No | **Sí** (fumarolic field disperso) |

**Resumen**: VSROI no es "círculo más chico", es "polígono ajustado al rasgo
térmico real, posiblemente múltiple, mucho más pequeño". El inner-radius
nuestro y el VSROI de Aveni resuelven cosas **distintas**.

## 2. Cómo se define el VSROI según Aveni 2024 (verbatim §4.3.4)

> "If a persistent thermal anomaly can be distinguished, a VSROI — usually
> extending for ~1 × 1 or ~2 × 2 km depending on the size of the thermal
> feature(s) — is centred on the hottest pixel (Fig. 8). To detect Candidate
> Alerts within the VSROI region(s), a similar approach to that presented in
> tests 4 and 6 is applied, yet thresholds are lowered to increase the
> detection sensitivity exclusively within the VSROI: Z-RES_VSROI ≥ 5."

> "It is worth it to mention that in a single scene multiple VSROI can be
> placed over different location, enabling a greater coverage of sparse
> thermal features (i.e., fumarolic fields) over the entire volcanic edifice."

Pasos para construir un VSROI según el paper:
1. **Identificar pixel(s) más caliente(s)** en la serie temporal histórica
   limpia (multi-año, nocturno, sin nubes).
2. **Dibujar polígono ad hoc** ~1×1 o ~2×2 km alrededor — manual, no
   algorítmico. Aveni lo describe como ROI "ad hoc mask".
3. **Permitir múltiples polígonos** en un mismo volcán si hay fumarolas
   dispersas.
4. **Sensor**: validado con VIIRS I5 (375 m, 11.45 μm). Implícitamente se
   aplica también a otros sensores en la cadena del paper.
5. **Sample size para definirlo**: Aveni usa décadas de VIIRS (2012-2023, ~10
   años) sobre Vulcano, Agung, La Palma. Para Chile, necesitaríamos al menos
   3-5 años nocturnos limpios por volcán — lo cual ya tenemos
   (`data/mirova_equivalent/<volcano>.json`).

## 3. Tabla per Tier A: ¿inner_radius captura lago/glaciar?

Para cada uno de los 11 volcanes Tier A (`mirova_monitored: true`),
inspecciono el `inner_radius_km` actual + geografía conocida del entorno. La
columna "¿captura lago/glaciar?" se basa en el `vent_lat/lon` del yaml + ojo
geológico (revisado por Nicolás post-S77 para Villarrica).

| # | Volcán | inner_radius | ¿captura agua/hielo dentro? | ¿VSROI sugerido? | Esfuerzo |
|---|---|---:|---|---|---|
| 1 | **Villarrica** | 5 km | **SÍ — Pichillancahue NW** | VSROI 1×1 km sobre cráter | bajo |
| 2 | **PuyehueCordonCaulle** | 20 km | parcialmente — lago Ranco S a ~22 km (justo en borde); lacolito 2011 SE es el real "hot spot" | VSROI 2×2 km sobre lacolito SE (-40.582, -72.131) | bajo |
| 3 | **Lascar** | 5 km | NO dentro de 5 km. Salar Atacama ya excluido vía `exclude_zones`. | Opcional — VSROI 1×1 sobre cráter V activo. Lascar funciona bien actualmente | bajo |
| 4 | **Copahue** | 4 km | **SÍ — lago cráter ácido** activo dentro de 4 km del vent | VSROI 1×1 km sobre lago cráter + posible VSROI separado fumarolas N | medio (2 polígonos) |
| 5 | **NevadosDeChillan** | 5 km | parcialmente — múltiples cráteres alineados N-S, área hidrotermal extensa | VSROI 2×2 km cubriendo línea de cráteres | medio |
| 6 | **Llaima** | 5 km | NO dentro de 5 km. Lago Conguillío a ~28 km (fuera). Posible nieve estacional cumbre | VSROI 1×1 km cráter principal | bajo |
| 7 | **Chaiten** | 5 km | NO. Domo principal compacto. Río Chaitén lejano | VSROI 1×1 km sobre domo (-42.834, -72.653) | bajo |
| 8 | **PlanchonPeteroa** | 3 km | parcialmente — pequeño cráter lake muy ácido (Peteroa pit) **dentro** | VSROI 0.5×0.5 km sobre pit Peteroa | bajo |
| 9 | **Lastarria** | 3 km | NO. Solfatara extensa SW del cráter, ya capturada por inner=3 | VSROI 1×1 km sobre solfatara persistente (offset SW del vent nominal) | medio (vent ≠ rasgo) |
| 10 | **Isluga** | 5 km | NO grande. Volcán seco, posibles fumarolas cumbre | VSROI 1×1 km cráter | bajo |
| 11 | **Tupungatito** | 7 km | parcialmente — glaciares en flancos N y W, posible nieve. mirova_center offset 3 km SE (S15) | VSROI 1×1 km sobre crater offset oficial | bajo |

### Hallazgos de la tabla

- **5 volcanes con rasgo térmico real ≠ vent_lat nominal** (PCC lacolito SE,
  Lastarria solfatara SW, Tupungatito offset SE, Villarrica cráter compacto,
  Planchón pit Peteroa). El VSROI corregiría sistemáticamente esto, mejor que
  los workarounds actuales `mirova_center_*`.
- **2 volcanes críticos con agua/hielo DENTRO del inner_radius**: Villarrica
  y Copahue. Son los 2 candidatos más rentables para piloto VSROI.
- **3 candidatos opcionales** (Llaima, Chaitén, Isluga) — funcionan bien con
  el inner-radius actual, VSROI sería refinamiento marginal.
- **Lascar** ya tiene workaround vía `exclude_zones` (Salar Atacama) — VSROI
  no es prioridad.

## 4. Opciones de implementación

### Opción A — VSROI polygonal en yaml (alineado al paper)

Agregar campo `vsroi` per volcán como lista de polígonos (cada polígono es
lista de vértices `[lat, lon]`):

```yaml
- name: Villarrica
  inner_radius_km: 5  # se mantiene para clasificación summit/far
  vsroi:
    - name: "crater_main"
      polygon:
        - [-39.4192, -71.9355]
        - [-39.4192, -71.9445]
        - [-39.4212, -71.9445]
        - [-39.4212, -71.9355]
      threshold_relax_k: 0.5   # ΔTbg dentro del VSROI
      z_threshold: 5            # vs Z=7 fuera
```

- **Ventajas**: literal al paper. Soporta múltiples polígonos. Fácil de
  versionar (texto plano en yaml). Visualizable en frontend con
  `Polygon.from_yaml` en Leaflet.
- **Desventajas**: requiere código nuevo en `scan_geometry.py`
  (`point_in_polygon` per pixel), nuevo gate en `process_viirs.py` y
  `process_modis.py`. Per-pixel point-in-polygon es O(N×V); con N=5000 pixels
  y V=4-8 vértices es despreciable (~0.02s).
- **Esfuerzo**: 1 sesión completa (Plan + TDD + reproc Tier A + validación).
  Plan F31 Task A5 ya enmarca un "piloto experimental_lowT" — VSROI cabe ahí
  como Task A7 o A8.

### Opción B — inner_radius_km más estricto per-volcán

Reducir el `inner_radius_km` Villarrica de 5 → 2 km, Copahue 4 → 1.5 km. NO
toca arquitectura — solo edita yaml.

- **Ventajas**: cero código nuevo. Reproc en 1 hora. Reversible. Cura ~80%
  de los FPs glaciar Villarrica sin meter polígonos.
- **Desventajas**: sigue siendo círculo (no excluye SE del vent si el
  glaciar está NW). En Villarrica el glaciar Pichillancahue está NW y NE del
  vent — un círculo de 2 km sigue tocando lengua glaciar. Sólo mitiga
  parcialmente.
- **Esfuerzo**: 30 min edit + 2-3 h reproc + 1 h auditoría. Buena opción
  intermedia antes de Opción A.

### Opción C — máscara bitmap raster per-volcán

Generar PNG/GeoTIFF binario per volcán delineando el VSROI.
`scan_geometry.py` lee el bitmap y aplica máscara per pixel.

- **Ventajas**: forma arbitraria, incluye exclusiones complejas (glaciar +
  lago + flanco N).
- **Desventajas**: binarios en git, harder to review, harder to version.
  Workflow de edición manual (QGIS) más lento que editar yaml. Almacenamiento
  per-volcán = ~10-100 KB → manejable pero feo.
- **Esfuerzo**: alto. Workflow QGIS per volcán + código de lectura raster +
  alineamiento CRS con el granule. Solo justificable si Opción A se queda
  corta.

## 5. Recomendación priorizada

**Piloto S79+ (no S78)**: combinar Opción B inmediata + Opción A para 2
candidatos:

1. **Quick win Opción B**: en S79 reducir `inner_radius_km` Villarrica 5→2 +
   Copahue 4→1.5. Reproc 5 meses con `--profile mirova_equivalent` + audit.
   Si ratio FP/mes cae <5× MIROVA (vs 21-40× actual Villarrica), ya valió la
   pena.
2. **Opción A piloto** sobre Villarrica + Copahue: definir manualmente 2
   polígonos cada uno (crater principal + fumarolas/lago para Copahue),
   correr en profile aislado `experimental_vsroi.yaml` con `data_subdir:
   experimental_vsroi/`, A/B contra `mirova_equivalent`. Si VSROI mejora
   precision sin destruir recall, expandir a Lastarria + PCC + PlanchonPeteroa.
3. **Opción C descartar** salvo que A+B fallen sobre Villarrica
   específicamente.

**No hacer en S78**: implementación. Esto es brainstorm read-only.

## 6. Preguntas abiertas para Nicolás (decisión geológica, no técnica)

1. **Villarrica**: ¿el cráter activo cabe en 1×1 km o necesitamos 2×2 km?
   Geometría real del pit (post-eruption 2015) sería útil.
2. **Copahue**: ¿el lago cráter y las fumarolas N son **una sola** zona
   térmica o realmente dos VSROI separados? Si están a <500 m, una sola.
3. **Lastarria solfatara SW**: ¿la solfatara persistente está realmente
   offset 1.5-2 km SW del vent_lat nominal, o el vent en yaml ya es el
   centroide de la solfatara? Esto define si necesitamos `mirova_center_*`
   como hoy o un polígono VSROI.
4. **PCC lacolito**: ya tenemos `mirova_center_lat/lon` apuntando al
   lacolito SE. ¿VSROI 2×2 km centrado en `mirova_center` lo cubre? Asumo sí.
5. **Tupungatito**: glaciares N/W son problema o pasa el actual?
   `docs/TUPUNGATITO_FINDING_S72.md` puede tener pistas.

## 7. Conexiones

- Paper: Aveni 2024 RSE — `documentacion/Aveni_2024_TIRVolcH_RSE.md` líneas
  544-1135 (sección 4.3.4 VSROI).
- Vault note: `Vault/10_Bibliografia/99_por_clasificar/aveni2024tirvolch.md`
  línea 87 (gap VSROI documentado).
- Plan F31 (paralelo): `docs/F31_AVENI_GRL_2025_EXTRACT.md` — VSROI puede
  integrarse como Task A7-A8 en ese plan post-Task A5 piloto.
- Datos FPs Villarrica: `docs/VILLARRICA_VIIRS375_OVERDETECTION.md`.
- Datos PCC ratio: `docs/F46_LASTARRIA_IMPACT_S77.md` (kernel-bg ya cura ~92%
  ratio PCC — VSROI sería refinamiento adicional, no reemplazo).
- F52 Villarrica max_cluster_pixels=12: ya es un workaround S77 contra
  glaciar Pichillancahue. VSROI lo haría obsoleto si cubre solo el cráter.

## 8. Próximo paso si Nicolás aprueba piloto

1. Crear Plan F60 bite-sized (writing-plans skill).
2. Definir VSROI manual Villarrica + Copahue (Nicolás dibuja en QGIS/Leaflet
   o da bbox bbox).
3. Implementar `vsroi` en `scan_geometry.py` (función `point_in_polygon`).
4. Profile `experimental_vsroi.yaml` con `extends: mirova_equivalent` +
   `data_subdir: experimental_vsroi/` + flag `enable_vsroi: true`.
5. A/B reproc 5 meses 2 volcanes piloto.
6. Auditar ratio + recall + precision.
7. Si pass criterios MIROVA-paridad → adoptar operacional con `superpowers-brainstorming`
   gate (A45 — toca pipeline NRT operacional).
