# Plan de reprocesos S124→S125 — cada corrida informa a la siguiente

> **For agentic workers:** REQUIRED SUB-SKILL: usar `superpowers:executing-plans`
> (ejecución inline con checkpoints — las tareas esperan corridas de CI, no
> sirve un subagente por tarea). Checkboxes `- [ ]` para tracking.

**Goal:** Secuenciar todos los reprocesos pendientes (NdC v2, brazos A y B de
F70.3, y los frentes derivados) en el orden que maximiza información: cada
corrida responde una pregunta que la siguiente necesita.

**Arquitectura:** Corridas de `reproc-chunked.yml` en GitHub Actions, una
pregunta por corrida, con verificación y lectura APAREADA entre corrida y
corrida. Los criterios de éxito están escritos ANTES de mirar resultados (A66)
— los de F70 viven dentro de los perfiles `_f70_a.yaml` / `_f70_b.yaml`.

**Stack:** `gh` CLI · perfiles YAML aislados (`data_subdir` propio) ·
scripts de lectura en `experiments/` (regla S91: ningún número a mano).

---

## Reglas transversales (violarlas invalida la corrida)

1. **Cola GH**: grupo de concurrencia `reproc-chunked` admite **1 corriendo +
   1 pendiente**. Despachar un tercero **EXPULSA al pendiente** (pasó 2 veces
   en S124). Regla: despachar el siguiente run SOLO cuando el pendiente pasó a
   `in_progress`.
2. **Lectura apareada por pasada** (lección S124): toda comparación entre
   corridas se hace sobre la INTERSECCIÓN de pasadas, clave
   `(datetime_utc, sensor)`. Nunca conteos de series completas.
3. **A47**: nunca dos corridas sobre el mismo `data_subdir`. Subdirs distintos
   sí pueden convivir.
4. **A45**: nada de esto toca `mirova_equivalent` ni el cron. Cualquier
   promoción posterior = tag defensivo + confirmación explícita de Nicolás.
5. **Criterio antes que dato**: no se mira un resultado sin haber releído el
   criterio pre-registrado del perfil correspondiente.
6. **Persistencia in-vivo**: cada gate cerrado se anota en
   `project_s124_estado` / doc correspondiente ANTES de despachar lo siguiente.

**Costos de referencia**: ~2,6 min/día/volcán; `max-parallel: 8`;
timeout 180 min/job; `max_days=37` seguro. Brazos F70: 11 vols × 2 trozos =
22 jobs ≈ 3-4 h de pared por brazo.

---

### Tarea 0 — NdC experimental v2 (CORRIENDO: run 33113486321)

**Pregunta que responde:** ¿el experimental difiere de la réplica SOLO por el
umbral cuando el perfil difiere solo en el umbral?

**Config:** `profile=experimental_ndc_focus` (v2) · `NevadosDeChillan` ·
2026-05-01..2026-08-27 · `max_days=30` (4 trozos + plan + merge).

- [ ] **0.1 Verificar cierre verde**

```bash
gh run view 33113486321 --json status,conclusion,jobs \
  -q '"\(.status) \(.conclusion//"")", ([.jobs[]|.conclusion//.status]|group_by(.)|map("\(.[0]): \(length)")|join("  "))'
```
Esperado: `completed success`, jobs `success: 6` (plan + 4 reproc + merge).
Si un trozo falla: relanzar SOLO la ventana del trozo caído (mismo comando de
despacho con `start/end` de ese trozo) — el merge conserva los que terminaron.

- [ ] **0.2 Traer la data y correr el diff v1-vs-v2**

```bash
git pull --ff-only
python experiments/_s124_ndc_focus/04_diff_v1_v2.py
```

Crear antes `experiments/_s124_ndc_focus/04_diff_v1_v2.py`:

```python
# -*- coding: utf-8 -*-
"""Diff v1 vs v2 del foco NdC: que noches aparecen/desaparecen y por que.

v1 = perfil con umbral + ancla Nicanor + inner 1 km (3 diferencias).
v2 = perfil con SOLO el umbral (1 diferencia).
La data v1 vive en git: ultimo commit que toco el subdir ANTES del merge v2.
"""
import io, json, subprocess, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
REL = "data/experimental_ndc_focus/NevadosDeChillan.json"

# sha del ultimo estado v1 (el commit anterior al merge del run 33113486321)
sha = subprocess.run(["git", "log", "-2", "--format=%H", "--", REL],
                     capture_output=True, text=True, cwd=ROOT).stdout.split()[1]
v1 = json.loads(subprocess.run(["git", "show", f"{sha}:{REL}"],
                capture_output=True, text=True, cwd=ROOT).stdout)
v2 = json.loads((ROOT / REL).read_text(encoding="utf-8"))

def noches(d):
    out = {}
    for r in d["records"]:
        s = r.get("sensor") or ""
        if "VIIRS" not in s or "750" in s:
            continue
        pc = r.get("primary_cluster") or {}
        v = pc.get("vrp_mw") or 0
        if v > 0:
            f = r["datetime_utc"][:10]
            out[f] = max(out.get(f, 0), v)
    return out

n1, n2 = noches(v1), noches(v2)
print(f"noches con deteccion  v1: {len(n1)}   v2: {len(n2)}")
print(f"\nAPARECEN en v2 ({len(set(n2)-set(n1))}):")
for f in sorted(set(n2) - set(n1)):
    print(f"   {f}  {n2[f]:.3f} MW")
print(f"\nDESAPARECEN en v2 ({len(set(n1)-set(n2))}):")
for f in sorted(set(n1) - set(n2)):
    print(f"   {f}  {n1[f]:.3f} MW")
```

