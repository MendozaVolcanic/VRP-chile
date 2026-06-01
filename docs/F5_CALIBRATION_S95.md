# F5' — calibración de magnitud campo-frío (S95)

**Sesión S95 (2026-05-31).** Calibración de las variantes F5' sobre data
REPROCESADA con el fix Test1 anomaly_pixels (PR #297), ventana 2026-05-01→05-29.
Diseño: `docs/superpowers/specs/2026-05-31-f5-coldfield-magnitude-design.md`.
Scripts reproducibles: `experiments/_s94_audit/f5_variants.py` (3 variantes) +
`experiments/_s95_audit/f5_d2_sweep.py` (barrido R_core de D2). Data: `data/_s94_reproc`.

Integridad §0.5: todos los números salen de los scripts (stdout → archivo), no a mano.

## El fenómeno (recordatorio)

Sobre fondo glaciar/helado, el path D contextual marca el **halo** de roca tibia
contra nieve (contraste hielo↔roca que Wooster lee como fondo↔lava). La magnitud VRP
suma decenas de esos píxeles débiles e infla 3-16× (Tupungatito 15.85×, Villarrica
9.83×). Láscar (cráter de roca caliente, sin halo nevado) calibra natural a 0.88×.
F5' = desacoplar la detección (intacta) de la magnitud (núcleo concentrado).

## Resultado 1 — la FORMA: D2 (radial desde el pico) gana

`f5_variants.py` con params default — ratio mediano vs MIROVA (VIIRS375):

| Volcán | baseline | D1 densidad | **D2 radial** | D3 trimming |
|---|---|---|---|---|
| Láscar | 0.88× | 0.82× | 0.82× | 0.88× |
| Lastarria | 1.78× | 1.56× | 1.66× | 1.78× |
| PCC | 3.94× | 1.71× | 1.93× | 3.86× |
| Planchón-Peteroa | 7.34× | 6.96× | 1.90× | 7.34× |
| Villarrica | 9.83× | 9.77× | 4.75× | 9.64× |
| Tupungatito | 15.85× | 15.72× | 11.34× | 15.85× |
| **mediana** | 5.64× | 4.33× | **1.92×** | 5.60× |

**D1 (densidad) y D3 (trimming) casi no mueven la aguja**: el halo glaciar NO es ralo
ni outlier estadístico — es denso y contiguo, así que D1 lo conserva (lo ve "denso")
y D3 lo conserva (lo ve "coherente"). Exactamente los modos de falla que el design
doc §4 anticipó. **Solo D2** (cortar a R_core del foco + extender por lava real
bt≥295K) muerde el campo frío sin romper el cráter caliente.

## Resultado 2 — el PARÁMETRO: R_core=0.75 km

`f5_d2_sweep.py` — barrido de R_core (bt_ext=295K fijo):

| Volcán | base | **R=0.75** | R=1.0 | R=1.25 | R=1.5 | R=2.0 |
|---|---|---|---|---|---|---|
| Láscar | 0.88× | 0.79× | 0.82× | 0.82× | 0.82× | 0.82× |
| Lastarria | 1.78× | 0.97× | 1.02× | 1.44× | 1.64× | 1.66× |
| PCC | 3.94× | 1.75× | 1.80× | 1.80× | 1.80× | 1.93× |
| Planchón-Peteroa | 7.34× | 1.34× | 1.51× | 1.56× | 1.72× | 1.90× |
| Villarrica | 9.83× | 1.99× | 2.46× | 3.15× | 3.59× | 4.75× |
| Tupungatito | 15.85× | 2.87× | 4.59× | 5.95× | 7.92× | 11.34× |
| **mediana** | | **1.55×** | 1.65× | 1.68× | 1.76× | 1.92× |
| records a magnitud 0 | | 1 | 1 | 1 | 1 | 1 |

R=0.75 da la mejor mediana (1.55×) y baja drásticamente el campo frío:
Tupungatito 15.85→2.87×, Villarrica 9.83→1.99×, PP 7.34→1.34×, Lastarria 1.78→0.97×.

## Seguridad — ⚠️ FALLA DETECTADA (criterio NO cumplido con D2 puro)

El "1 record a magnitud 0" del barrido **SÍ es un caso con match MIROVA** —
`_zerocheck.py` (R=0.75) lo identificó:

```
Lascar 2026-05-08 04:48  npx=2  pc.vrp=0.677  MIROVA=0.62  dist_min_vent=0.20km  bt_max=284.32
```

Es un **evento térmico real y débil de Láscar**: MIROVA reporta 0.62 MW, el píxel
más cercano está a **0.20 km del cráter** (clavado en el vent), 2 píxeles. D2 con
R_core=0.75 lo lleva a **magnitud 0** → **pérdida de señal real. El criterio de
seguridad (ningún evento confirmado a 0) NO se cumple con D2 puro.**

**Mecanismo**: D2 ancla el pico al píxel más cercano al vent entre el top-5 por vrp,
suma píxeles dentro de R_core del pico o con bt≥bt_ext. Con solo 2 píxeles separados
>0.75 km y ambos bt<295K, el segundo se descarta y, en el borde, la magnitud colapsa.
Es exactamente el modo de falla "foco real débil de 1-2 píxeles" que el design doc §3
anticipó para D1 — y que su **mitigación** resuelve: *"siempre conservar el píxel pico
y sus 8-vecinos inmediatos (el foco nunca se anula)"*.

**Fix aplicado — D2-safe** (`experiments/_s95_audit/f5_d2safe.py`): D2 + excepción
del píxel-pico (el píxel más cercano al vent y su vecindad ≤0.5 km SIEMPRE se
conservan). Re-barrido R_core con la métrica de seguridad:

| Volcán | base | **R=0.75** | R=1.0 | R=1.25 | R=1.5 |
|---|---|---|---|---|---|
| Tupungatito | 15.85× | 2.87× | 4.59× | 5.95× | 7.92× |
| Villarrica | 9.83× | 1.99× | 2.46× | 3.15× | 3.59× |
| Láscar | 0.88× | 0.82× | 0.82× | 0.82× | 0.82× |
| PCC | 3.94× | 1.75× | 1.80× | 1.80× | 1.80× |
| PP | 7.34× | 1.34× | 1.51× | 1.56× | 1.72× |
| Lastarria | 1.78× | 0.97× | 1.02× | 1.44× | 1.64× |
| **mediana** | | **1.55×** | 1.65× | 1.68× | 1.76× |
| **records MIR a 0** | | **0** | **0** | **0** | **0** |

**Criterio de seguridad → CUMPLIDO**: 0 eventos con match MIROVA caen a magnitud 0
(antes 1: el Láscar 0.62 MW, ahora conservado por la excepción). El campo frío sigue
curado (Tupungatito 15.85→2.87×, Villarrica 9.83→1.99×, mediana 5.6→1.55×).

**Lección de método (integridad §0.5)**: escribí "NINGUNO a magnitud 0" en la primera
versión de este doc ANTES de leer el output de `_zerocheck.py` (lo lancé en el mismo
turno). El dato lo refutó. Conclusión nunca antes del dato — corregido aquí.

## Tensiones abiertas (refinamiento pendiente)

1. **Láscar 0.79× cae apenas bajo el rango objetivo 0.9-1.1×.** Es el modo de falla
   D2 del design doc: Láscar es un cráter caliente con emisión realmente extendida;
   al apretar el núcleo a 0.75 km se recortan píxeles de lava genuina >0.75 km del
   pico que NO superan bt_ext=295K. **Mitigación a probar: bajar bt_ext** (p.ej.
   285-290K) para que la extensión por intensidad recupere esos píxeles de Láscar —
   el halo de Tupungatito es mucho más frío, así que no debería reactivarse. Requiere
   barrido 2D R_core × bt_ext (pendiente).
2. **Tupungatito 2.87× / Villarrica 1.99× aún sobre 1×.** Mejor que 15.85×/9.83× pero
   no del todo aterrizado. Su halo glaciar es denso y cercano (<0.75 km), parcialmente
   dentro del núcleo. Bajar R_core más sub-contaría Láscar — de ahí la tensión
   estructural cráter-caliente ↔ halo-glaciar. El barrido 2D bt_ext debería ayudar.

**Veredicto S95**: **D2-safe con R_core=0.75 km es el punto de operación recomendado.**
Forma D2 (radial desde el pico, anclado al vent) + excepción del píxel-pico. Cumple:
(a) campo frío curado (mediana 5.6×→1.55×, Tupungatito 15.85→2.87×, Villarrica
9.83→1.99×); (b) Láscar conservado 0.82×; (c) **0 eventos confirmados a magnitud 0**.

Residuales de segundo orden (opcionales, no bloquean): Láscar 0.82× apenas bajo el
rango ideal 0.9-1.1× (dentro del ±30% que MIROVA declara); Tupungatito 2.87× /
Villarrica 1.99× aún sobre 1× (halo glaciar denso <0.75 km del foco). Un barrido 2D
de bt_ext podría afinarlos pero la tensión cráter-caliente↔halo-glaciar es estructural;
no vale forzarla a costa de sub-contar Láscar (A55: no sobre-ajustar).

Próximo paso: implementación display-first (abajo).

## Implementación (pendiente, post-decisión de params)

F5' es **display-first** (decisión Nicolás S94): replicar D2 como `mirovaEqVrpCore(r)`
en las 3 vistas frontend (index/diario/mosaico, S92 L5), recomputando la magnitud
desde `anomaly_pixels` (ahora poblados en los 3 sensores tras #297). Validación =
preview real navegador. Solo si convence visualmente + R2 pixel-level vs TIF MIROVA →
bajar a `process_viirs.py` con A45 (tag+OK+TDD+reproc). Detección NUNCA se toca.

## Nota: 5 vols sin VIIRS reprocesado
El reproc VIIRS GitHub dejó sin archivo a Copahue/NevadosDeChillan/Llaima/Chaiten/
Isluga (matrix los incluyó; jobs sin commit — probable 0 pasadas VIIRS nocturnas
válidas en la ventana, o job sin completar). NO afecta la calibración F5' (los vols
campo-frío clave Tupun/Villarrica/PCC/Lascar/PP/Lastarria SÍ tienen VIIRS). Verificar
en S96 si re-disparar esos 5 para completitud.
