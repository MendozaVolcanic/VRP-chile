# Plan de mejoras — vista experimental Beyond MIROVA (S122+)

> La vista `frontend/experimental/beyond-mirova.html` muestra lo que el algoritmo de
> Coppola captura pero MIROVA NRT no publica (extensión cat-b, magnitud recuperada).
> NO toca el operacional ni la detección — es display sobre data fiel + un perfil aislado.
> Objetivo (misión obj-2): documentar el valor agregado VRP Chile de forma defendible.

## Estado actual (S121)

- **Panel 2a** (zonas geológicas proximal/extensión/dispersión): interactivo, sliders por
  volcán. Solo **3/11 tienen preset documentado** (PCC lacolito 2 km Castro 2016, Lastarria
  Lazufre, Villarrica lava lake). Los otros 8 usan default `inner`/`2×inner`.
- **Panel 1** (fidelidad vs MIROVA): serie nuestra (pc.vrp máx diario) vs CSV consolidado +
  ratio geométrico. Funciona.
- **Panel 2b** (Eq.16 lava lake): multi-volcán (selector), lee perfil `_s99_test1_eq16`.
  Resultado S120: Eq.16 corrige hacia abajo el sobre-registro invernal, clava banda OCR.

## Mejoras priorizadas

### M1 — Zonas 2a de los 8 volcanes faltantes (criterio geológico Nicolás) [ALTA, requiere Nicolás]
Los 3 con preset salieron de literatura/campo. Faltan: Láscar, Isluga, Llaima, Chaitén,
Tupungatito, Copahue, PlanchonPeteroa, NevadosDeChillan. Para cada uno: Nicolás mueve los
sliders en el navegador hasta que la zona naranja abrace el cuerpo volcánico real; Claude
persiste los valores en `ZONE_PRESETS` con la cita física (como PCC/Castro 2016). **Bloque
de 30-45 min con Nicolás frente al dashboard** (no delegable — criterio geológico).
Incluye el WATCH Copahue: cotejar si el sesgo S ~1.2 km es el cráter El Agrio real.

### M2 — Integrar AVTOD como segundo ground truth (EXT-8) [ALTA, para el paper]
`documentacion/AVTOD_Reath_2019.pdf` + `.md` ya están. Es catálogo ASTER 90m manual
(Reath, Coppola et al. 2019), INDEPENDIENTE de MIROVA OSF, cubre los Tier A chilenos.
Tareas: (a) extraer los valores VRP AVTOD de los vols chilenos del PDF a un CSV; (b) Panel
nuevo (o serie en Panel 1) que superponga nuestra serie vs AVTOD; (c) identificar vols
donde MIROVA diverge de AVTOD → casos documentables para el paper Volcanica. **Es el
argumento de robustez metodológica del paper** (doble cross-validation, no una sola fuente).

### M3 — Distancias OCR de MIROVA en el Panel 1 (F-B2) [MEDIA]
El OCR (registro_vrp_ocr.csv) tiene la distancia al cráter que MIROVA reporta por imagen.
Superponerla como serie de posición en Panel 1 (o un chip) para cotejar nuestro
final_hotspot_dist vs el de MIROVA visualmente. Loader ya soporta el campo (cobertura
subió 4%→12% en #485).

### M4 — geo_class display en el dashboard experimental [MEDIA, tras M1]
Una vez afinadas las zonas 2a (M1), promover la clasificación proximal/extensión/dispersión
a un `geo_class` de display en la vista experimental — que las detecciones cat-b (Lazufre,
lacolito, El Agrio) se muestren nombradas, no como "far gris". A72: es señal real, display
legítimo (no toca detección).

### M5 — Panel 2b Eq.16: reproc de los vols con lava lake activo [MEDIA]
Villarrica ya está. Extender el reproc `_s99_test1_eq16` a los otros vols con lava lake /
domo (Chaitén, PCC) para poblar el Panel 2b multi-volcán con más series cruda-vs-Eq.16.

## Fuera de alcance (backlog catálogo)
EXT-6 HotLINK CNN, EXT-4 multi-sensor fusion (GOES/S2), EXT-12 TIRVolcH — requieren
infra nueva, no son mejoras incrementales de la vista.

## Orden sugerido
M1 (con Nicolás, desbloquea M4) → M2 (paper) → M3 → M5. M2 es el de mayor valor para la
publicación; M1 es el de mayor valor visual/geológico y el único que necesita a Nicolás.