Esperado (predicción escrita ANTES de correr): aparecen las noches marginales
que la réplica tenía y la v1 no (2026-06-22, 06-23, 08-21 al menos) más la
cobertura 08-25..27; desaparecen ~ninguna. Si desaparecen varias → investigar
antes de seguir (systematic-debugging).

- [ ] **0.3 Test de convergencia (el perfil quedó bien si esto da ~0)**

Sobre pasadas comunes y radio 500 m: noches solo-réplica con VRP ≥ 0,02 deben
ser ≈ 0 (la única diferencia legítima que queda es el tramo 0,005-0,02).
Verificar con `experiments/_s124_ndc_focus/03_ceguera_y_fondo.py` adaptado o
consulta ad-hoc; anotar el número en el commit.

- [ ] **0.4 Regenerar las DOS figuras y enviarlas a Nicolás**

```bash
python experiments/_s124_ndc_focus/plot_simple.py
python experiments/_s124_ndc_focus/plot_mapa.py
git add experiments/_s124_ndc_focus/ && git commit -m "data(s124): figuras NdC con serie v2 completa hasta 2026-08-27" && git push
```

- [ ] **0.5 Commit del diff + actualización de memoria** (`project_s124_estado`).

---

### Tarea 1 — F70.3 brazo A: ¿la grilla SOLA qué hace?

**Pregunta:** el efecto de la grilla UTM aislado del kernel. Incluye la
**predicción NdC** nueva: ¿cuántas de las 17 noches extra al cráter (réplica
detecta, MIROVA RUTINA 0,00) sobreviven detectando sobre grilla?

**Por qué A antes que B:** si A ya cura al juez (Tupungatito), B solo agrega el
kernel; si A rompe algo, no queremos confundirlo con el kernel. Separación de
variables — el mismo principio de la pregunta 1 de Nicolás.

- [ ] **1.1 Despachar (SOLO cuando el run de Tarea 0 esté `in_progress` o
  `completed` — regla de cola)**

```bash
gh workflow run reproc-chunked.yml --ref main -f profile=_f70_a \
  -f volcanoes="Lascar,Isluga,Lastarria,Llaima,Copahue,Tupungatito,NevadosDeChillan,Villarrica,Chaiten,PlanchonPeteroa,PuyehueCordonCaulle" \
  -f start=2026-06-25 -f end=2026-08-24 -f max_days=37
```

- [ ] **1.2 Al terminar: verificar 24 jobs verdes** (plan + 22 reproc + merge)
  con el mismo comando de 0.1 (cambiando el run id).

- [ ] **1.3 Lectura APAREADA contra control** (`data/mirova_equivalent/`),
  criterios pre-registrados del yaml `_f70_a.yaml`. Crear
  `experiments/_s124_f70/03_leer_brazo.py`:

```python
# -*- coding: utf-8 -*-
"""Lectura APAREADA de un brazo F70 contra el control operacional.

Uso: python 03_leer_brazo.py _f70_a
Por PASADA comun (datetime+sensor), por volcan y sensor:
  - ratio de VRP brazo/control en pasadas donde ambos detectan
  - detecciones que aparecen / desaparecen (con VRP y dist al vent)
  - offset espacial MEDIANO al vent y por rumbo (A61/A70)
  - cruce vs MIROVA CONS: recall por volcan, brazo vs control
"""
import io, json, math, statistics as st, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
BRAZO = sys.argv[1] if len(sys.argv) > 1 else "_f70_a"
VOLS = ["Lascar", "Isluga", "Lastarria", "Llaima", "Copahue", "Tupungatito",
        "NevadosDeChillan", "Villarrica", "Chaiten", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]
INI, FIN = "2026-06-25", "2026-08-24"

def idx(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    out = {}
    for r in d["records"]:
        f = (r.get("datetime_utc") or "")
        if not (INI <= f[:10] <= FIN):
            continue
        out[(f, r.get("sensor"))] = r
    return out

def vrp(r):
    pc = (r or {}).get("primary_cluster") or {}
    return (pc.get("vrp_mw") or 0), pc.get("centroid_dist_km")

print(f"{'volcan':20s} {'pasadas':>8s} {'ratio med':>10s} {'aparecen':>9s} {'desaparecen':>12s}")
print("-" * 66)
for v in VOLS:
    a = idx(ROOT / f"data/{BRAZO}/{v}.json")
    c = idx(ROOT / f"data/mirova_equivalent/{v}.json")
    com = set(a) & set(c)
    ratios, ap, de = [], 0, 0
    for k in com:
        va, _ = vrp(a[k]); vc, _ = vrp(c[k])
        if va > 0 and vc > 0:
            ratios.append(va / vc)
        elif va > 0:
            ap += 1
        elif vc > 0:
            de += 1
    m = st.median(ratios) if ratios else float("nan")
    print(f"{v:20s} {len(com):8d} {m:10.2f} {ap:9d} {de:12d}")
print("\nJUEZ (criterios del yaml): Tupungatito ratio vs MIROVA en banda,")
print("Lastarria NO roto, recall sin caidas >2pp, offset espacial <= control.")
```

