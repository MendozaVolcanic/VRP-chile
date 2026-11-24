# S197, issue #1106: Chaitén MODIS 2026-11-19 02:30 UTC (pre-registro, escrito antes de despachar)

Rama desechable `s197-1106-probe` (no va a main). Sólo lectura: no escribe en `data/`, no commitea a main, no hace push
a main. Arnés: el de D36 punto 1 (`experiments/_s190_d36/p1_runner.py` y `brazos.py`, sin tocar), con
`p1_pasadas.json` reemplazado SÓLO en esta rama por 5 pasadas.

## Lo que ya se sabe sin bajar nada

- MIROVA (tabla consolidada de Mirova-v1, bajada el 2026-11-23 22:57 UTC): 1,07 MW, 3,61 km, «Bajo». OCR: [1, 2) MW,
  3,65 km, cenit 51°. Es la primera alerta MODIS nocturna de MIROVA en Chaitén en 2026 (D36 contó 0 desde marzo).
- La vía (record de main, procesado el 2026-11-21 17:12 UTC; desde entonces la detección nocturna de producción no
  cambió): 0 píxeles; celda decisiva en la cumbre sensible (zona 2, fila 26, col 23), dNTI 0,004864 contra umbral
  0,0058 (μ + 5σ), margen 0,84. La guardia K: 0 píxeles.
- 3,61 km es la distancia de la celda (2, 3) de una grilla de 1 km: fuera de la caja de 5 × 5 km. Ahí la vía usa el
  piso 0,02 del `.m` de VIIRS 750; la Tabla 1 de Coppola et al. 2016a para MODIS dice 0,01 (D36). La celda decisiva
  sólo da el máximo de c/u, así que una celda fuera de la cumbre con dNTI entre ~0,012 y ~0,017 no aparece en ella.

## Hipótesis

H1: el brazo B2 (sólo el piso de la Tabla 1, 0,01) o B (Tabla 1 completa) alerta en la pasada objetivo al menos una
celda fuera de la cumbre a 2,5 a 4,5 km del centro, y el brazo A (la vía) no.

## Regla, fijada antes de ver datos

- Control: A igual a `prod` (copia = módulo) y `prod` igual al record guardado, en las 5 pasadas. Si falla en la
  objetivo, el resultado no se lee.
- H1 CONFIRMADA si B2 o B alerta en la objetivo como dice H1. Mecanismo: el piso de D36. Costo mínimo visible: cuántas de
  las 3 negativas de Chaitén (MIROVA en 0) alerta B2 o B.
- H1 REFUTADA si ningún brazo alerta en la objetivo: la diferencia no está en los números de D36; se mira el campo de
  dNTI del recorte nativo (`nativos/*.npz`) alrededor de la celda (2, 3) y su vecindad.
- Villarrica 2026-09-25 08:05 (otra pérdida, no protegida, en la cumbre): se espera que ningún brazo cambie (el piso de
  la cumbre es igual en los dos). Si cambia, se informa.

Ningún cambio de producción sale de esto: la decisión sobre D36 o sobre aceptar la pérdida es de Nicolás.