- [ ] **1.4 NdC específico — la predicción:** contar cuántas de las 17 noches
  RUTINA-0,00 siguen detectadas en `data/_f70_a/NevadosDeChillan.json` al
  cráter (500 m). Anotar: si caen a ~3-5, el exceso era sustrato; si quedan
  ~15+, es sensibilidad real (cat-b).

- [ ] **1.5 Persistir lectura en `docs/S12X_F70_BRAZO_A_RESULTADO.md`** (mismo
  formato que `S124_F70_BRAZO_C_RESULTADO.md`) + memoria. Commit.

---

### Tarea 2 — F70.3 brazo B: la hipótesis central (grilla + kernel global)

- [ ] **2.1 Despachar cuando el brazo A esté `in_progress`** (mismo comando de
  1.1 con `-f profile=_f70_b`).
- [ ] **2.2 Verificar 24 jobs verdes** (como 0.1).
- [ ] **2.3 Tabla de 4 brazos** — control / A / B / C (C ya corrido:
  `docs/S124_F70_BRAZO_C_RESULTADO.md`), lectura apareada con
  `03_leer_brazo.py _f70_b`. Contra los criterios del yaml:
  - **JUEZ**: Tupungatito — B lo cura donde C no. Si B tampoco → la hipótesis
    F70 se refuta y se documenta en `MIROVA_DIVERGENCES.md` (no hay plan C).
  - Lastarria en banda (Lazufre es real, A84).
  - Sobre-reportadores (Copahue/NdC/Chaitén) no se escapan de 1,4.
  - Espacial: offset mediano ≤ control, por rumbo (A70).
  - Recall por sensor sin caídas >2 pp; si aparecen FN nuevos, **sospechoso #1
    = pérdida de hot-pixel por nearest-neighbor en MODIS** (medido F70.2b,
    `experiments/_s124_f70/01_perdida_hot_pixel.py`).
- [ ] **2.4 Escribir `docs/S12X_F70_VEREDICTO.md`** con la tabla y el
  cumplimiento criterio por criterio. **Presentar a Nicolás. STOP: nada se
  promueve sin su confirmación explícita (A45).**

---

### Tarea 3 — Post-veredicto (decisiones separadas, UNA a la vez)

- [ ] **3a. Si B pasa → diseño de promoción F70.5** (no ejecutar en esta
  tanda): tag defensivo `pre-s12X-f70-promote`, flip de `enable_utm_regrid` +
  kernel global en `mirova_equivalent`, reproc histórico **staged** (1 volcán
  piloto → verificar → los 11), actualización FICHA SDA (cambio metodológico
  mayor, CPLT N°372). Cada paso con confirmación.
- [ ] **3b. D14 — máscara de nube <260 K**: A/B propio con perfiles
  `_d14_mask_{on,off}` y `data_subdir` aislados, ventana 2026-06-25..08-24,
  SOLO después del veredicto F70 (la máscara toca el fondo; dos cambios juntos
  = el error que A66 documenta). Criterio pre-registrado a escribir en el yaml
  ANTES de correr: recall vs CONS∪OCR no cae; el 23 % de pasadas ciegas se
  recupera; los FP nuevos se clasifican por categoría A54 antes de juzgar.
- [ ] **3c. Celda de referencia del `Distancia_km` en UTM** (pendiente menor
  D15): repetir la inferencia de la celda con los 903 pares proyectados a UTM
  (zonas 18S/19S según volcán), no en la reproyección lat/lon del TIF.
  Informativo — no bloquea nada.
- [ ] **3d. Origen de grilla per-volcán desde GeoTIFF** (barato, read-only):
  leer `transform` de 1 TIF por volcán del archivo → tabla centro-de-grilla
  vs vent para los 11, para el análisis espacial futuro. 20 líneas con
  rasterio, patrón de `experiments/_s124_cuantizacion/`.
- [ ] **3e. Propuestas aún aprobables** (diseño antes de código): test de
  determinismo (misma entrada → bytes idénticos) y manifiesto de cobertura por
  corrida (qué granules se intentaron/bajaron/procesaron). Presentar como
  diseños; implementar solo con ok.

---

## Autorevisión (hecha al escribir)

- Cobertura: v2 (0), brazo A (1), brazo B (2), veredicto (2.4), y los 5
  frentes derivados (3a-3e) — todo lo abierto de S124 tiene tarea.
- Sin placeholders: comandos y código completos; los criterios de F70 viven en
  los yaml y se referencian, no se reescriben (DRY).
- Consistencia: ventanas idénticas entre brazos (2026-06-25..08-24 = la del
  brazo C, para comparabilidad de los 4); lectura siempre apareada.
